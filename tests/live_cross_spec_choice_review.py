"""Read-only source-visibility grammar control on unrelated real WoW specs.

This is NOT an opener/gameplay QA and does not assume every specialization
has potion branches. Run one normal HTTPS GET for each guide; print only
counts and booleans, never guide text, expressions, talent names or HTML.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

from engine.source_acquisition_pipeline import run_specialization
from engine.http_source_fetch import get_html
from engine.embedded_markup import CALL, TAG, _literal_args
from engine.source_scoped_evidence import _nested_scopes
from engine.source_page_acquire import SourceAccessError
from engine.spec_source_resolver import SpecializationResolutionError
from engine.source_choice_visibility import source_option_visible


def _html_outside_guide_literals(html: str) -> str:
    """Remove exactly parsed embedded WHML JSON string literals, not other JS."""
    intervals = []
    decoder = json.JSONDecoder()
    for call in CALL.finditer(html):
        tail = html[call.end():]
        prefix = len(tail) - len(tail.lstrip())
        try:
            body, consumed = decoder.raw_decode(tail.lstrip())
        except (ValueError, TypeError):
            continue
        if isinstance(body, str):
            intervals.append((call.end() + prefix, call.end() + prefix + consumed))
    for start, end in reversed(intervals):
        html = html[:start] + (" " * (end - start)) + html[end:]
    return html


def _unbound_contexts(packet: dict, technical_ids: set[str],
                      page_html: str | None) -> dict:
    """Scope/type/impact metadata only, never original text snippets."""
    source = packet["payloads"][0]
    raw = source["original_whml"]
    scopes, structure_issues = _nested_scopes(raw)
    outside = (_html_outside_guide_literals(page_html)
               if isinstance(page_html, str) else None)
    out = {}
    for ident in sorted(technical_ids):
        rows = []
        for entry in source["conditional_expressions"]:
            expr = entry["expression"]
            expr_ids = set(re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]*", expr))
            if ident not in expr_ids:
                continue
            offset = entry["position"]
            parents = [x for x in scopes if x["start"] <= offset < x["end"]]
            closest_rows = [x for x in parents if x["tag"] in {"li", "tr"}]
            tooltip = any(x["tag"] == "tooltip" for x in parents)
            ordered = any(x["tag"] == "ol" for x in parents)
            unordered = any(x["tag"] == "ul" for x in parents)
            # Do not infer an action from spell text alone. Report only how
            # many possible action markers coexist in that exact source row.
            if closest_rows:
                item = min(closest_rows, key=lambda x: x["end"] - x["start"])
                fragment = raw[item["body_start"]:item["body_end"]]
            else:
                fragment = ""
            ability_tokens = len(re.findall(
                r"\[(?:spell|rt-step|rt-step-group)\s*=\s*\d+", fragment, re.I
            ))
            rows.append({
                "conditional_tag": entry["tag"],
                "in_ordered_action_candidate": bool(ordered and closest_rows),
                "in_unordered_notes_candidate": bool(unordered and closest_rows),
                "in_table_row": any(x["tag"] == "tr" for x in parents),
                "in_tooltip": tooltip,
                "nearest_list_or_table_spell_tokens": ability_tokens,
                "condition_is_standalone_marker": not any(
                    x["start"] == offset for x in scopes
                ),
            })
        declared_syntax = re.findall(
            r"\[[A-Za-z][\w-]*\b[^\]]{0,260}\b(?:id|name|value)"
            r"\s*=\s*['\"]?" + re.escape(ident) + r"(?:['\"\s\]])",
            raw, flags=re.I,
        )
        out[ident] = {
            "conditional_occurrences": len(rows),
            "condition_locations": rows,
            "whml_other_possible_named_declarations": len(declared_syntax),
            "raw_html_mentions_outside_whml_literal": (
                outside.count(ident) if outside is not None else None
            ),
            "scope_parser_issue_kinds": structure_issues,
            "resolved_by_this_audit": False,
        }
    return out


def review_source(packet: dict, page_html: str | None = None) -> dict:
    declared = {option["id"]
                for p in packet["payloads"]
                for option in p["option_definitions"]}
    expressions = [c["expression"]
                   for p in packet["payloads"]
                   for c in p["conditional_expressions"]]
    recognized = 0
    decisions = 0
    unknown = 0
    unknown_kinds = Counter()
    undeclared_option_ids = set()
    for expression in expressions:
        # Empty selection checks that the expression is syntactically and
        # semantically interpretable for the declared options, not whether
        # its corresponding UI choice should be visible to a real player.
        result = source_option_visible(expression, set(), declared)
        if result is None:
            unknown += 1
            compact = re.sub(r"\s+", "", expression)
            tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]*|[()!&|]", compact)
            if "".join(tokens) != compact:
                unknown_kinds["unsupported_characters"] += 1
            elif any(t not in declared for t in tokens
                     if t not in {"(", ")", "!", "&", "|"}):
                unknown_kinds["undeclared_option_reference"] += 1
                undeclared_option_ids.update(t for t in tokens
                    if t not in {"(", ")", "!", "&", "|"} and t not in declared)
            else:
                unknown_kinds["malformed_supported_grammar"] += 1
        else:
            recognized += 1
            decisions += 1
    raw = "\n".join(p["original_whml"] for p in packet["payloads"])
    undeclared_diagnostics = {}
    for option_id in sorted(undeclared_option_ids):
        escaped = re.escape(option_id)
        undeclared_diagnostics[option_id] = {
            "mentions_in_source": len(re.findall(escaped, raw)),
            "looks_like_display_option_definition": bool(re.search(
                r"\[display-option\s*=\s*['\"]?" + escaped + r"\b", raw,
                re.I)),
            "looks_like_toggler_definition": bool(re.search(
                r"\[toggler\s*=\s*['\"]?" + escaped + r"\b", raw,
                re.I)),
            "matches_case_insensitive_declared_id": any(
                x.casefold() == option_id.casefold() for x in declared),
        }
    return {
        "captured_real_source": True,
        "conditional_expression_count": len(expressions),
        "declared_option_count": len(declared),
        "recognized_visibility_expressions": recognized,
        "unrecognized_visibility_expressions_review": unknown,
        "unrecognized_reason_counts": dict(sorted(unknown_kinds.items())),
        "undeclared_technical_option_identifiers": sorted(undeclared_option_ids)[:12],
        "undeclared_identifier_structure": undeclared_diagnostics,
        "unbound_condition_contexts": _unbound_contexts(
            packet, undeclared_option_ids, page_html),
        "source_selector_expressions_all_interpreted": unknown == 0,
        "unbound_conditional_selector_review_required": unknown > 0,
        "source_choice_completeness_verified": False,
        "hero_and_fight_contexts_verified": False,
        "gameplay_meaning_verified": False,
        "automatic_publish_allowed": False,
    }


def main() -> None:
    for name, label in (("생존 사냥꾼", "survival"),
                        ("비전 마법사", "arcane")):
        try:
            with TemporaryDirectory() as tmp:
                root = Path(tmp)
                obtained = {}
                def capture_html(url: str) -> str:
                    page = get_html(url)
                    obtained["html"] = page
                    return page
                run_specialization(name, root, fetch_html=capture_html)
                packet = json.loads(
                    (root / "editorial-evidence-private.json").read_text("utf8")
                )
                report = review_source(packet, obtained.get("html"))
                print("cross_spec_" + label + "_status=source_expression_inspected")
                for key, value in report.items():
                    print("cross_spec_" + label + "_" + key + "=" +
                          json.dumps(value))
        except (SourceAccessError, SpecializationResolutionError,
                ValueError, KeyError, OSError) as exc:
            print("cross_spec_" + label + "_status=source_review_required")
            print("cross_spec_" + label + "_error_class=" + type(exc).__name__)


if __name__ == "__main__":
    main()
