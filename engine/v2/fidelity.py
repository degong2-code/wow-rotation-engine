"""V11 editorial and presentation fidelity without copying guide source text.

Reads a private V11 HTML only to count structure; reports counts and class
presence, never content excerpts. A CREATE guide must reuse existing V11
components, provide independent explanation context and remain review-gated.
A structural PASS is not a claim of gameplay correctness.
"""
from __future__ import annotations

from statistics import median
from bs4 import BeautifulSoup

V11_COMPONENTS = (
    "quick-head", "chapter-heading", "chapter-no", "overview-table",
    "steps", "aside", "glossary-list", "glossary-row", "priority",
    "table-scroll", "spell", "tip-trigger", "variant", "hero-switch",
    "sequence", "comparison",
)
REQUIRED_CREATE = V11_COMPONENTS


def structural_metrics(guide):
    sections = guide.select("section[id]")
    per = {}
    for section in sections:
        # Classify by semantic suffix, not by class/spec display name.
        name = section["id"].split("-")[-1]
        per[name] = {
            "characters": len(section.get_text(" ", strip=True)),
            "paragraphs": len(section.select("p")),
            "subheads": len(section.select("h3")),
            "lists": len(section.select("ol, ul")),
            "asides": len(section.select("aside")),
        }
    return {
        "guide_id": guide.get("data-guide", "unknown"),
        "section_count": len(sections),
        "text_characters": len(guide.get_text(" ", strip=True)),
        "sections": per,
        "components": {
            name: len(guide.select("." + name)) for name in V11_COMPONENTS
        },
    }


def baseline_profile(source_html: str) -> dict:
    soup = BeautifulSoup(source_html, "html.parser")
    guides = soup.select("div.manual-view[data-guide]")
    if len(guides) != 7 or len({g["data-guide"] for g in guides}) != 7:
        raise ValueError("Expected exactly the seven canonical V11 guides")
    metrics = [structural_metrics(guide) for guide in guides]
    return {
        "guide_count": len(metrics),
        "median_section_count": median(g["section_count"] for g in metrics),
        "median_text_characters": median(g["text_characters"] for g in metrics),
        "common_components": [
            name for name in V11_COMPONENTS
            if all(g["components"][name] > 0 for g in metrics)
        ],
        "per_guide": metrics,
        "source_text_exported": False,
    }


def audit_create_fragment(fragment_html: str, draft: dict) -> dict:
    soup = BeautifulSoup(fragment_html, "html.parser")
    guides = soup.select("div.manual-view[data-guide]")
    if len(guides) != 1 or guides[0]["data-guide"] != draft["id"]:
        raise ValueError("Expected one newly generated guide")
    guide = guides[0]
    structure = structural_metrics(guide)
    failures = []
    for component in REQUIRED_CREATE:
        if not structure["components"][component]:
            failures.append("missing V11 component: " + component)
    chapters = guide.select("section.chapter[id]")
    if any(not section.select_one(".chapter-heading .chapter-no")
           for section in chapters):
        failures.append("chapter header/number missing")
    if len(guide.select("section.overview")) != 1:
        failures.append("must have one V11 overview section")
    # A complete V11-style guide needs actionable mechanics, not merely text length.
    expected_flows = len(draft["editorial"]["mechanics"]["flows"])
    expected_comparisons = len(draft["editorial"]["mechanics"]["comparisons"])
    if len(guide.select(".mechanic-flow .sequence")) != expected_flows:
        failures.append("actionable mechanics flow count mismatch")
    if len(guide.select(".mechanic-comparison table.comparison")) != expected_comparisons:
        failures.append("hero/condition comparison count mismatch")
    for name in ("overview", "pre", "basics", "opener", "cooldowns", "advanced", "practice"):
        if not guide.select_one("#arcane-" + name + " .spell"):
            failures.append("missing contextual spell links: " + name)
    if not guide.select_one("#arcane-opener ol.steps"):
        failures.append("V11 steps component missing in opener")
    if not guide.select_one("#arcane-rotation p.rule"):
        failures.append("rotation interpretation paragraph missing")
    if not guide.select_one("#arcane-glossary .glossary-list"):
        failures.append("V11 glossary component missing")
    if len(guide.select("#arcane-rotation table.priority")) != len(draft["rotation_groups"]):
        failures.append("rotation group count mismatch")
    if len(guide.select("#arcane-rotation tbody tr")) != sum(
        len(group["rows"]) for group in draft["rotation_groups"]
    ):
        failures.append("priority row count mismatch")
    if len(guide.select("#arcane-advanced [data-tip-id]")) != len(draft["advanced_guidance"]):
        failures.append("advanced item count mismatch")
    if len(guide.select("#arcane-glossary .glossary-row")) != len(draft["spells"]):
        failures.append("glossary row count mismatch")
    if not guide.select("aside.aside.warn"):
        failures.append("V11 review warning component missing")
    chapter_ids = [section["id"] for section in guide.select("section[id]")]
    if len(chapter_ids) != len(set(chapter_ids)):
        failures.append("duplicate chapter ID")

    # Never synthesize facts to satisfy an arbitrary content-length quota.
    total_rows = sum(len(group["rows"]) for group in draft["rotation_groups"])
    evidenced = sum(
        bool(row.get("evidence_refs")) for group in draft["rotation_groups"]
        for row in group["rows"]
    )
    return {
        "status": "PASS" if not failures else "FAIL",
        "structure": structure,
        "reused_v11_components": [
            name for name in REQUIRED_CREATE
            if structure["components"][name] > 0
        ],
        "failures": failures,
        "evidence_coverage": {
            "rows_with_item_evidence": evidenced,
            "total_rows": total_rows,
        },
        "actionable_mechanisms": {
            "flows": expected_flows,
            "comparisons": expected_comparisons,
            "contextual_spell_links": sum(
                len(guide.select("#arcane-" + name + " .spell"))
                for name in ("overview", "pre", "basics", "opener", "cooldowns", "advanced", "practice")
            ),
            "external_evidence_verified": False,
        },
        "editorial_review_required": True,
        "gameplay_accuracy_verified": False,
    }
