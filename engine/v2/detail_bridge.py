"""Recover V11 detail text by joining exact source hashes to public rule IDs.

The original V11 HTML is private. Detailed text and HTML fragments are written
ONLY outside the GitHub working tree. The public compact index remains unchanged.
This does not certify gameplay correctness or external Wowhead source meaning.

Usage:
  python -m engine.v2.detail_bridge PRIVATE_V11.html --output-dir /private/v11-details
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from bs4 import BeautifulSoup, Tag

from .build import ROOT
from ..public_data import BASE, load, validate


GROUP = re.compile(r"^([^:]+):([^:]+):table-([1-9][0-9]*)$")


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _advanced_items(section: Tag) -> list[Tag]:
    """Match the ordering contract of engine.v2.rules.extract_guide."""
    results = []
    for child in section.find_all(recursive=False):
        if child.name in ("h3", "h4"):
            continue
        if child.name in ("header", "div") and "chapter-heading" in (
            child.get("class") or []
        ):
            continue
        if child.name in ("p", "aside"):
            chunks = [child]
        elif child.name in ("ul", "ol"):
            chunks = child.find_all("li", recursive=False)
        elif child.name == "div" and child.find("table"):
            chunks = child.select("tbody tr")
        else:
            continue
        results.extend(item for item in chunks if item.get_text(" ", strip=True))
    return results


def _section(guide: Tag, section_id: str) -> Tag:
    # IDs are data-derived from the public manifest, not arbitrary CSS selectors.
    found = [s for s in guide.find_all("section", id=True)
             if s.get("id") == section_id]
    if len(found) != 1:
        raise ValueError(f"Expected exactly one V11 section: {section_id}")
    return found[0]


def extract_details(source: Path, public_base: Path = BASE,
                    expected_sha256: str | None = None) -> dict:
    """Recover private text/markup only if every canonical public hash matches."""
    original = Path(source).read_bytes()
    baseline = hashlib.sha256(original).hexdigest()
    if expected_sha256 and baseline != expected_sha256:
        raise ValueError(f"V11 baseline mismatch: {baseline}")
    valid = validate(public_base)
    if not valid["ok"]:
        raise ValueError("Invalid public index: " + "; ".join(valid["errors"]))
    manifest, _, public_guides = load(public_base)
    soup = BeautifulSoup(original.decode("utf-8"), "html.parser")
    actual = soup.select("div.manual-view[data-guide]")
    if len(actual) != len(public_guides):
        raise ValueError("V11/public guide count mismatch")
    source_guides = {g["data-guide"]: g for g in actual}
    if len(source_guides) != len(actual):
        raise ValueError("Duplicate V11 guide ID")
    output = []
    for entry, public in zip(manifest["guides"], public_guides):
        gid = entry["id"]
        if public["guide_id"] != gid or gid not in source_guides:
            raise ValueError(f"Guide identity mismatch: {gid}")
        if public["baseline_v11_sha256"] != baseline:
            raise ValueError(f"Public V11 baseline mismatch for {gid}")
        src = source_guides[gid]
        rule_groups = []
        for group in public["rotation_groups"]:
            found = GROUP.fullmatch(group["id"])
            if not found or (found[1], found[2]) != (gid, group["source_section"]):
                raise ValueError(f"Unsupported group identity: {group['id']}")
            section = _section(src, found[2])
            tables = [
                t for t in section.find_all("table")
                if t.select_one("thead th")
                and t.select_one("thead th").get_text(" ", strip=True) == "순위"
            ]
            table_number = int(found[3])
            if table_number > len(tables):
                raise ValueError(f"Missing priority table: {group['id']}")
            rows = tables[table_number - 1].select("tbody tr")
            if len(rows) != len(group["rules"]):
                raise ValueError(f"Priority row count mismatch: {group['id']}")
            extracted_rules = []
            for ordinal, (row, rule) in enumerate(zip(rows, group["rules"]), 1):
                expected_id = f"{group['id']}:row-{ordinal}"
                if rule["id"] != expected_id or rule["order"] != ordinal:
                    raise ValueError(f"Public rule order mismatch: {expected_id}")
                cells = row.find_all(["td", "th"], recursive=False)
                if len(cells) < 3:
                    raise ValueError(f"Missing V11 condition cell: {rule['id']}")
                evidence_text = " | ".join(
                    cell.get_text(" ", strip=True) for cell in cells
                )
                if digest(evidence_text) != rule["provenance"]["v11_fragment_sha256"]:
                    raise ValueError(f"V11 rule hash mismatch: {rule['id']}")
                extracted_rules.append({
                    "id": rule["id"],
                    "condition_text_ko": cells[2].get_text(" ", strip=True),
                    "condition_html": cells[2].decode_contents(),
                    "action_text_ko": cells[1].get_text(" ", strip=True),
                    "source_fragment_sha256": digest(evidence_text),
                    "source_locator": rule["provenance"]["locator"],
                })
            rule_groups.append({"id": group["id"], "rules": extracted_rules})

        indexed_tips = public["advanced_guidance_index"]
        sections = [sec for sec in src.find_all("section", id=True)
                    if "advanced" in sec["id"]]
        tip_nodes = []
        for sec in sections:
            tip_nodes.extend((sec["id"], node) for node in _advanced_items(sec))
        if len(tip_nodes) != len(indexed_tips):
            raise ValueError(f"Advanced tip count mismatch: {gid}")
        tips = []
        for index, (public_tip, (section_id, node)) in enumerate(
            zip(indexed_tips, tip_nodes), 1
        ):
            tip_id = f"{gid}:{section_id}:tip-{index}"
            if public_tip["id"] != tip_id:
                raise ValueError(f"Advanced tip identity mismatch: {tip_id}")
            body = node.get_text(" ", strip=True)
            if digest(body) != public_tip["provenance"]["v11_fragment_sha256"]:
                raise ValueError(f"V11 advanced tip hash mismatch: {tip_id}")
            tips.append({
                "id": tip_id,
                "topic": public_tip["topic"],
                "text_ko": body,
                "html": str(node),
                "source_fragment_sha256": digest(body),
                "source_locator": public_tip["provenance"]["locator"],
            })
        output.append({
            "schema_version": "v11-private-detail-v1",
            "guide_id": gid,
            "baseline_v11_sha256": baseline,
            "public_storage_allowed": False,
            "rotation_groups": rule_groups,
            "advanced_guidance": tips,
        })
    return {
        "baseline_v11_sha256": baseline,
        "guides": output,
        "counts": {
            "specs": len(output),
            "groups": sum(len(x["rotation_groups"]) for x in output),
            "rows": sum(len(g["rules"]) for x in output for g in x["rotation_groups"]),
            "tips": sum(len(x["advanced_guidance"]) for x in output),
        },
    }


def export_private(source: Path, output_dir: Path, *,
                   public_base: Path = BASE, expected_sha256: str | None = None
                   ) -> dict:
    """Write private per-spec detail files; refuse any destination inside repo."""
    dst = Path(output_dir).resolve()
    if dst == ROOT.resolve() or dst.is_relative_to(ROOT.resolve()):
        raise ValueError("Refusing to write full V11 details into the GitHub repository")
    if dst.is_relative_to(Path(public_base).resolve()):
        raise ValueError("Refusing to write V11 details into the public dataset")
    extracted = extract_details(source, public_base, expected_sha256)
    dst.mkdir(parents=True, exist_ok=True)
    for guide in extracted["guides"]:
        path = dst / (guide["guide_id"] + ".json")
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite private detail: {path}")
        path.write_text(
            json.dumps(guide, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return extracted["counts"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract private V11 detail JSON")
    parser.add_argument("source", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--baseline-manifest", type=Path,
                        default=ROOT / "docs" / "v2-origin-manifest.json")
    args = parser.parse_args()
    manifest = json.loads(args.baseline_manifest.read_text(encoding="utf-8"))
    counts = export_private(
        args.source, args.output_dir,
        expected_sha256=manifest["v11_baseline_sha256"],
    )
    print(json.dumps({"status": "PASS", "counts": counts,
                      "private_output_only": True}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
