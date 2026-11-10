"""Source-section traceability audit for Arcane V11 CREATE priority rules.

This validates metadata rigor and FAILS CLOSED if any current priority row
lacks source-section mapping. It does not fetch external pages or claim that
pointing to a guide proves its condition. Only independent human review can
upgrade a row beyond the source-section mapping stage.
"""
from __future__ import annotations

from collections import Counter
from urllib.parse import urlsplit

ALLOWED = {
    "aligned", "needs_refinement", "source_variation",
    "conditional_talent", "fallback_only",
}
DOMAINS = {"www.wowhead.com", "www.icy-veins.com", "www.method.gg"}
COLUMNS = {
    "source_section_refs", "source_alignment", "review_focus",
    "source_section_mapped", "full_condition_verified", "gameplay_approved",
}


def audit_rule_sources(draft: dict, audit: dict) -> dict:
    if not isinstance(draft, dict) or not isinstance(audit, dict):
        raise ValueError("Arcane source audit requires draft and evidence objects")
    if (audit.get("schema_version") != "v11-rule-source-audit-v1"
            or audit.get("guide_id") != draft.get("id")
            or audit.get("patch") != draft.get("patch")):
        raise ValueError("Arcane evidence schema, guide or patch mismatch")
    policy = audit.get("policy", {})
    required_policy = (
        "source_section_pointer_is_not_exact_quote_evidence",
        "source_alignment_is_not_gameplay_approval",
        "full_condition_verification_requires_manual_review",
    )
    if not all(policy.get(name) is True for name in required_policy):
        raise ValueError("Source locations must never masquerade as verified facts")
    if (policy.get("original_guide_text_embedded") is not False
            or policy.get("publication_allowed") is not False):
        raise ValueError("Source audit cannot embed guide text or authorize publication")
    catalog = audit.get("source_catalog")
    if not isinstance(catalog, dict) or set(catalog) != {"wowhead", "icyveins", "method"}:
        raise ValueError("Expected three canonical independent guide sources")
    for source_id, source in catalog.items():
        if not isinstance(source, dict) or set(source) != {"url", "updated", "patch", "sections"}:
            raise ValueError("Source catalog entry malformed")
        url = urlsplit(source["url"])
        if (url.scheme != "https" or url.hostname not in DOMAINS
                or url.username is not None or url.password is not None):
            raise ValueError("Source requires approved HTTPS guide URL")
        if source["patch"] != draft["patch"]:
            raise ValueError("Source patch/version mismatch")
        if not isinstance(source["sections"], dict) or not source["sections"]:
            raise ValueError("Source must contain named, human-checkable sections")

    rows = {
        item["id"]: item
        for group in draft["rotation_groups"] for item in group["rows"]
    }
    if len(rows) != sum(len(g["rows"]) for g in draft["rotation_groups"]):
        raise ValueError("Duplicate Arcane priority IDs")
    records = audit.get("records")
    if not isinstance(records, dict) or set(records) != set(rows):
        missing = set(rows).difference(records if isinstance(records, dict) else {})
        extra = set(records or {}).difference(rows) if isinstance(records, dict) else set()
        raise ValueError("Missing/stale source mapping: " + repr({
            "missing": sorted(missing), "extra": sorted(extra),
        }))
    levels = Counter()
    for row_id, rec in records.items():
        if not isinstance(rec, dict) or set(rec) != COLUMNS:
            raise ValueError("Malformed rule evidence record: " + row_id)
        assessment = rec["source_alignment"]
        if assessment not in ALLOWED:
            raise ValueError("Unknown source alignment status: " + row_id)
        if (rec["source_section_mapped"] is not True
                or rec["full_condition_verified"] is not False
                or rec["gameplay_approved"] is not False):
            raise ValueError("Cannot silently approve a source-mapped rule")
        if not isinstance(rec["review_focus"], str) or len(rec["review_focus"].strip()) < 12:
            raise ValueError("Missing specific review focus: " + row_id)
        if not isinstance(rec["source_section_refs"], list) or not rec["source_section_refs"]:
            raise ValueError("Rule must have source-section locations: " + row_id)
        for pointer in rec["source_section_refs"]:
            if not isinstance(pointer, str) or pointer.count(":") != 1:
                raise ValueError("Malformed evidence pointer: " + row_id)
            source_id, section_id = pointer.split(":")
            if section_id not in catalog.get(source_id, {}).get("sections", {}):
                raise ValueError("Unknown source-section reference: " + pointer)
        if assessment == "source_variation" and len(set(rec["source_section_refs"])) < 2:
            raise ValueError("Source variation needs two section references")
        levels[assessment] += 1
    for block in ("cross_source_issues", "scope_gaps"):
        value = audit.get(block)
        if not isinstance(value, list) or not value:
            raise ValueError("Source audit must preserve open concerns: " + block)
    return {
        "status": "SOURCE_LOCATIONS_MAPPED_REVIEW_REQUIRED",
        "guide_id": draft["id"],
        "patch": draft["patch"],
        "source_sections_mapped": len(records),
        "total_rules": len(rows),
        "alignment_counts": dict(sorted(levels.items())),
        "verified_rule_conditions": 0,
        "gameplay_approved_rules": 0,
        "safe_to_publish": False,
    }
