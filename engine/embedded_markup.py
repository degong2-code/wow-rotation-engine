"""Inspect JSON-compatible WHML literal payloads in previously acquired HTML.

No JavaScript execution, network, publication, or claim that live pages use WHML.
Output is metadata only, with source passage text excluded.
"""
import hashlib
import json
import re

CALL = re.compile(r"WH\s*\.\s*markup\s*\.\s*printHtml\s*\(")
TAG = re.compile(r"\[([a-zA-Z][\w-]*)\b([^\]]*)\]")
ATTR = re.compile(r"""([a-zA-Z][\w-]*)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s\]]+))""")


def _attrs(raw: str) -> dict[str, str]:
    return {m.group(1).lower(): next((v for v in m.groups()[1:] if v is not None), "")
            for m in ATTR.finditer(raw)}


def _literal_args(source: str, start: int) -> tuple[str, str] | None:
    decoder = json.JSONDecoder()
    try:
        rest = source[start:].lstrip()
        body, used = decoder.raw_decode(rest)
        rest = rest[used:].lstrip()
        if not rest.startswith(","):
            return None
        target, _ = decoder.raw_decode(rest[1:].lstrip())
        if not isinstance(body, str) or not isinstance(target, str):
            return None
        return body, target
    except (ValueError, TypeError):
        return None



NESTED = re.compile(r"\[(/?)(tabs|tab)\b([^\]]*)\]", re.IGNORECASE)


def _digest(value: str) -> dict:
    text = re.sub(r"\s+", " ", value).strip()
    return {"characters": len(text), "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}


def _tab_groups(body: str) -> tuple[list[dict], list[str]]:
    """Build a bounded tab tree from a literal WHML payload, never rendering it."""
    groups: list[dict] = []
    stack: list[tuple[str, int, int, int | None]] = []
    problems: list[str] = []
    for token in NESTED.finditer(body):
        closing, name, raw_attrs = bool(token.group(1)), token.group(2).lower(), token.group(3)
        if not closing:
            if name == "tabs":
                idx = len(groups)
                attrs = _attrs(raw_attrs)
                groups.append({"group_index": idx, "label_digest": _digest(attrs.get("name", "")),
                               "closed": False, "tabs": []})
                stack.append(("tabs", token.end(), idx, None))
            else:
                parent = next((x for x in reversed(stack) if x[0] == "tabs"), None)
                if parent is None:
                    problems.append("orphan_tab_without_parent")
                    continue
                group_idx = parent[2]
                tab_idx = len(groups[group_idx]["tabs"])
                attrs = _attrs(raw_attrs)
                groups[group_idx]["tabs"].append({
                    "tab_index": tab_idx, "label_digest": _digest(attrs.get("name", "")),
                    "closed": False, "body_digest": None,
                })
                stack.append(("tab", token.end(), group_idx, tab_idx))
            continue
        if not stack or stack[-1][0] != name:
            problems.append("unmatched_closing_" + name)
            continue
        _, start, group_idx, tab_idx = stack.pop()
        if name == "tabs":
            groups[group_idx]["closed"] = True
        else:
            tab = groups[group_idx]["tabs"][tab_idx]
            tab["closed"] = True
            tab["body_digest"] = _digest(body[start:token.start()])
    if stack:
        problems.append("unclosed_tab_or_tab_group")
    return groups, sorted(set(problems))



TOOLTIP_BODY = re.compile(r"\[tooltip\b([^\]]*)\](.*?)\[/tooltip\]", re.I | re.S)
DISPLAY_OPTION = re.compile(
    r"\[display-option\s*=\s*(?:\"([^\"]+)\"|'([^']+)'|([^\s\]]+))"
    r"([^\]]*)\](.*?)\[/display-option\]", re.I | re.S
)
OPTION_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")


def _decision_controls(body: str) -> dict:
    """Inventory declared switches and all conditional display expressions.

    The actual meaning of these switches, including whether a potion changes
    an opener, is an editorial question and is never inferred here.
    """
    options = []
    for m in DISPLAY_OPTION.finditer(body):
        ident = next(v for v in m.groups()[:3] if v is not None)
        attr = _attrs(m.group(4))
        options.append({
            "id": ident[:120],
            "radio_group": attr.get("radio", "")[:120],
            "checked_by_default": bool(re.search(r"(?:^|\s)checked(?:\s|$)", m.group(4))),
            "label_digest": _digest(m.group(5)),
        })
    declared = {option["id"] for option in options}
    expressions = []
    for tag in TAG.finditer(body):
        attr = _attrs(tag.group(2))
        if "display-options" not in attr:
            continue
        expr = attr["display-options"]
        names = sorted(set(OPTION_TOKEN.findall(expr)))
        expressions.append({
            "tag": tag.group(1).lower(),
            "expression": expr[:500],
            "option_ids": names,
            "unknown_option_ids": sorted(set(names) - declared),
        })
    radio_groups = {}
    for option in options:
        radio_groups.setdefault(option["radio_group"], []).append(option["id"])
    return {
        "option_definitions": options,
        "radio_groups": radio_groups,
        "conditional_occurrences": len(expressions),
        "conditional_expressions": expressions,
        "unknown_conditional_option_ids": sorted({
            ident for expr in expressions for ident in expr["unknown_option_ids"]
        }),
    }


def _tooltip_definition_bodies(body: str) -> list[dict]:
    """Capture contents by digest, avoiding empty hydrated DOM templates."""
    definitions = []
    for m in TOOLTIP_BODY.finditer(body):
        ident = _attrs(m.group(1)).get("name")
        if ident:
            definitions.append({"name": ident[:120], "body_digest": _digest(m.group(2))})
    return definitions


def inspect_embedded_whml(html: str) -> dict:
    calls = list(CALL.finditer(html))
    payloads = []
    unsupported = 0
    for call in calls:
        parsed = _literal_args(html, call.end())
        if parsed is None:
            unsupported += 1
            continue
        body, target = parsed
        definitions = []
        references = []
        controls = {"tabs": 0, "tab": 0, "toggler": 0, "tooltip": 0}
        for tag in TAG.finditer(body):
            name = tag.group(1).lower()
            attrs = _attrs(tag.group(2))
            if name in controls:
                controls[name] += 1
            if name == "tooltip" and attrs.get("name"):
                definitions.append(attrs["name"][:120])
            for key, value in attrs.items():
                if re.fullmatch(r"tooltip\d*", key):
                    references.append({"attribute": key, "name": value[:120]})
        tab_groups, nested_issues = _tab_groups(body)
        tooltip_bodies = _tooltip_definition_bodies(body)
        display_switches = _decision_controls(body)
        defined = set(definitions)
        used = {x["name"] for x in references}
        payloads.append({
            "target": target[:120],
            "characters": len(body),
            "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "components": controls,
            "tab_groups": tab_groups,
            "named_tooltip_bodies": tooltip_bodies,
            "display_switches": display_switches,
            "nested_structure_issues": nested_issues,
            "named_tooltip_definitions": definitions,
            "tooltip_references": references,
            "unresolved_reference_names": sorted(used - defined),
            "unreferenced_definition_names": sorted(defined - used),
            "duplicate_definition_names": sorted(x for x in defined if definitions.count(x) > 1),
        })
    return {
        "literal_call_candidates": len(calls),
        "decoded_payloads": len(payloads),
        "unsupported_nonliteral_calls": unsupported,
        "payloads": payloads,
        "javascript_executed": False,
        "source_text_in_report": False,
        "current_live_guide_verified": False,
    }
