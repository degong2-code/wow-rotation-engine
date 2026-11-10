"""Apply reviewed, private rule/tip edits to original V11 HTML without redesign.

Edits target an exact public rule/tip ID and baseline evidence hash. The HTML
document is sliced only at the target element's *inner* span, preserving all
other original bytes, including V11 layout, CSS, icons, tooltips and scripts.

Run with a private V11 source, private patch JSON, and private output path:
  python -m engine.v2.patch_v11 SOURCE.html PATCH.json --output /private/updated.html
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import re

from bs4 import BeautifulSoup, Tag

from .build import ROOT
from .detail_bridge import _advanced_items, _section, extract_details
from .html_spans import SpanParser
from ..public_data import BASE

RULE_ID = re.compile(r"^([^:]+):([^:]+):table-([1-9]\d*):row-([1-9]\d*)$")
TIP_ID = re.compile(r"^([^:]+):([^:]+):tip-([1-9]\d*)$")
DANGEROUS_TAGS = {"script", "style", "iframe", "object", "embed", "form", "base", "meta", "link"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _safe_fragment(markup: str, *, inherited_html: str = "") -> None:
    """Preserve trusted V11 icon handlers; reject any new executable markup.

    Existing V11 spell icons use IMG onerror handlers. A patch that retains the
    same handler must not fail; new or modified event handlers are still denied.
    Spell/icon identities must remain unchanged for text-only detail edits.
    """
    if not isinstance(markup, str) or not markup.strip():
        raise ValueError("new_inner_html must be a non-empty HTML fragment")
    parsed = BeautifulSoup(markup, "html.parser")
    previous = BeautifulSoup(inherited_html, "html.parser")

    def events(dom):
        return Counter(
            (tag.name, key.lower(), str(value))
            for tag in dom.find_all(True)
            for key, value in tag.attrs.items()
            if key.lower().startswith("on")
        )

    allowed_events = events(previous)
    for event, count in events(parsed).items():
        if count > allowed_events[event]:
            raise ValueError("New or modified event handler attributes are forbidden")

    def icon_identity(dom):
        return (
            Counter(tag.get("data-spell") for tag in dom.select("[data-spell]")),
            Counter(tag.get("src") for tag in dom.select("img[src]")),
        )

    if icon_identity(parsed) != icon_identity(previous):
        raise ValueError("Original V11 spell icons must be preserved by text edits")

    for tag in parsed.find_all(True):
        if tag.name in DANGEROUS_TAGS:
            raise ValueError(f"Disallowed HTML tag in proposed edit: {tag.name}")
        for key, value in tag.attrs.items():
            if key.lower() in ("src", "href", "xlink:href", "formaction"):
                for item in value if isinstance(value, list) else [value]:
                    raw = str(item).strip().lower()
                    if raw.startswith(("javascript:", "data:", "vbscript:")):
                        raise ValueError("Executable URL is not accepted")


def _target_element(guide: Tag, update: dict) -> Tag:
    logical_id = update["id"]
    if update["kind"] == "rule":
        match = RULE_ID.fullmatch(logical_id)
        if not match or match[1] != guide["data-guide"]:
            raise ValueError(f"Invalid rule ID: {logical_id}")
        section = _section(guide, match[2])
        tables = [
            t for t in section.find_all("table")
            if t.select_one("thead th")
            and t.select_one("thead th").get_text(" ", strip=True) == "순위"
        ]
        table_index, row_index = int(match[3]), int(match[4])
        if table_index > len(tables):
            raise ValueError(f"No V11 table for {logical_id}")
        rows = tables[table_index - 1].select("tbody tr")
        if row_index > len(rows):
            raise ValueError(f"No V11 row for {logical_id}")
        cells = rows[row_index - 1].find_all(["td", "th"], recursive=False)
        if len(cells) < 3:
            raise ValueError(f"No condition cell for {logical_id}")
        return cells[2]

    match = TIP_ID.fullmatch(logical_id)
    if not match or match[1] != guide["data-guide"]:
        raise ValueError(f"Invalid Advanced Tip ID: {logical_id}")
    section = _section(guide, match[2])
    items = _advanced_items(section)
    index = int(match[3])
    if index > len(items):
        raise ValueError(f"No V11 Advanced Tip for {logical_id}")
    return items[index - 1]


def _source_span(source_text: str, parser: SpanParser, tag: Tag):
    if tag.sourceline is None or tag.sourcepos is None:
        raise ValueError("V11 tag has no source position")
    start = parser.offsets[tag.sourceline - 1] + tag.sourcepos
    candidates = [span for span in parser.spans if span.start == start]
    if len(candidates) != 1 or candidates[0].tag != tag.name:
        raise ValueError("V11 source position does not match the parsed element")
    span = candidates[0]
    # Any unexpected parser re-serialization means we should not alter this span.
    if span.inner(source_text) != tag.decode_contents():
        raise ValueError("V11 HTML node differs from its original source bytes")
    return span


def apply_patch(source_path: Path, patch: dict, public_base: Path = BASE) -> bytes:
    """Validate provenance for all original content before editing target spans."""
    source = Path(source_path).read_bytes()
    current_sha = hashlib.sha256(source).hexdigest()
    if not isinstance(patch, dict) or set(patch) != {
        "schema_version", "baseline_v11_sha256", "updates"
    } or patch["schema_version"] != "v11-private-patch-v1":
        raise ValueError("Wrong private patch schema")
    if patch["baseline_v11_sha256"] != current_sha:
        raise ValueError("V11 patch baseline SHA-256 mismatch")
    updates = patch["updates"]
    if not isinstance(updates, list) or len(updates) > 256:
        raise ValueError("Invalid patch updates")
    if not updates:
        return source

    baseline = extract_details(source_path, public_base, expected_sha256=current_sha)
    known = {}
    for guide in baseline["guides"]:
        for group in guide["rotation_groups"]:
            for rule in group["rules"]:
                known[rule["id"]] = ("rule", guide["guide_id"], rule["source_fragment_sha256"])
        for tip in guide["advanced_guidance"]:
            known[tip["id"]] = ("tip", guide["guide_id"], tip["source_fragment_sha256"])

    html = source.decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    guides = {g["data-guide"]: g for g in soup.select("div.manual-view[data-guide]")}
    spans = SpanParser(html)
    position_map = {span.start: span for span in spans.spans}
    offsets = spans.offsets
    changes = []
    seen = set()

    for update in updates:
        if not isinstance(update, dict) or set(update) != {
            "kind", "id", "expected_source_sha256", "new_inner_html"
        }:
            raise ValueError("Unexpected patch update fields")
        logical_id = update["id"]
        if not isinstance(logical_id, str) or logical_id in seen:
            raise ValueError(f"Invalid or duplicate patch ID: {logical_id}")
        seen.add(logical_id)
        expected = known.get(logical_id)
        if not expected or update["kind"] != expected[0]:
            raise ValueError(f"Unknown or wrongly classified V11 ID: {logical_id}")
        if not isinstance(update["expected_source_sha256"], str) or (
            SHA256.fullmatch(update["expected_source_sha256"]) is None
        ) or update["expected_source_sha256"] != expected[2]:
            raise ValueError(f"V11 source evidence mismatch: {logical_id}")
        replacement = update["new_inner_html"]
        tag = _target_element(guides[expected[1]], update)
        _safe_fragment(replacement, inherited_html=tag.decode_contents())
        if tag.sourceline is None or tag.sourcepos is None:
            raise ValueError(f"Missing original HTML source position: {logical_id}")
        start = offsets[tag.sourceline - 1] + tag.sourcepos
        span = position_map.get(start)
        if span is None or span.tag != tag.name:
            raise ValueError(f"Cannot locate original HTML span: {logical_id}")
        if span.inner(html) != tag.decode_contents():
            raise ValueError(f"Original HTML span differs from parser: {logical_id}")
        changes.append((span.inner_start, span.inner_end, replacement, logical_id))

    changes.sort(key=lambda x: x[0])
    for preceding, following in zip(changes, changes[1:]):
        if preceding[1] > following[0]:
            raise ValueError(f"Overlapping HTML changes: {preceding[3]}, {following[3]}")
    for begin, end, replacement, _ in reversed(changes):
        html = html[:begin] + replacement + html[end:]
    return html.encode("utf-8")


def rebuild_v2(source_bytes: bytes) -> bytes:
    """Use the original V2 importer and builder to emit the updated V11 HTML.

    All full guide JSON and chapter HTML are temporary private intermediate
    files. A changed element is never allowed to silently alter the outer UI.
    """
    from .build import read_json, render, validate
    from .import_v11 import bootstrap

    with TemporaryDirectory(prefix="wow-v11-update-") as temporary:
        workspace = Path(temporary)
        private_source = workspace / "private-input.html"
        private_source.write_bytes(source_bytes)
        bootstrap(private_source, destination_root=workspace)
        registry = read_json(workspace / "content" / "registry.json")
        page, guides = render(registry, root=workspace)
        errors = validate(registry, guides, page)
        if errors:
            raise ValueError("V2 HTML validation failed: " + "; ".join(errors))
        rebuilt = page.encode("utf-8")
        if rebuilt != source_bytes:
            raise ValueError("V2 HTML reconstruction changed non-target bytes")
    return rebuilt


def write_private_patch(source_path: Path, patch_path: Path, output_path: Path,
                        *, public_base: Path = BASE) -> dict:
    out = Path(output_path).resolve()
    if out == ROOT.resolve() or out.is_relative_to(ROOT.resolve()):
        raise ValueError("Refusing to write private V11 HTML into the GitHub repository")
    if out.is_relative_to(Path(public_base).resolve()):
        raise ValueError("Refusing to write private V11 HTML to the public data directory")
    if out == Path(source_path).resolve():
        raise ValueError("Refusing to overwrite the original V11 source HTML")
    patch = json.loads(Path(patch_path).read_text(encoding="utf-8"))
    result = rebuild_v2(apply_patch(source_path, patch, public_base))
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite output: {out}")
    out.write_bytes(result)
    return {
        "status": "PASS",
        "updated_items": len(patch["updates"]),
        "baseline_sha256": patch["baseline_v11_sha256"],
        "output_sha256": hashlib.sha256(result).hexdigest(),
        "source_overwritten": False,
        "public_repository_updated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch exact V11 HTML spans with private edits")
    parser.add_argument("source", type=Path)
    parser.add_argument("patch", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = write_private_patch(args.source, args.patch, args.output)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
