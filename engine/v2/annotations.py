"""V11 note markers and explanation table contract for CREATE guides.

Reuse the original V11 note-marker/tip-trigger and floating-tip implementation.
This module does NOT create a new tooltip or script. Notes are explanatory
annotations, NOT independently verified gameplay evidence.
"""
from __future__ import annotations

from html import escape
import re


_ID = re.compile(r"^[a-z0-9][a-z0-9:-]*$")
_ANCHOR = re.compile(r"^arcane-(?:overview|pre|basics|opener|rotation|cooldowns|advanced|practice|glossary)$")
_REVIEW = "needs_manual_gameplay_review"


def validate_notes(draft: dict) -> dict:
    """Validate identifiers, severity, anchor safety, and allowed placements."""
    annotations = draft.get("editorial", {}).get("annotations")
    if not isinstance(annotations, dict) or set(annotations) != {"schema_version", "notes"}:
        raise ValueError("V11 annotation contract missing or malformed")
    if annotations["schema_version"] != "v11-notes-v1":
        raise ValueError("Unknown V11 annotation schema")
    notes = annotations["notes"]
    if not isinstance(notes, list) or not 4 <= len(notes) <= 24:
        raise ValueError("Expected 4-24 review-gated V11 note annotations")
    rules = {
        r["id"] for group in draft["rotation_groups"] for r in group["rows"]
    }
    mechanics = {
        item["id"] for key in ("flows", "comparisons")
        for item in draft["editorial"]["mechanics"][key]
    }
    seen_ids, seen_targets, count = set(), set(), {"?": 0, "!": 0}
    by_target = {}
    for note in notes:
        required = {
            "id", "target_type", "target_id", "marker", "title",
            "body", "detail_anchor", "review"
        }
        if not isinstance(note, dict) or set(note) != required:
            raise ValueError("Malformed V11 note fields")
        if not isinstance(note["id"], str) or not _ID.fullmatch(note["id"]):
            raise ValueError("Unsafe or missing note ID")
        if note["id"] in seen_ids:
            raise ValueError("Duplicate V11 note ID")
        seen_ids.add(note["id"])
        kind, target_id = note["target_type"], note["target_id"]
        if kind not in ("rule", "mechanic") or not isinstance(target_id, str):
            raise ValueError("Unrecognized V11 note target")
        if target_id not in (rules if kind == "rule" else mechanics):
            raise ValueError("V11 note must point to an existing rule/mechanism")
        if (kind, target_id) in seen_targets:
            raise ValueError("Duplicate V11 note target")
        seen_targets.add((kind, target_id))
        if note["marker"] not in count:
            raise ValueError("V11 notes use ? or ! markers only")
        if note["review"] != _REVIEW:
            raise ValueError("Note cannot be approved without source review")
        for field, limit in (("title", 85), ("body", 600)):
            val = note[field]
            if not isinstance(val, str) or not 8 <= len(val.strip()) <= limit:
                raise ValueError("Note must have concise, meaningful " + field)
        if not isinstance(note["detail_anchor"], str) or not _ANCHOR.fullmatch(note["detail_anchor"]):
            raise ValueError("Unsafe/missing in-document V11 detail anchor")
        if note["marker"] == "!" and not any(
            word in note["body"] for word in
            ("주의", "예외", "혼동", "검토", "선택", "확인", "미보유", "아니")
        ):
            raise ValueError("Critical marker must explain a concrete caution")
        count[note["marker"]] += 1
        by_target[(kind, target_id)] = note
    if count["?"] < 2 or count["!"] < 2:
        raise ValueError("Need both detailed ? explanations and critical ! cautions")
    if not any(x["target_type"] == "mechanic" for x in notes):
        raise ValueError("Mechanism comparison/flow note required")
    return by_target


def render_note(note: dict) -> str:
    """Exact original V11 trigger class/attributes; its JS owns tooltip behavior."""
    marker = note["marker"]
    classes = "note-marker tip-trigger" + (" critical" if marker == "!" else "")
    title = escape(note["title"], quote=True)
    body = escape(note["body"], quote=True)
    identity = escape(note["id"], quote=True)
    href = escape(note["detail_anchor"], quote=True)
    return (
        '<button type="button" class="' + classes
        + '" data-note="' + identity + '" data-hint-title="' + title
        + '" data-hint-body="' + body + '" data-hint-href="#' + href
        + '" aria-label="' + title + ' 관련 설명">' + marker + '</button>'
    )


def render_legend() -> str:
    """Use existing V11 note-key visual language; avoid additional custom CSS."""
    return (
        '<p class="tiny-rule">'
        '<span class="note-key">?</span> 상세 판단 설명 · '
        '<span class="note-key important">!</span> 중요한 예외·검토 주의 · '
        '마우스를 올리면 설명, 클릭하면 설명 고정 · 자세히 읽기로 해당 장 이동'
        '</p>'
    )
