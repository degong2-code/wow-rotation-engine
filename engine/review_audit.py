"""Fail-closed readiness audit for public WoW rotation metadata.

The report does not attest that a spell name or priority has been verified.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
from .public_data import BASE, load, validate


def audit(base: Path = BASE) -> dict:
    checked = validate(base)
    if not checked["ok"]:
        return {"schema_ok": False, "errors": checked["errors"], "publish_ready": False}
    manifest, spells, guides = load(base)
    conflicts = defaultdict(set)
    for record in spells["spells"]:
        conflicts[str(record["spell_id"])].add(record["name_ko"])
    clashes = {sid: sorted(names) for sid,names in conflicts.items() if len(names) > 1}
    rule_states=Counter()
    tags=Counter()
    nonempty_partial_predicates=0
    for g in guides:
        for group in g["rotation_groups"]:
            for rule in group["rules"]:
                rule_states[rule["condition"]["state"]]+=1
                tags.update(rule["condition"]["semantic_tags"])
                if rule["condition"]["machine_predicates"]:
                    nonempty_partial_predicates+=1
    return {
        "schema_ok": True,
        "baseline": manifest.get("baseline"),
        "summary": {
            "guides": len(guides),
            "rotation_groups": sum(len(g["rotation_groups"]) for g in guides),
            "priority_rows": sum(len(x["rules"]) for g in guides for x in g["rotation_groups"]),
            "uninterpreted_conditions": rule_states.get("needs_manual_interpretation",0),
            "partial_predicate_rows_not_sufficient": nonempty_partial_predicates,
            "advanced_tips_without_full_explanations": sum(len(g["advanced_guidance_index"]) for g in guides),
            "unresolved_rule_spell_ids": sum(r["action"]["spell_id"] is None
                for g in guides for group in g["rotation_groups"] for r in group["rules"]),
            "spell_name_records_unverified": sum(s["review"]=="unverified_inherited_from_v11" for s in spells["spells"]),
            "distinct_spell_ids": len(conflicts),
        },
        "name_conflicts_by_spell_id": clashes,
        "top_semantic_tags": dict(sorted(tags.items())),
        "publish_ready": False,
        "blockers": [
            "All priority-row conditions still require manual interpretation",
            "Official localized spell names have not been independently verified",
            "Advanced Tips retain topic/index only, not complete approved meaning",
            "Source text/semantic equivalence has not been validated in this repository",
        ],
        "disclaimer": "Code/data integrity validation is not a gameplay or source-meaning audit."
    }


def main() -> int:
    p=argparse.ArgumentParser(description="Public rule review readiness")
    p.add_argument("--output",default="dist/review-audit.json")
    p.add_argument("--require-publish-ready",action="store_true")
    args=p.parse_args()
    data=audit()
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"schema_ok":data["schema_ok"],"publish_ready":data["publish_ready"],
                      "counts":data.get("summary",{}),"output":str(out)},ensure_ascii=False))
    return 1 if not data["schema_ok"] or (args.require_publish_ready and not data["publish_ready"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
