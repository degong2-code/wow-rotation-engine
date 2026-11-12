"""Offline HTML structure inventory for source acquisition.

Finds *candidates* for nested tabs, collapsed regions, and tooltip triggers
in legitimately available static HTML. No network, browser, JavaScript
execution, or claims about completeness of live UI. Reports no long body text.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re

SCHEMA = "html-structure-inventory-v1"
MAX_HTML_BYTES = 12 * 1024 * 1024
MAX_NODES = 100000
MAX_ITEMS = 6000
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"}
HEADING = {"h1", "h2", "h3", "h4", "h5", "h6"}
INLINE_TIPS = ("title", "data-original-title", "data-hint-body",
               "data-tippy-content", "data-bs-title", "data-tooltip-content")
REFERENCE_TIPS = ("aria-describedby", "data-tooltip-id", "data-tooltip-target",
                  "tooltip", "tooltip2")
SCRIPT_MARKERS = ("WH.markup.printHtml", "__NEXT_DATA__", "data.pageMeta",
                  "tooltip2", "application/ld+json")


@dataclass
class Node:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    parent: "Node | None" = None
    parts: list = field(default_factory=list)

    def text(self) -> str:
        return " ".join(
            part.text() if isinstance(part, Node) else part
            for part in self.parts
        )


class _Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#document")
        self.stack = [self.root]
        self.nodes = []

    def handle_starttag(self, tag, attrs):
        if len(self.nodes) >= MAX_NODES:
            raise ValueError("HTML node limit exceeded")
        attr = {str(k).lower(): str(v) if v is not None else "" for k, v in attrs}
        node = Node(tag, attr, self.stack[-1])
        self.stack[-1].parts.append(node)
        self.nodes.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].parts.append(data)


def _compact(value: str, limit: int = 90) -> str:
    return re.sub(r"\s+", " ", value).strip()[:limit]


def _digest(body: str) -> dict:
    cleaned = re.sub(r"\s+", " ", body).strip()
    return {"characters": len(cleaned),
            "sha256": hashlib.sha256(cleaned.encode("utf-8")).hexdigest()}


def _hidden(node: Node) -> list[str]:
    attr = node.attrs
    result = []
    if "hidden" in attr or attr.get("aria-hidden", "").lower() == "true":
        result.append("attribute")
    style = re.sub(r"\s+", "", attr.get("style", "").lower())
    if "display:none" in style or "visibility:hidden" in style:
        result.append("style")
    if node.tag == "details" and "open" not in attr:
        result.append("collapsed_details")
    return result


def _parent_row(node: Node) -> str | None:
    cur = node.parent
    while cur is not None:
        if cur.tag == "tr":
            return cur.attrs.get("id") or _digest(cur.text())["sha256"][:12]
        cur = cur.parent
    return None


def _ref_body(ref: str, ids: dict[str, Node]) -> tuple[str, str | None]:
    target = ids.get(ref.removeprefix("#"))
    if target is None:
        return "unresolved_reference", None
    body = _compact(target.text(), 100000)
    if not body:
        return "empty_reference", None
    return "reference_body", body


def inspect_html(html: str) -> dict:
    if not isinstance(html, str):
        raise ValueError("HTML must be text")
    if len(html.encode("utf-8")) > MAX_HTML_BYTES:
        raise ValueError("HTML size limit exceeded")
    parser = _Parser()
    parser.feed(html)
    parser.close()
    ids = {}
    duplicate_ids = []
    for node in parser.nodes:
        ident = node.attrs.get("id")
        if ident:
            if ident in ids:
                duplicate_ids.append(ident)
            else:
                ids[ident] = node

    controls = []
    hidden_regions = []
    tooltips = []
    unresolved = []
    markers = {marker: 0 for marker in SCRIPT_MARKERS}
    active_heading = None

    for n, node in enumerate(parser.nodes):
        a = node.attrs
        if node.tag in HEADING:
            active_heading = _compact(node.text())
        heading = active_heading
        if node.tag == "script":
            data = node.text()
            for marker in SCRIPT_MARKERS:
                markers[marker] += data.count(marker)
        is_hidden = _hidden(node)
        if is_hidden and len(hidden_regions) < MAX_ITEMS:
            hidden_regions.append({
                "element": n, "tag": node.tag,
                "id": a.get("id"), "causes": is_hidden, "section": heading,
                "body": _digest(node.text())
            })

        role = a.get("role", "")
        control_type = None
        if node.tag == "select":
            control_type = "select"
        elif node.tag == "summary":
            control_type = "details_summary"
        elif role == "tab":
            control_type = "tab"
        elif node.tag == "input" and a.get("type", "").lower() in {"radio", "checkbox"}:
            control_type = a["type"].lower()
        elif "aria-controls" in a or "aria-expanded" in a or "data-bs-target" in a:
            control_type = "controlled"
        elif node.tag == "button":
            control_type = "button"
        if control_type and len(controls) < MAX_ITEMS:
            targets = []
            for attr in ("aria-controls", "data-bs-target", "data-target"):
                if a.get(attr):
                    targets += a[attr].split()
            if role == "tab" and a.get("href", "").startswith("#"):
                targets.append(a["href"])
            targets = [x.lstrip("#") for x in targets]
            options = []
            if node.tag == "select":
                options = [_compact(x.text()) for x in parser.nodes
                           if x.parent is node and x.tag == "option"]
            controls.append({
                "element": n, "type": control_type, "id": a.get("id"),
                "label": _compact(a.get("aria-label", "") or node.text(), 75),
                "section": heading, "targets": targets,
                "targets_in_html": [v for v in targets if v in ids],
                "targets_not_in_html": [v for v in targets if v not in ids],
                "options": options
            })

        found = []
        for attr in INLINE_TIPS:
            if attr in a:
                found.append((attr, "inline_body" if a[attr].strip() else "empty_body", a[attr]))
        for attr in REFERENCE_TIPS:
            if attr not in a:
                continue
            refs = a[attr].split() if attr == "aria-describedby" else [a[attr]]
            for ref in refs:
                status, body = _ref_body(ref, ids)
                found.append((attr, status, body))
                if status != "reference_body":
                    unresolved.append({"element": n, "attribute": attr, "reference": ref})
        if a.get("data-tooltip"):
            value = a["data-tooltip"]
            if value.lstrip("#") in ids:
                status, body = _ref_body(value, ids)
            elif len(value) >= 18:
                status, body = "inline_body", value
            else:
                status, body = "unresolved_reference", None
                unresolved.append({"element": n, "attribute": "data-tooltip",
                                   "reference": value})
            found.append(("data-tooltip", status, body))
        # Text-only '?' or info triggers often have content in JS, not static HTML.
        if not found and node.tag in {"button", "span", "a"} and _compact(node.text()) == "?":
            found.append(("question_icon", "body_not_found_in_static_html", None))
        if found and len(tooltips) < MAX_ITEMS:
            tooltips.append({
                "element": n, "tag": node.tag, "id": a.get("id"),
                "section": heading, "table_row": _parent_row(node),
                "descriptions": [
                    {"attribute": attr, "status": status,
                     "body": _digest(body) if body is not None else None}
                    for attr, status, body in found
                ],
            })

    return {
        "schema_version": SCHEMA,
        "inspection": "static_html_only",
        "node_count": len(parser.nodes),
        "control_candidates": controls,
        "hidden_region_candidates": hidden_regions,
        "tooltip_trigger_candidates": tooltips,
        "unresolved_tooltip_references": unresolved,
        "duplicate_ids": sorted(set(duplicate_ids)),
        "embedded_script_markers": {k: v for k, v in markers.items() if v},
        "candidate_lists_truncated": any(
            len(x) == MAX_ITEMS for x in (controls, hidden_regions, tooltips)
        ),
        "source_text_in_report": False,
        "live_ui_completeness_verified": False,
        "dynamic_script_content_extracted": False,
        "gameplay_meaning_verified": False,
        "automatic_publish_allowed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Existing local HTML")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = inspect_html(args.input.read_text(encoding="utf-8"))
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
