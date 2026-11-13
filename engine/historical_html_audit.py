"""Exact historical HTML guide/section preservation audit for private artifacts.

Purpose: verify old guides survived a CREATE/UPDATE without requiring uniform
chapter counts or any hard-coded WoW specialization names. All input sources
are trusted, private UTF-8 authored HTML (not unsanitized remote website HTML).

Audit compares raw source slices, not BeautifulSoup reserialization or rendered
screenshots. An allowed section edit cannot hide changes to surrounding guide
markup, other sections, nav labels or data-guide attributes inside that guide.
Global shell/CSS/JS integrity requires additional functional QA.

No source text or private guide names are emitted in its public-safe report.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re

from .v2.html_spans import SpanParser

_HASH = re.compile(r"[0-9a-f]{64}\Z")


def _utf8(source: bytes) -> str:
    if not isinstance(source, bytes):
        raise TypeError("Historical sources must be bytes")
    try:
        return source.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Historical source must be UTF-8") from exc


def _views(source: str) -> dict:
    spans = SpanParser(source).spans
    sections = sorted((s for s in spans if s.tag == "section" and s.attrs.get("id")),
                      key=lambda s: s.start)
    guides = sorted(
        (s for s in spans if s.tag == "div" and
         "manual-view" in (s.attrs.get("class") or "").split() and
         s.attrs.get("data-guide")), key=lambda s: s.start
    )
    if not guides:
        raise ValueError("Private HTML has no manual-view[data-guide] views")
    result = {}
    for view in guides:
        guide_id = view.attrs["data-guide"]
        if guide_id in result:
            raise ValueError("Duplicate guide identity in private source")
        child_sections = [
            s for s in sections if view.start < s.start and s.end < view.end
        ]
        names = [s.attrs["id"] for s in child_sections]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate section ID within guide")
        if any(a.end > b.start for a, b in zip(child_sections, child_sections[1:])):
            raise ValueError("Overlapping section evidence is not supported")
        result[guide_id] = (view, child_sections)
    return result


def _mask_allowed(whole: str, guide, sections, permitted: set[str]) -> str:
    start = guide.start
    content = whole[guide.start:guide.end]
    targets = [s for s in sections if s.attrs["id"] in permitted]
    for sec in sorted(targets, key=lambda s: s.start, reverse=True):
        a, b = sec.start - start, sec.end - start
        # Stable placeholder is keyed by the original section ID, not by prose.
        placeholder = "<REVIEWED-SECTION:" + sec.attrs["id"] + ">"
        content = content[:a] + placeholder + content[b:]
    return content


def compare_historical_html(
    baseline_bytes: bytes, updated_bytes: bytes, *,
    protect_guides: list[str] | None = None,
    allowed_section_changes: dict[str, list[str]] | None = None,
    expected_baseline_sha256: str | None = None,
) -> dict:
    """Read-only check of every protected guide's exact raw authored markup.

    A new guide added to the document does not alter the old guide's content.
    An authorized section can change while all other parts of that guide,
    including siblings and wrapper markup, remain source-identical.
    """
    baseline_hash = sha256(baseline_bytes).hexdigest()
    updated_hash = sha256(updated_bytes).hexdigest()
    if expected_baseline_sha256 is not None:
        if not isinstance(expected_baseline_sha256, str) or not _HASH.fullmatch(expected_baseline_sha256):
            raise ValueError("Expected SHA-256 must be 64 lowercase hex characters")
        if expected_baseline_sha256 != baseline_hash:
            raise ValueError("Historical baseline SHA-256 mismatch")
    baseline = _utf8(baseline_bytes)
    updated = _utf8(updated_bytes)
    old = _views(baseline)
    new = _views(updated)
    if protect_guides is None:
        targets = list(old)
    else:
        if len(protect_guides) != len(set(protect_guides)) or not protect_guides:
            raise ValueError("Protected guide IDs must be unique and nonempty")
        if any(g not in old for g in protect_guides):
            raise ValueError("Requested guide is absent from historical baseline")
        targets = protect_guides
    allow = allowed_section_changes or {}
    if not isinstance(allow, dict):
        raise ValueError("Allowed section changes must be a mapping")
    if any(g not in targets for g in allow):
        raise ValueError("Allowed updates cannot refer to unprotected guide")
    reasons = Counter()
    identical = 0
    allowed_edited = 0
    section_count = 0
    for gid in targets:
        if gid not in new:
            reasons["removed_protected_guide"] += 1
            continue
        before_view, before_sections = old[gid]
        after_view, after_sections = new[gid]
        before_ids = [s.attrs["id"] for s in before_sections]
        after_ids = [s.attrs["id"] for s in after_sections]
        section_count += len(before_ids)
        if before_ids != after_ids:
            reasons["protected_section_inventory_changed"] += 1
            continue
        permitted_list = allow.get(gid, [])
        if not isinstance(permitted_list, list) or len(permitted_list) != len(set(permitted_list)):
            raise ValueError("Allowed section names must be a unique list")
        permitted = set(permitted_list)
        if not permitted.issubset(before_ids):
            raise ValueError("An allowed section does not exist in baseline")
        # First compare exact old/new byte slices with explicitly whitelisted
        # section content masked. This also catches changing intro/footer/UI
        # markup outside all section elements.
        if _mask_allowed(baseline, before_view, before_sections, permitted) != (
            _mask_allowed(updated, after_view, after_sections, permitted)
        ):
            reasons["unexpected_protected_guide_change"] += 1
            continue
        prior_sections = {s.attrs["id"]: s for s in before_sections}
        for after_sec in after_sections:
            ident = after_sec.attrs["id"]
            before_sec = prior_sections[ident]
            if baseline[before_sec.start:before_sec.end] != updated[after_sec.start:after_sec.end]:
                if ident not in permitted:
                    reasons["unexpected_protected_section_change"] += 1
                else:
                    allowed_edited += 1
        if not permitted:
            identical += 1
    result = {
        "schema_version": "historical-guide-preservation-audit-v1",
        "baseline_sha256": baseline_hash,
        "updated_sha256": updated_hash,
        "baseline_guide_count": len(old),
        "updated_guide_count": len(new),
        "protected_guide_count": len(targets),
        "protected_section_count": section_count,
        "unchanged_protected_guides": identical,
        "allowed_section_edits_observed": allowed_edited,
        "added_guide_count": len(set(new) - set(old)),
        "removed_guide_count": len(set(old) - set(new)),
        "failure_categories": dict(sorted(reasons.items())),
        "status": "PASS" if not reasons else "FAIL",
        "content_accuracy_verified": False,
        "functional_ui_verified": False,
        "source_text_in_report": False,
        "automatic_publish_allowed": False,
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--updated", type=Path, required=True)
    parser.add_argument("--expected-baseline-sha256")
    parser.add_argument("--protect-guide", action="append", default=[])
    parser.add_argument("--allow-section-change", action="append", default=[],
                        help="guide_id:section_id exact whitelist, repeatable")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    allowed = {}
    for entry in args.allow_section_change:
        if ":" not in entry:
            parser.error("Allowed changes must use guide_id:section_id")
        guide, section = entry.split(":", 1)
        if not guide or not section:
            parser.error("Allowed changes must specify both guide and section")
        allowed.setdefault(guide, []).append(section)
    result = compare_historical_html(
        args.baseline.read_bytes(), args.updated.read_bytes(),
        expected_baseline_sha256=args.expected_baseline_sha256,
        protect_guides=args.protect_guide or None,
        allowed_section_changes=allowed,
    )
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
