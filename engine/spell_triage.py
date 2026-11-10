"""Deterministic review queue for the 2026-11-10 Blizzard ko_KR observations.

API 404 != an invalid spell ID. Matching names != verified gameplay logic.
The queue must not mutate canonical names, approve rules, or publish a guide.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from .public_data import BASE, load, validate

EVIDENCE = Path(__file__).resolve().parents[1] / "content" / "review" / "blizzard-spell-20261110.json"
AUDIT_SCHEMA = "ko-kr-live-comparison-v1"
QUEUE_SCHEMA = "spell-review-queue-v1"
STATUSES = ("name_mismatch", "game_data_api_404")


def read_evidence(path: Path = EVIDENCE) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise ValueError("Audit evidence must be an object")
    return doc


def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def analyze(base: Path = BASE, evidence: dict | None = None) -> dict:
    checked = validate(base)
    if not checked["ok"]:
        raise ValueError("Invalid public catalog: " + "; ".join(checked["errors"]))
    doc = read_evidence() if evidence is None else evidence
    if not isinstance(doc, dict) or doc.get("schema_version") != AUDIT_SCHEMA:
        raise ValueError("Unknown live evidence format")
    if any(doc.get(key) != expected for key,expected in (
        ("region", "kr"), ("locale", "ko_KR"), ("namespace", "static-kr"),
        ("automatic_publish_allowed", False),
        ("all_rules_review", "pending")
    )):
        raise ValueError("Untrusted provenance or unsupported publication state")
    raw = (base / "spells.json").read_bytes()
    if git_blob_sha1(raw) != doc.get("baseline_spells_git_blob_sha"):
        raise ValueError("Baseline spell dictionary changed since evidence capture")
    manifest, spell_doc, guides = load(base)
    spell_records = spell_doc["spells"]
    known = {s["spell_id"] for s in spell_records}
    if len(spell_records) != doc.get("baseline_name_records"):
        raise ValueError("Raw spell record count differs from evidence")
    if len(known) != doc.get("total_requested_spell_ids"):
        raise ValueError("Unique spell-ID count differs from evidence")

    matched = doc.get("observations_matched_existing_name_ids")
    not_found = doc.get("observations_not_found_ids")
    mismatches = doc.get("observations_mismatched_names")
    other = doc.get("observations_other_error_ids")
    if (not isinstance(matched, list) or not isinstance(not_found, list) or
            not isinstance(mismatches, list) or not isinstance(other, list)):
        raise ValueError("Incomplete observation categories")
    if any(type(sid) is not int for sid in matched + not_found + other):
        raise ValueError("Non-integer spell ID in evidence")
    if any(not isinstance(r, dict) or type(r.get("spell_id")) is not int
           for r in mismatches):
        raise ValueError("Malformed mismatched name evidence")
    mismatch_ids = [r["spell_id"] for r in mismatches]
    classified = matched + not_found + other + mismatch_ids
    if len(classified) != len(known) or len(set(classified)) != len(known) or set(classified) != known:
        raise ValueError("Audit does not partition all baseline spell IDs exactly once")

    inherited_names: dict[int, set[str]] = {}
    for s in spell_records:
        inherited_names.setdefault(s["spell_id"], set()).add(s["name_ko"])
    for r in mismatches:
        if r.get("review") != "pending" or r.get("inherited_name_ko") not in inherited_names[r["spell_id"]]:
            raise ValueError("Mismatched name lacks unchanged inherited evidence")
        if not isinstance(r.get("observed_name_ko"), str) or not r["observed_name_ko"]:
            raise ValueError("Mismatched name has no observed label")
        if r["observed_name_ko"] in inherited_names[r["spell_id"]]:
            raise ValueError("Evidence flagged a matching name as mismatched")

    usage: dict[int, list[dict]] = {}
    for g in guides:
        for group in g["rotation_groups"]:
            for row in group["rules"]:
                sid = row["action"]["spell_id"]
                if sid is None:
                    continue
                usage.setdefault(sid, []).append({
                    "guide_id": g["guide_id"],
                    "rule_id": row["id"],
                    "group_id": group["id"],
                    "v11_fragment_sha256": row["provenance"]["v11_fragment_sha256"],
                })

    mismatch_by_id = {r["spell_id"]: r for r in mismatches}
    records = []
    for sid in sorted(set(not_found) | set(mismatch_ids)):
        status = "name_mismatch" if sid in mismatch_by_id else "game_data_api_404"
        hit = usage.get(sid, [])
        priority = ("P0_rotation_reference" if hit else
                    "P1_name_disagreement" if status == "name_mismatch" else
                    "P2_glossary_only_404")
        spell_rows = [r for r in spell_records if r["spell_id"] == sid]
        inherited = sorted(inherited_names[sid])
        record = {
            "spell_id": sid,
            "status": status,
            "triage_priority": priority,
            "inherited_names_ko": inherited,
            "observed_name_ko": mismatch_by_id[sid]["observed_name_ko"] if status == "name_mismatch" else None,
            "priority_rule_count": len(hit),
            "affected_priority_rules": sorted(hit, key=lambda x: x["rule_id"]),
            "glossary_only": not bool(hit),
            "inherited_english_metadata_may_include_commentary": any(
                "  " in r.get("name_en", "") or len(r.get("name_en", "")) > 85 for r in spell_rows
            ),
            "review": "pending_client_or_secondary_evidence",
            "client_verified": False,
            "automatic_name_correction_allowed": False,
            "automatic_publish_allowed": False,
        }
        records.append(record)
    records.sort(key=lambda x: ({"P0_rotation_reference":0,"P1_name_disagreement":1,
                                "P2_glossary_only_404":2}[x["triage_priority"]],x["spell_id"]))
    priorities = Counter(r["triage_priority"] for r in records)
    return {
        "schema_version": QUEUE_SCHEMA,
        "baseline": manifest["baseline"],
        "source_observation_run_url": doc.get("workflow_run_url"),
        "source_snapshot_sha256": doc.get("original_snapshot_sha256"),
        "evidence_categories_complete": True,
        "summary": {
            "unique_spell_ids": len(known),
            "raw_name_records": len(spell_records),
            "api_name_matches": len(matched),
            "api_name_mismatches": len(mismatch_ids),
            "api_404": len(not_found),
            "other_errors": len(other),
            "review_queue_ids": len(records),
            "priority_rotation_spell_ids": priorities["P0_rotation_reference"],
            "affected_priority_rows": sum(r["priority_rule_count"] for r in records),
            "glossary_only_review_ids": sum(r["glossary_only"] for r in records),
            "review_unresolved": len(records),
            "verified_by_client": 0,
        },
        "records": records,
        "automatic_publish_allowed": False,
        "disclaimer": "API gaps and mismatches require further evidence; no gameplay rules or names are approved.",
    }


def main() -> int:
    p=argparse.ArgumentParser(description="Prioritize observed ko_KR name gaps without approval")
    p.add_argument("--output",default="dist/spell-review-queue.json")
    p.add_argument("--require-resolved",action="store_true")
    args=p.parse_args()
    try:
        result=analyze()
        output=Path(args.output)
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
                          encoding="utf-8")
        print(json.dumps(result["summary"],ensure_ascii=False))
        return 1 if args.require_resolved else 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print("Spell triage failed:",str(exc))
        return 1


if __name__=="__main__":
    raise SystemExit(main())
