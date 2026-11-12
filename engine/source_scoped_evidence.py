"""Private source-scope index for WHML lists and conditional content.

Preserve exact nested UI predicates with source ranges, and explicitly mark
list items with conditional subparts. A display-options expression governs
visibility; it is not itself a gameplay predicate or rotation priority.
No HTML rendering, guessing skill names, execution or source publishing.
"""
from __future__ import annotations

from collections import Counter
import re

from .source_page_acquire import SourceAccessError

TOKENS = re.compile(r"\[(/?)([A-Za-z][\w-]*)\b([^\]]*)\]")
ATTR = re.compile(
    r"""([A-Za-z][\w-]*)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s\]]+))"""
)
# Track only paired containers relevant to source context; there are many
# inline/self-contained WHML tokens whose closing partner is optional/absent.
PAIRED = {
    "div", "span", "p", "li", "ol", "ul", "table", "tbody", "tr", "td",
    "th", "h1", "h2", "h3", "h4", "h5", "h6", "tabs", "tab", "toggler",
    "tooltip", "section", "blockquote", "display-option",
}
EVIDENCE_ROWS = {"li", "tr"}
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


def _attributes(raw: str) -> dict[str, str]:
    return {
        m.group(1).lower(): next(x for x in m.groups()[1:] if x is not None)
        for m in ATTR.finditer(raw)
    }


def _nested_scopes(whml: str) -> tuple[list[dict], list[str]]:
    """Pair exact brackets; unmatched scopes require human review."""
    opened: list[dict] = []
    closed: list[dict] = []
    issues: list[str] = []
    for token in TOKENS.finditer(whml):
        closing, tag, attrs_raw = bool(token.group(1)), token.group(2).lower(), token.group(3)
        attrs = _attributes(attrs_raw)
        if not closing:
            if tag not in PAIRED and "display-options" not in attrs:
                continue
            opened.append({
                "tag": tag,
                "start": token.start(),
                "body_start": token.end(),
                "attributes": attrs,
                "parent_start": opened[-1]["start"] if opened else None,
            })
            continue
        if tag not in PAIRED and not any(o["tag"] == tag for o in opened):
            continue
        if not opened:
            issues.append("closing_without_open")
            continue
        if opened[-1]["tag"] != tag:
            issues.append("crossed_or_unmatched_closing")
            continue
        scope = opened.pop()
        scope["body_end"] = token.start()
        scope["end"] = token.end()
        closed.append(scope)
    if opened:
        issues.append("unclosed_relevant_scopes")
    return sorted(closed, key=lambda x: x["start"]), sorted(set(issues))


def _covering(outer: dict, inner: dict) -> bool:
    return outer["start"] <= inner["start"] and outer["end"] >= inner["end"]


def scoped_from_packet(packet: dict) -> dict:
    """Index private list/row evidence under actual WHML display scopes."""
    if packet.get("schema_version") != "source-editorial-evidence-private-v1":
        raise SourceAccessError("Expected private WHML evidence packet, not a public audit")
    results = []
    for source in packet.get("payloads", []):
        body = source.get("original_whml")
        if not isinstance(body, str):
            raise SourceAccessError("Original private WHML is unavailable")
        if len(body) > 3_000_000:
            raise SourceAccessError("Guide source exceeds scoping limit")
        scopes, issues = _nested_scopes(body)
        visibility = [s for s in scopes if "display-options" in s["attributes"]]
        tabs = [s for s in scopes if s["tag"] == "tab"]
        headings = [s for s in scopes if s["tag"] in HEADING_TAGS]
        definitions = [s for s in scopes if s["tag"] == "tooltip"]
        rows = []
        for scope in scopes:
            if scope["tag"] not in EVIDENCE_ROWS:
                continue
            active = sorted(
                (v for v in visibility if _covering(v, scope)),
                key=lambda x: x["start"],
            )
            internal = sorted(
                (v for v in visibility if _covering(scope, v)
                 and v["start"] != scope["start"]),
                key=lambda x: x["start"],
            )
            tab_owners = sorted(
                (t for t in tabs if _covering(t, scope)), key=lambda x: x["start"],
            )
            in_tooltip = any(_covering(t, scope) for t in definitions)
            prior_headings = [h for h in headings if h["end"] <= scope["start"]]
            heading = prior_headings[-1] if prior_headings else None
            refs = [
                {"position": r["position"], "definition_name": r["definition_name"]}
                for r in source.get("tooltip_references", [])
                if scope["start"] <= r["position"] < scope["end"]
            ]
            rows.append({
                "kind": "source_list_item" if scope["tag"] == "li" else "source_table_row",
                "source_start": scope["start"],
                "source_end": scope["end"],
                "original_whml_fragment": body[scope["body_start"]:scope["body_end"]],
                "active_display_scopes": [
                    {"expression": v["attributes"]["display-options"],
                     "start": v["start"], "end": v["end"]}
                    for v in active
                ],
                "nested_display_fragments": [
                    {"expression": v["attributes"]["display-options"],
                     "start": v["start"], "end": v["end"]}
                    for v in internal
                ],
                "containing_tabs": [
                    {"start": t["start"], "end": t["end"],
                     "label_whml": t["attributes"].get("name", "")}
                    for t in tab_owners
                ],
                "previous_heading": (
                    {"start": heading["start"],
                     "body_whml": body[heading["body_start"]:heading["body_end"]]}
                    if heading else None
                ),
                "tooltip_references": refs,
                "inside_tooltip_definition": in_tooltip,
                "contains_multiple_visibility_cases": bool(internal),
                "gameplay_action_interpreted": False,
            })
        results.append({
            "guide_body_sha256": source["sha256"],
            "source_characters": len(body),
            "source_list_rows": rows,
            "visible_predicate_scope_count": len(visibility),
            "unresolved_structure_issues": issues,
            "source_text_may_be_public": False,
        })
    return {
        "schema_version": "whml-scoped-source-evidence-private-v1",
        "payloads": results,
        "source_text_in_file": True,
        "source_text_may_be_public": False,
        "ui_visibility_is_gameplay_condition": False,
        "gameplay_action_interpreted": False,
        "gameplay_meaning_verified": False,
        "automatic_publish_allowed": False,
    }


def scoped_metadata(scoped: dict) -> dict:
    """Public-safe counts only: do not emit source fragments or expressions."""
    rows = [row for source in scoped["payloads"] for row in source["source_list_rows"]]
    issues = Counter(issue for p in scoped["payloads"] for issue in p["unresolved_structure_issues"])
    return {
        "schema_version": "whml-scoped-source-audit-v1",
        "guide_body_payload_count": len(scoped["payloads"]),
        "source_row_candidates": len(rows),
        "rows_under_display_predicates": sum(bool(x["active_display_scopes"]) for x in rows),
        "rows_with_mixed_visibility": sum(x["contains_multiple_visibility_cases"] for x in rows),
        "rows_inside_tooltip_definitions": sum(x["inside_tooltip_definition"] for x in rows),
        "structure_issue_types": dict(sorted(issues.items())),
        "source_text_in_report": False,
        "gameplay_action_interpreted": False,
        "gameplay_meaning_verified": False,
        "automatic_publish_allowed": False,
    }
