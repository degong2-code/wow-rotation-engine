"""Source-linked rule-condition candidate worklist, NOT a rotation solver.

A parsed fragment (even a syntactically complete AST) does not establish all
requirements for using an ability. Candidate evaluation is diagnostic only.
No candidate from this module can be promoted or auto-published.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re

from .conditions import evaluate
from .public_data import BASE, load, validate as validate_public

SCHEMA = "condition-candidates-v1"
DEFAULT = Path(__file__).resolve().parents[1] / "content" / "review" / "condition-candidates.json"
HEX = re.compile(r"^[0-9a-f]{64}$")
CORE_FIELDS = {"hero", "target_count", "combo_points", "combo_point_cap", "phase", "combat_mode"}
PREFIXES = ("buff:", "debuff:", "ready:", "talent:")
OPS = {"eq", "ne", "gte", "lte"}


def load_overlay(path: Path = DEFAULT) -> dict:
    result = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ValueError("Condition overlay must be a JSON object")
    return result


def original_rows(base: Path = BASE) -> dict[str, dict]:
    result = validate_public(base)
    if not result["ok"]:
        raise ValueError("Public dataset invalid: " + "; ".join(result["errors"]))
    _manifest, _spells, guides = load(base)
    rows = {}
    for guide in guides:
        for group in guide["rotation_groups"]:
            for rule in group["rules"]:
                key = rule["id"]
                if key in rows:
                    raise ValueError("Duplicate original rule id: " + key)
                rows[key] = {
                    "guide_id": guide["guide_id"],
                    "group_id": group["id"],
                    "scenario": group["scenario"],
                    "order": rule["order"],
                    "spell_id": rule["action"]["spell_id"],
                    "name_ko": rule["action"]["name_ko"],
                    "fragment_sha256": rule["provenance"]["v11_fragment_sha256"],
                    "review": rule["review"],
                    "original_condition_state": rule["condition"]["state"],
                    "partial_predicates": rule["condition"]["machine_predicates"],
                }
    return rows


def _field(name: str) -> None:
    if not isinstance(name, str) or not name or len(name) > 128:
        raise ValueError("Condition field must be a bounded string")
    if name in CORE_FIELDS:
        return
    if any(name.startswith(prefix) and len(name) > len(prefix) and
           re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", name[len(prefix):])
           for prefix in PREFIXES):
        return
    raise ValueError(f"Unsupported condition field: {name}")


def validate_ast(node, *, depth: int = 0) -> int:
    """Reject unknown operators, empty branches and unbounded expressions."""
    if depth > 8 or not isinstance(node, dict):
        raise ValueError("Malformed or excessively nested condition AST")
    keys = set(node)
    logical = keys & {"all", "any", "not"}
    if logical:
        if len(logical) != 1 or len(keys) != 1:
            raise ValueError("Logical AST node cannot contain extra properties")
        op = next(iter(logical))
        if op == "not":
            return 1 + validate_ast(node["not"], depth=depth + 1)
        children = node[op]
        if not isinstance(children, list) or not 1 <= len(children) <= 16:
            raise ValueError(f"{op} must be a nonempty bounded list")
        count = 1 + sum(validate_ast(child, depth=depth+1) for child in children)
        if count > 64:
            raise ValueError("Condition AST too large")
        return count
    if keys not in ({"field", "op", "value"}, {"field", "op", "rhs_field"}):
        raise ValueError("Unexpected leaf AST properties")
    _field(node["field"])
    if node["op"] not in OPS:
        raise ValueError("Unsupported comparison")
    if "rhs_field" in node:
        _field(node["rhs_field"])
    else:
        value = node["value"]
        if not isinstance(value, (bool, int, float, str)) or len(str(value)) > 128:
            raise ValueError("Unsafe literal")
        if node["op"] in {"gte", "lte"} and type(value) not in (int, float):
            raise ValueError("Ordering literal must be numeric")
    # Evaluate with no context so all variable references resolve as unknown.
    # This only tests syntax/operand compatibility; never proves source semantics.
    evaluate(node, {})
    return 1


def validate_overlay(doc: dict, base: Path = BASE) -> list[str]:
    errors = []
    if not isinstance(doc, dict):
        return ["Expected JSON object"]
    if doc.get("schema_version") != SCHEMA or doc.get("baseline") != "V11":
        errors.append("Wrong condition overlay schema/baseline")
    rows = original_rows(base)
    proposals = doc.get("proposals")
    if not isinstance(proposals, list):
        return errors + ["proposals must be a list"]
    seen = set()
    for pos, item in enumerate(proposals):
        if not isinstance(item, dict):
            errors.append(f"proposal {pos}: expected object")
            continue
        rid = item.get("rule_id")
        if not isinstance(rid, str) or rid not in rows or rid in seen:
            errors.append(f"proposal {pos}: unknown or duplicate rule_id")
            continue
        seen.add(rid)
        row = rows[rid]
        if item.get("guide_id") != row["guide_id"]:
            errors.append(f"{rid}: mismatched guide")
        if item.get("source_fragment_sha256") != row["fragment_sha256"]:
            errors.append(f"{rid}: original source fragment changed")
        if item.get("spell_id") != row["spell_id"]:
            errors.append(f"{rid}: referenced spell changed")
        if item.get("completeness") != "partial":
            errors.append(f"{rid}: only explicitly partial candidates allowed")
        if item.get("source_review") != "pending_external_verification":
            errors.append(f"{rid}: missing source review gate")
        if item.get("review") != "pending" or item.get("automatic_publish_allowed") is not False:
            errors.append(f"{rid}: candidate cannot be approved or published")
        if not isinstance(item.get("interpretation_note"), str) or not item["interpretation_note"].strip():
            errors.append(f"{rid}: interpretation caveat required")
        try:
            validate_ast(item.get("when"))
        except (ValueError, TypeError, AttributeError, KeyError) as exc:
            errors.append(f"{rid}: invalid AST: {exc}")
    return errors


def worklist(base: Path = BASE, overlay: dict | None = None) -> dict:
    original = original_rows(base)
    proposals = load_overlay() if overlay is None else overlay
    errors = validate_overlay(proposals, base)
    if errors:
        raise ValueError("; ".join(errors))
    by_id = {p["rule_id"]: p for p in proposals["proposals"]}
    entries = []
    counts = Counter()
    for rule_id, row in sorted(original.items(), key=lambda x: (
        x[1]["guide_id"], x[1]["group_id"], x[1]["order"])):
        state = "partial_candidate_pending" if rule_id in by_id else "not_formalized"
        counts[state] += 1
        entries.append({
            "rule_id": rule_id,
            "guide_id": row["guide_id"],
            "group_id": row["group_id"],
            "scenario": row["scenario"],
            "spell_id": row["spell_id"],
            "source_fragment_sha256": row["fragment_sha256"],
            "condition_work_state": state,
            "source_verified": False,
            "can_execute_rotation": False,
            "automatic_publish_allowed": False,
        })
    return {
        "schema_version": "condition-worklist-v1",
        "baseline": "V11",
        "summary": {
            "total_rows": len(entries),
            "partial_candidate_pending": counts["partial_candidate_pending"],
            "not_formalized": counts["not_formalized"],
            "approved_full_conditions": 0,
            "publish_ready": False,
        },
        "entries": entries,
        "disclaimer": "Partial syntax never suffices to select a spell or claim optimal gameplay.",
    }


def diagnose(rule_id: str, context: dict, overlay: dict | None = None, base: Path = BASE) -> dict:
    doc = load_overlay() if overlay is None else overlay
    errors = validate_overlay(doc, base)
    if errors:
        raise ValueError("; ".join(errors))
    proposals = {p["rule_id"]: p for p in doc["proposals"]}
    if rule_id not in original_rows(base):
        raise ValueError("Unknown source rule id")
    prop = proposals.get(rule_id)
    result = {
        "rule_id": rule_id, "candidate_found": prop is not None,
        "syntactic_predicate_result": None,
        "rotation_applicability": None,
        "can_recommend_ability": False,
        "source_verified": False,
    }
    if prop is not None:
        result["syntactic_predicate_result"] = evaluate(prop["when"], context)
    return result


def main() -> int:
    p = argparse.ArgumentParser(description="Fail-closed condition candidate review worklist")
    p.add_argument("--output", default="dist/condition-worklist.json")
    p.add_argument("--require-ready", action="store_true")
    p.add_argument("--diagnose-rule-id")
    p.add_argument("--context")
    args = p.parse_args()
    try:
        if args.diagnose_rule_id:
            context = json.loads(Path(args.context).read_text(encoding="utf8")) if args.context else {}
            result = diagnose(args.diagnose_rule_id, context)
        else:
            result = worklist()
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True,
                                  indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result.get("summary", result), ensure_ascii=False)
              if args.diagnose_rule_id else json.dumps(result["summary"], ensure_ascii=False))
        if args.require_ready:
            # A separate evidence-verified approval system must be built
            # before any true publishing capability can exist.
            return 1
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print("Condition review failed:", str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
