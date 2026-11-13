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


def _nested_scopes(whml: str, diagnostics: list[dict] | None = None) -> tuple[list[dict], list[str]]:
    """Pair exact brackets; unmatched scopes require human review."""
    opened: list[dict] = []
    closed: list[dict] = []
    issues: list[str] = []
    for token in TOKENS.finditer(whml):
        closing, tag, attrs_raw = bool(token.group(1)), token.group(2).lower(), token.group(3)
        attrs = _attributes(attrs_raw)
        if not closing:
            # Unknown custom WHML components (e.g. timeline steps) can be
            # standalone tokens. Never invent a closing scope for them.
            if tag not in PAIRED:
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
            if diagnostics is not None:
                diagnostics.append({"kind": "closing_without_open",
                                    "offset": token.start(), "closing_tag": tag})
            continue
        if opened[-1]["tag"] != tag:
            issues.append("crossed_or_unmatched_closing")
            if diagnostics is not None:
                diagnostics.append({"kind": "crossed_or_unmatched_closing",
                                    "offset": token.start(), "closing_tag": tag,
                                    "open_tag": opened[-1]["tag"]})
            continue
        scope = opened.pop()
        scope["body_end"] = token.start()
        scope["end"] = token.end()
        closed.append(scope)
    if opened:
        issues.append("unclosed_relevant_scopes")
        if diagnostics is not None:
            diagnostics.extend({"kind": "unclosed_relevant_scopes",
                                "offset": entry["start"], "open_tag": entry["tag"]}
                               for entry in opened[-8:])
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
        diagnostics: list[dict] = []
        scopes, issues = _nested_scopes(body, diagnostics)
        visibility = [s for s in scopes if "display-options" in s["attributes"]]
        tabs = [s for s in scopes if s["tag"] == "tab"]
        headings = [s for s in scopes if s["tag"] in HEADING_TAGS]
        definitions = [s for s in scopes if s["tag"] == "tooltip"]
        list_containers = [s for s in scopes if s["tag"] in {"ol", "ul"}]
        list_row_counts: dict[int, int] = {}
        standalone_conditions = []
        for token in TOKENS.finditer(body):
            if token.group(1) or token.group(2).lower() in PAIRED:
                continue
            attrs = _attributes(token.group(3))
            if "display-options" in attrs:
                standalone_conditions.append({
                    "tag": token.group(2).lower(),
                    "start": token.start(),
                    "end": token.end(),
                    "expression": attrs["display-options"],
                    "original_markup": body[token.start():token.end()],
                    "scope_unverified": True,
                })
        accounted_conditions = {scope["start"] for scope in visibility}
        accounted_conditions.update(x["start"] for x in standalone_conditions)
        unassigned_conditions = [
            x["position"] for x in source.get("conditional_expressions", [])
            if x["position"] not in accounted_conditions
        ]
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
            # Ordered priorities, unordered explanatory notes and timelines
            # are different source containers. This is only structural
            # provenance, not proof that a row is a rotation action.
            parent_lists = sorted(
                (l for l in list_containers if _covering(l, scope)),
                key=lambda l: (l["end"] - l["start"]), reverse=True,
            )
            list_parent = parent_lists[-1] if parent_lists else None
            ordinal = None
            if list_parent is not None:
                location = list_parent["start"]
                list_row_counts[location] = list_row_counts.get(location, 0) + 1
                ordinal = list_row_counts[location]
            prior_headings = [h for h in headings if h["end"] <= scope["start"]]
            heading = prior_headings[-1] if prior_headings else None
            nested_markers = [
                x for x in standalone_conditions
                if scope["start"] <= x["start"] < scope["end"]
            ]
            refs = [
                {"position": r["position"], "definition_name": r["definition_name"]}
                for r in source.get("tooltip_references", [])
                if scope["start"] <= r["position"] < scope["end"]
            ]
            rows.append({
                "kind": "source_list_item" if scope["tag"] == "li" else "source_table_row",
                "source_start": scope["start"],
                "containing_list": (
                    {"tag": list_parent["tag"], "start": list_parent["start"],
                     "end": list_parent["end"], "ordinal": ordinal}
                    if list_parent is not None else None
                ),
                "source_end": scope["end"],
                "original_whml_fragment": body[scope["body_start"]:scope["body_end"]],
                "active_display_scopes": [
                    {"expression": v["attributes"]["display-options"],
                     "start": v["start"], "end": v["end"]}
                    for v in active
                ],
                "standalone_condition_markers_inside_row": [
                    {"tag": m["tag"], "start": m["start"],
                     "expression": m["expression"]} for m in nested_markers
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
                "contains_multiple_visibility_cases": bool(internal or nested_markers),
                "gameplay_action_interpreted": False,
            })
        results.append({
            "guide_body_sha256": source["sha256"],
            "source_characters": len(body),
            "source_list_rows": rows,
            "visible_predicate_scope_count": len(visibility),
            "standalone_condition_markers": standalone_conditions,
            "source_condition_expression_count": len(source.get("conditional_expressions", [])),
            "unassigned_conditional_positions": unassigned_conditions,
            "unresolved_structure_issues": issues,
            "structure_issue_positions": diagnostics[:20],
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


def unbound_selector_impact(packet: dict, scoped: dict) -> dict:
    """Identify unresolved *source visibility* that could hide action rows.

    This is an editorial REVIEW gate, not a proof of gameplay error.
    Does not reveal source prose, unknown IDs or expression strings in reports.
    """
    if (packet.get("schema_version") != "source-editorial-evidence-private-v1"
            or len(packet.get("payloads", [])) != len(scoped.get("payloads", []))):
        raise SourceAccessError("Unmatched private source and scoped evidence")
    token = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
    ability = re.compile(r"\[(?:spell|rt-step|rt-step-group)\s*=\s*\d+", re.I)
    all_expressions = critical_rows = ability_rows = potential_steps = 0
    unique_unbound = set()
    for source, scope in zip(packet["payloads"], scoped["payloads"]):
        if source["sha256"] != scope["guide_body_sha256"]:
            raise SourceAccessError("Mismatched source and scoped body SHA")
        declared = {o["id"] for o in source.get("option_definitions", [])}
        for condition in source.get("conditional_expressions", []):
            missing = set(token.findall(condition["expression"])) - declared
            if missing:
                all_expressions += 1
                unique_unbound.update(missing)
                if condition["tag"] in {"rt-step", "rt-step-group"}:
                    potential_steps += 1
        for row in scope["source_list_rows"]:
            owner = row.get("containing_list")
            if (not owner or owner.get("tag") != "ol"
                    or row.get("inside_tooltip_definition")):
                continue
            expressions = (
                [x["expression"] for x in row["active_display_scopes"]] +
                [x["expression"] for x in row["nested_display_fragments"]] +
                [x["expression"] for x in row["standalone_condition_markers_inside_row"]]
            )
            if not any(set(token.findall(expr)) - declared for expr in expressions):
                continue
            critical_rows += 1
            if ability.search(row["original_whml_fragment"]):
                ability_rows += 1
    return {
        "unbound_selector_expression_occurrences": all_expressions,
        "unbound_selector_identifier_count": len(unique_unbound),
        "unbound_selector_ordered_row_candidates": critical_rows,
        "unbound_selector_ordered_ability_row_candidates": ability_rows,
        "unbound_selector_standalone_step_candidates": potential_steps,
        "source_selector_references_resolved": all_expressions == 0,
        "ordered_action_review_required": bool(critical_rows or potential_steps),
        "gameplay_action_meaning_proven": False,
        "source_text_in_report": False,
    }


def scoped_metadata(scoped: dict) -> dict:
    """Public-safe counts only: do not emit source fragments or expressions."""
    rows = [row for source in scoped["payloads"] for row in source["source_list_rows"]]
    issues = Counter(issue for p in scoped["payloads"] for issue in p["unresolved_structure_issues"])
    examples = [sample for p in scoped["payloads"]
                for sample in p["structure_issue_positions"]]
    return {
        "schema_version": "whml-scoped-source-audit-v1",
        "guide_body_payload_count": len(scoped["payloads"]),
        "source_row_candidates": len(rows),
        "rows_under_display_predicates": sum(bool(x["active_display_scopes"]) for x in rows),
        "rows_with_mixed_visibility": sum(x["contains_multiple_visibility_cases"] for x in rows),
        "rows_inside_tooltip_definitions": sum(x["inside_tooltip_definition"] for x in rows),
        "rows_in_ordered_lists": sum(
            bool(x["containing_list"] and x["containing_list"]["tag"] == "ol")
            for x in rows
        ),
        "rows_in_unordered_lists": sum(
            bool(x["containing_list"] and x["containing_list"]["tag"] == "ul")
            for x in rows
        ),
        "standalone_conditional_markers": sum(
            len(p["standalone_condition_markers"]) for p in scoped["payloads"]),
        "paired_conditional_scopes": sum(
            p["visible_predicate_scope_count"] for p in scoped["payloads"]),
        "source_condition_expression_count": sum(
            p["source_condition_expression_count"] for p in scoped["payloads"]),
        "unassigned_conditional_expressions": sum(
            len(p["unassigned_conditional_positions"]) for p in scoped["payloads"]),
        "standalone_conditional_marker_types": dict(sorted(Counter(
            m["tag"] for p in scoped["payloads"]
            for m in p["standalone_condition_markers"]
        ).items())),
        "structure_issue_types": dict(sorted(issues.items())),
        "structure_issue_positions": examples[:20],
        "source_text_in_report": False,
        "gameplay_action_interpreted": False,
        "gameplay_meaning_verified": False,
        "automatic_publish_allowed": False,
    }
