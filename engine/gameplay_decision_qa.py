"""Content QA for *editorially annotated* gameplay decisions against private WHML.

This does not infer skills, ranks, numbers or mechanics from WHML. An editor must
ground each candidate action to exact positions in the *same* acquired source.
The evaluator catches inconsistent next-action choices and ambiguous priorities;
it cannot prove an interpretation of the source is correct.

Private input: WHML evidence packet and gameplay annotations may contain
third-party text. Public-safe output: counts, case IDs, codes, never source text.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

SCHEMA = "gameplay-decision-annotations-private-v1"
REPORT = "gameplay-decision-audit-v1"
OPERATORS = {"eq", "neq", "lt", "lte", "gt", "gte"}
KINDS = {"priority", "opener"}
RESULTS = {"matched", "mismatch", "ambiguous", "underdetermined", "no_rule"}
MAX_RULES = 2000
MAX_CASES = 1000


def _valid_name(value: Any, description: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 200:
        raise ValueError(description + " must be a nonempty string, maximum 200 characters")
    return value


def _literal(value: Any) -> bool:
    return isinstance(value, (str, int, float, bool)) and value is not None


def _check_context(context: Any, description: str) -> None:
    if not isinstance(context, dict) or len(context) > 20:
        raise ValueError(description + " must be a bounded object")
    for key, value in context.items():
        _valid_name(key, description + ".key")
        if not _literal(value):
            raise ValueError(description + " values must be literal scalars")


def _check_predicates(predicates: Any) -> None:
    if not isinstance(predicates, list) or len(predicates) > 20:
        raise ValueError("when must be a bounded list")
    for predicate in predicates:
        if not isinstance(predicate, dict) or set(predicate) != {"field", "op", "value"}:
            raise ValueError("A condition requires field/op/value")
        _valid_name(predicate["field"], "condition field")
        if predicate["op"] not in OPERATORS or not _literal(predicate["value"]):
            raise ValueError("Unsupported condition comparison")
        if predicate["op"] not in {"eq", "neq"} and (
            isinstance(predicate["value"], bool) or
            not isinstance(predicate["value"], (int, float))
        ):
            raise ValueError("Numeric comparisons require numeric thresholds")


def _check_source(packet: dict) -> None:
    if packet.get("schema_version") != "source-editorial-evidence-private-v1":
        raise ValueError("Expected original private WHML evidence packet")
    payloads = packet.get("payloads")
    if not isinstance(payloads, list) or not payloads:
        raise ValueError("WHML evidence payloads required")
    from hashlib import sha256
    for payload in payloads:
        body = payload.get("original_whml")
        if not isinstance(body, str) or sha256(body.encode("utf-8")).hexdigest() != payload.get("sha256"):
            raise ValueError("Source WHML missing or digest mismatch")


def _verify_evidence(rule: dict, payloads: list) -> bool:
    evidence = rule.get("evidence")
    if not isinstance(evidence, list) or not evidence or len(evidence) > 20:
        return False
    for ref in evidence:
        if not isinstance(ref, dict) or set(ref) != {"payload_sha256", "start", "end"}:
            return False
        digest, start, end = ref["payload_sha256"], ref["start"], ref["end"]
        hits = [p for p in payloads if p["sha256"] == digest]
        if len(hits) != 1 or type(start) is not int or type(end) is not int:
            return False
        body = hits[0]["original_whml"]
        if start < 0 or end > len(body) or start >= end or not body[start:end].strip():
            return False
    return True


def _equals(a: Any, b: Any) -> bool:
    return type(a) is type(b) and a == b


def _compare(actual: Any, op: str, expected: Any) -> bool | None:
    if op == "eq":
        return _equals(actual, expected)
    if op == "neq":
        return not _equals(actual, expected)
    if isinstance(actual, bool) or not isinstance(actual, (int, float)):
        return None
    if op == "lt":
        return actual < expected
    if op == "lte":
        return actual <= expected
    if op == "gt":
        return actual > expected
    return actual >= expected


def _applicability(rule: dict, case: dict) -> bool | None:
    """True, False or unknown (missing evidence of current combat state)."""
    unknown = False
    for key, value in rule["context"].items():
        if key not in case["context"]:
            unknown = True
        elif not _equals(case["context"][key], value):
            return False
    for condition in rule["when"]:
        field = condition["field"]
        if field not in case["state"]:
            unknown = True
            continue
        result = _compare(case["state"][field], condition["op"], condition["value"])
        if result is False:
            return False
        if result is None:
            unknown = True
    return None if unknown else True


def _identity(rule: dict) -> str:
    conditions = sorted(
        (c["field"], c["op"], json.dumps(c["value"], ensure_ascii=False))
        for c in rule["when"]
    )
    context = sorted((k, json.dumps(v, ensure_ascii=False))
                     for k, v in rule["context"].items())
    return json.dumps([rule["kind"], rule["rank"], rule["step"], context, conditions],
                      ensure_ascii=False)


def _evaluate_case(case: dict, rules: list[dict]) -> dict:
    candidates = [r for r in rules if r["kind"] == case["kind"]]
    certain = []
    uncertain = []
    for rule in candidates:
        status = _applicability(rule, case)
        if status is True:
            certain.append(rule)
        elif status is None:
            uncertain.append(rule)
    selected: list[dict]
    if case["kind"] == "priority":
        rank = min((r["rank"] for r in certain), default=None)
        if any(rank is None or r["rank"] <= rank for r in uncertain):
            return {"id": case["id"], "result": "underdetermined",
                    "competing_rule_count": len(uncertain)}
        if rank is None:
            return {"id": case["id"], "result": "no_rule", "competing_rule_count": 0}
        selected = [r for r in certain if r["rank"] == rank]
    else:
        if uncertain:
            return {"id": case["id"], "result": "underdetermined",
                    "competing_rule_count": len(uncertain)}
        if not certain:
            return {"id": case["id"], "result": "no_rule", "competing_rule_count": 0}
        steps: dict[int, set[str]] = {}
        for r in certain:
            steps.setdefault(r["step"], set()).add(r["action"])
        if any(len(actions) != 1 for actions in steps.values()):
            return {"id": case["id"], "result": "ambiguous",
                    "competing_rule_count": len(certain)}
        if sorted(steps) != list(range(1, max(steps) + 1)):
            return {"id": case["id"], "result": "underdetermined",
                    "competing_rule_count": 0}
        sequence = [next(iter(steps[k])) for k in sorted(steps)]
        return {"id": case["id"], "result": "matched" if sequence == case["expected_actions"]
                else "mismatch", "competing_rule_count": 0}
    actions = {r["action"] for r in selected}
    if len(actions) > 1:
        return {"id": case["id"], "result": "ambiguous",
                "competing_rule_count": len(selected)}
    return {"id": case["id"],
            "result": "matched" if next(iter(actions)) == case["expected_action"] else "mismatch",
            "competing_rule_count": 0}


def assess_annotations(packet: dict, annotations: dict) -> dict:
    """Compare authored rules with evidence and synthetic/editorial combat cases.

    A report with zero detected conflicts is NOT a verification of source
    semantics, patch, untested branches, or live game behavior.
    """
    _check_source(packet)
    if annotations.get("schema_version") != SCHEMA:
        raise ValueError("Unexpected annotation schema")
    rules = annotations.get("rules")
    cases = annotations.get("cases")
    if not isinstance(rules, list) or len(rules) > MAX_RULES:
        raise ValueError("Rules must be a bounded list")
    if not isinstance(cases, list) or len(cases) > MAX_CASES:
        raise ValueError("Cases must be a bounded list")
    ids = set()
    invalid_evidence = []
    duplicate_decisions = []
    seen = {}
    for rule in rules:
        if not isinstance(rule, dict):
            raise ValueError("Every rule must be an object")
        ident = _valid_name(rule.get("id"), "rule id")
        if ident in ids:
            raise ValueError("Duplicate rule id")
        ids.add(ident)
        if rule.get("kind") not in KINDS:
            raise ValueError("Rule kind must be priority or opener")
        _valid_name(rule.get("action"), "action")
        _valid_name(rule.get("reason"), "reason")
        if not isinstance(rule.get("exceptions"), list):
            raise ValueError("Exceptions must be a list (possibly empty)")
        for exception in rule["exceptions"]:
            _valid_name(exception, "exception")
        _check_context(rule.get("context"), "rule context")
        _check_predicates(rule.get("when"))
        rank, step = rule.get("rank"), rule.get("step")
        if rule["kind"] == "priority":
            if type(rank) is not int or rank < 1 or step is not None:
                raise ValueError("Priority rule needs positive rank, step=null")
        else:
            if type(step) is not int or step < 1 or rank is not None:
                raise ValueError("Opener rule needs positive step, rank=null")
        if not _verify_evidence(rule, packet["payloads"]):
            invalid_evidence.append(ident)
        key = _identity(rule)
        if key in seen and seen[key]["action"] != rule["action"]:
            duplicate_decisions.append((seen[key]["id"], ident))
        seen[key] = rule
    evaluations = []
    case_ids = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("Each test case must be an object")
        cid = _valid_name(case.get("id"), "case id")
        if cid in case_ids:
            raise ValueError("Duplicate case id")
        case_ids.add(cid)
        if case.get("kind") not in KINDS:
            raise ValueError("Unknown case kind")
        _check_context(case.get("context"), "case context")
        _check_context(case.get("state"), "case state")
        if case["kind"] == "priority":
            _valid_name(case.get("expected_action"), "expected action")
        else:
            actions = case.get("expected_actions")
            if not isinstance(actions, list) or not actions:
                raise ValueError("Opener case needs expected action sequence")
            for action in actions:
                _valid_name(action, "expected opener action")
        evaluated = _evaluate_case(case, rules)
        # Case IDs are author-controlled and can reveal source content. Public
        # reports use ordinal references only; private annotations retain IDs.
        evaluated.pop("id", None)
        evaluated["case_index"] = len(evaluations) + 1
        evaluations.append(evaluated)
    outcomes = Counter(e["result"] for e in evaluations)
    unexercised = sum(
        not any(case["kind"] == rule["kind"] and
                _applicability(rule, case) is True for case in cases)
        for rule in rules
    )
    exception_rules = sum(bool(rule["exceptions"]) for rule in rules)
    blockers = []
    if invalid_evidence:
        blockers.append("invalid_source_evidence")
    if duplicate_decisions:
        blockers.append("same_conditions_conflicting_actions")
    if not cases:
        blockers.append("no_decision_cases")
    if unexercised:
        blockers.append("unexercised_rule_branches")
    if exception_rules:
        # A free-text exception is not executable. It may override the winner.
        # Until represented by exact guarded rules, next-action QA is incomplete.
        blockers.append("unmodeled_rule_exceptions")
    if any(e["result"] != "matched" for e in evaluations):
        blockers.append("undecided_or_conflicting_decision_cases")
    return {
        "schema_version": REPORT,
        "annotation_rule_count": len(rules),
        "decision_case_count": len(cases),
        "case_outcome_counts": dict(sorted(outcomes.items())),
        "case_results": evaluations,
        "invalid_evidence_rule_count": len(invalid_evidence),
        "conflicting_identical_rule_pairs": len(duplicate_decisions),
        "unexercised_rule_count": unexercised,
        "unmodeled_exception_rule_count": exception_rules,
        "blocker_codes": sorted(set(blockers)),
        "all_declared_cases_matched": bool(cases) and not blockers,
        "source_meaning_independently_verified": False,
        "all_combat_states_tested": False,
        "gameplay_meaning_verified": False,
        "automatic_publish_allowed": False,
        "source_text_in_report": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-packet", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    packet = json.loads(args.source_packet.read_text(encoding="utf-8"))
    annotations = json.loads(args.annotations.read_text(encoding="utf-8"))
    result = assess_annotations(packet, annotations)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
