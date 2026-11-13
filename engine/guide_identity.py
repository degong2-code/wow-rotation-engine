"""Fail-closed identity validation and cautious revision hints for acquired guides.

Do not mistake a patch string anywhere inside unrelated JavaScript for a guide
patch verification. Revision/patch hints are descriptive: an external current
season baseline remains an independent editorial decision.
"""
from __future__ import annotations

from datetime import date
from html.parser import HTMLParser
import re

from .source_page_acquire import SourceAccessError
from .spec_source_resolver import Specialization

_DATE = re.compile(r"(?<!\d)20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}(?!\d)")
_MODIFIED = re.compile(
    r"(?:Updated|업데이트됨)\s*[:：]?\s*(20\d{2}[-/.]\d{1,2}[-/.]\d{1,2})",
    re.I,
)
_PATCH = re.compile(
    r"(?:Patch\s*[:：]?\s*(\d{1,2}\.\d{1,2}\.\d{1,2})"
    r"|(\d{1,2}\.\d{1,2}\.\d{1,2})\s*(?:Patch|패치))",
    re.I,
)


class _VisibleGuideMetadata(HTMLParser):
    """Read markup title, h1, visible text and selected article metadata."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title: list[str] = []
        self.heading: list[str] = []
        self.visible: list[str] = []
        self.meta_modified: list[str] = []
        self._hidden = 0
        self._title = 0
        self._h1 = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {"script", "style", "template", "noscript"}:
            self._hidden += 1
        if tag == "title":
            self._title += 1
        if tag == "h1":
            self._h1 += 1
        if tag == "meta":
            key = (attrs.get("property") or attrs.get("name") or "").lower()
            if key in {"article:modified_time", "date.modified", "last-modified",
                       "modified", "dateModified".lower()} and attrs.get("content"):
                self.meta_modified.append(attrs["content"][:64])

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag in {"script", "style", "template", "noscript"}:
            self._hidden = max(0, self._hidden - 1)
        if tag == "title":
            self._title = max(0, self._title - 1)
        if tag == "h1":
            self._h1 = max(0, self._h1 - 1)

    def handle_data(self, data):
        if self._title and len(self.title) < 100:
            self.title.append(data)
        if self._h1 and not self._hidden and len(self.heading) < 150:
            self.heading.append(data)
        if not self._hidden and not self._title and len(self.visible) < 10000:
            self.visible.append(data)

    def texts(self) -> tuple[str, str, str]:
        return (
            " ".join(" ".join(self.title).split())[:600],
            " ".join(" ".join(self.heading).split())[:600],
            " ".join(" ".join(self.visible).split())[:30000],
        )


def _date(value: str) -> str | None:
    match = _DATE.search(value)
    if not match:
        return None
    try:
        return date.fromisoformat(match.group().replace("/", "-").replace(".", "-")).isoformat()
    except ValueError:
        return None


def inspect_identity(html: str, spec: Specialization,
                     *, expected_patch: str | None = None,
                     min_updated: str | None = None) -> dict:
    parsed = _VisibleGuideMetadata()
    parsed.feed(html)
    title, h1, visible = parsed.texts()
    expected = spec.english_name + " Rotation Guide"
    candidates = [title, h1]
    # Require a proper guide heading, not a random mention of a spec in JS.
    valid = any(re.search(r"(?<![a-z])" + re.escape(expected) + r"(?![a-z])",
                          item, re.I) for item in candidates)
    if not valid:
        raise SourceAccessError("Guide heading does not match requested specialization")
    if title and re.search(r"\bRotation Guide\b", title, re.I) and expected.casefold() not in title.casefold():
        raise SourceAccessError("HTML page title points to a different specialization")

    updated = None
    if parsed.meta_modified:
        updated = next((_date(x) for x in parsed.meta_modified if _date(x)), None)
    if not updated:
        found = _MODIFIED.search(visible)
        updated = _date(found.group(1)) if found else None
    patches = sorted({
        next(x for x in m.groups() if x is not None)
        for m in _PATCH.finditer(visible)
    })
    if expected_patch is not None:
        if not re.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{1,2}", expected_patch):
            raise ValueError("Expected patch must be like 12.1.5")
        if expected_patch not in patches:
            raise SourceAccessError("Requested patch is not evidenced by visible guide metadata")
    if min_updated is not None:
        lower = _date(min_updated)
        if lower is None or lower != min_updated:
            raise ValueError("Expected minimum update date must use ISO YYYY-MM-DD")
        if updated is None or updated < lower:
            raise SourceAccessError("Guide update date is missing or older than required")

    return {
        "guide_identity_matched": True,
        "specialization_key": spec.key,
        "observed_guide_update_date": updated,
        "visible_patch_candidates": patches[:20],
        "expected_patch_visible": expected_patch in patches if expected_patch else None,
        "update_date_requirement_met": updated >= min_updated if min_updated else None,
        # Editorial checks are separate: a page can contain old patch text.
        "current_patch_independently_verified": False,
        "source_content_complete": False,
        "gameplay_meaning_verified": False,
        "automatic_publish_allowed": False,
    }
