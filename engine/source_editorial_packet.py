"""Private evidence packet: original WHML + exact offsets for editorial review.

This is an index into the *source*, not a rule generator. It never guesses
gameplay state, hero talent defaults or which item is a real action. Long
third-party text must never be committed or published.
"""
from __future__ import annotations

from hashlib import sha256
import re

from .embedded_markup import (
    CALL, TAG, TOOLTIP_BODY, DISPLAY_OPTION, _literal_args, _attrs,
    inspect_embedded_whml,
)
from .source_page_acquire import SourceAccessError

REF = re.compile(r"tooltip\d*", re.I)
HEADING = re.compile(r"h[1-6]", re.I)


def packet_from_html(html: str) -> dict:
    """Preserve every literal guide-body WHML without requiring a browser."""
    parsed = inspect_embedded_whml(html)
    matching = [p for p in parsed["payloads"] if p["target"] == "guide-body"]
    if not matching:
        raise SourceAccessError("No decoded literal guide-body found for editorial packet")

    payloads = []
    for call in CALL.finditer(html):
        args = _literal_args(html, call.end())
        if args is None:
            continue
        body, target = args
        if target != "guide-body":
            continue
        tooltip_defs = []
        for m in TOOLTIP_BODY.finditer(body):
            name = _attrs(m.group(1)).get("name")
            if name:
                tooltip_defs.append({
                    "name": name,
                    "position": m.start(),
                    "body_whml": m.group(2),
                })
        refs, conditionals, headings = [], [], []
        for tag in TAG.finditer(body):
            name = tag.group(1).lower()
            attrs = _attrs(tag.group(2))
            for key, value in attrs.items():
                if REF.fullmatch(key):
                    refs.append({
                        "position": tag.start(),
                        "tag": name,
                        "attribute": key,
                        "definition_name": value,
                    })
            if "display-options" in attrs:
                conditionals.append({
                    "position": tag.start(),
                    "tag": name,
                    "expression": attrs["display-options"],
                })
            if HEADING.fullmatch(name):
                headings.append({"position": tag.start(), "tag": name})
        options = []
        for option in DISPLAY_OPTION.finditer(body):
            ident = next(v for v in option.groups()[:3] if v is not None)
            attrs = _attrs(option.group(4))
            options.append({
                "position": option.start(),
                "id": ident,
                "radio_group": attrs.get("radio", ""),
                "default_checked": bool(re.search(r"(?:^|\s)checked(?:\s|$)",
                                                  option.group(4))),
                "label_whml": option.group(5),
            })
        source_digest = sha256(body.encode("utf-8")).hexdigest()
        payloads.append({
            "target": target,
            "characters": len(body),
            "sha256": source_digest,
            "original_whml": body,
            "tooltip_definitions": tooltip_defs,
            "tooltip_references": refs,
            "conditional_expressions": conditionals,
            "option_definitions": options,
            "heading_positions": headings,
        })

    assert len(payloads) == len(matching)
    return {
        "schema_version": "source-editorial-evidence-private-v1",
        "payloads": payloads,
        "source_text_in_file": True,
        "source_text_may_be_public": False,
        "conditions_interpreted": False,
        "guide_patch_verified": False,
        "gameplay_meaning_verified": False,
        "automatic_publish_allowed": False,
    }
