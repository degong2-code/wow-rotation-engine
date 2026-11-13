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




def _verify_action_marker(rule: dict, payloads: list) -> bool:
    """An optional exact action marker must be inside one cited source span.

    Confirms a concrete source token, not that the gameplay interpretation or
    author-written rationale is true. A marker cannot substitute for evidence.
    """
    marker = rule.get("action_source_marker")
    if marker is None:
        return True
    if not isinstance(marker, str) or not 3 <= len(marker) <= 100:
        return False
    # The FIRST citation is the action's own source span. Later citations
    # may be explanatory tooltips/notes and must not legitimize an unrelated
    # action. The source markup can represent an action as a list, table, or
    # custom component, so do not impose a class-specific row/tag template.
    citations = rule.get("evidence")
    if not isinstance(citations, list) or not citations:
        return False
    ref = citations[0]
    if not isinstance(ref, dict):
        return False
    for payload in payloads:
        if payload.get("sha256") != ref.get("payload_sha256"):
            continue
        start, end = ref.get("start"), ref.get("end")
        body = payload["original_whml"]
        if type(start) is int and type(end) is int and 0 <= start < end <= len(body):
            return marker in body[start:end]
    return False


def _rule_exercised_as_winner(rule: dict, cases: list[dict], rules: list[dict]) -> bool:
    """Being technically applicable is insufficient if always shadowed."""
    for case in cases:
        if case["kind"] != rule["kind"] or _applicability(rule, case) is not True:
            continue
        if rule["kind"] == "opener":
            return True
        competing = any(
            other is not rule and other["kind"] == "priority"
            and (
                other["rank"] < rule["rank"]
                or (other["rank"] == rule["rank"] and other["action"] != rule["action"])
            )
            and _applicability(other, case) is not False
            for other in rules
        )
        # Missing higher-priority state is UNKNOWN, not a proven selection.
        # Ties leading to a different action are not a tested winner either.
        if not competing:
            return True
    return False

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



def _target_predicate_possible(predicate: dict, low: int, high: int | None) -> bool:
    """Conservatively discard only a target-count guard impossible in the view.

    Unknown/other predicates stay intact, including talents, stacks and procs.
    This is NOT a gameplay inference or a general SAT solver.
    """
    if predicate["field"] != "target_count":
        return True
    op, value = predicate["op"], predicate["value"]
    if type(value) not in (int, float):
        return True
    if op == "eq":
        return low <= value and (high is None or value <= high)
    if op == "neq":
        return not (high == low == value)
    if op == "lt":
        return low < value
    if op == "lte":
        return low <= value
    if op == "gt":
        return high is None or high > value
    if op == "gte":
        return high is None or high >= value
    return True


def project_priority_view(
    source_rules: list[dict], *, view_context: dict,
    min_targets: int, max_targets: int | None = None,
) -> list[dict]:
    """Create display rows by REFERENCE to a single source decision list.

    The editorial source rules must first be grounded to exact source spans
    using assess_annotations and separately checked for gameplay meaning.
    Projection NEVER rewrites an operator/threshold, action, explanation, or
    source condition text. It only removes a rule when the view makes it
    provably inapplicable. Complex OR clauses must be preserved as independently
    authored branches; never reinterpret opaque prose to filter a rule.

    The returned dictionaries are safe to use as the actual HTML table inputs.
    Existing legacy Arcane drafts are NOT implicitly validated by this function.
    """
    from copy import deepcopy

    _check_context(view_context, "view context")
    if type(min_targets) is not int or min_targets < 1:
        raise ValueError("min_targets must be a positive integer")
    if max_targets is not None and (
        type(max_targets) is not int or max_targets < min_targets
    ):
        raise ValueError("max_targets must be >= min_targets")
    if not isinstance(source_rules, list) or not 0 < len(source_rules) <= MAX_RULES:
        raise ValueError("Bounded canonical source rules required")
    seen = set()
    selected = []
    for rule in source_rules:
        if not isinstance(rule, dict) or rule.get("kind") != "priority":
            raise ValueError("Priority projection only accepts source priority rules")
        ident = _valid_name(rule.get("id"), "canonical source rule ID")
        if ident in seen:
            raise ValueError("Duplicate canonical source rule ID")
        seen.add(ident)
        if type(rule.get("rank")) is not int or rule["rank"] < 1:
            raise ValueError("Canonical source priority must be positive")
        _valid_name(rule.get("action"), "source action")
        _valid_name(rule.get("reason"), "source reason")
        _valid_name(rule.get("condition_text"), "source condition text")
        _check_context(rule.get("context"), "source context")
        if "when_any" in rule:
            # DNF: every clause is AND; the clauses are OR. Never flatten
            # this into a single AND list, which would change the decision.
            branches = rule["when_any"]
            if (not isinstance(branches, list) or not branches or
                    len(branches) > 20):
                raise ValueError("when_any must be a bounded nonempty OR list")
            for clause in branches:
                _check_predicates(clause)
            if rule.get("when") not in (None, []):
                raise ValueError("Provide when or when_any, never both")
        else:
            _check_predicates(rule.get("when"))
        exceptions = rule.get("exceptions")
        if not isinstance(exceptions, list) or any(
            not isinstance(x, str) or not x.strip() for x in exceptions
        ):
            raise ValueError("Source exceptions must remain explicit")
        missing = set(rule["context"]) - set(view_context)
        if missing:
            raise ValueError("View lacks required source context; cannot choose branch")
        if any(not _equals(view_context[k], v) for k, v in rule["context"].items()):
            continue
        clauses = rule.get("when_any", [rule.get("when", [])])
        # A rule can be omitted only if EVERY OR alternative is impossible.
        if not any(all(_target_predicate_possible(c, min_targets, max_targets)
                       for c in clause) for clause in clauses):
            continue
        selected.append(rule)

    # Retain source ordering, not author-restated ST/AoE priority numbers.
    selected.sort(key=lambda rule: rule["rank"])
    rows = []
    for idx, rule in enumerate(selected, 1):
        rows.append({
            "source_rule_id": rule["id"],
            "source_rank": rule["rank"],
            "view_rank": idx,
            "action": rule["action"],
            "when": deepcopy(rule.get("when", [])),
            **({"when_any": deepcopy(rule["when_any"])}
               if "when_any" in rule else {}),
            "condition_text": rule["condition_text"],
            "reason": rule["reason"],
            "exceptions": deepcopy(rule["exceptions"]),
            "evidence": deepcopy(rule.get("evidence")),
        })
    return rows



def _predicate_entails(known: dict, required: dict) -> bool:
    """Sound, intentionally incomplete implication for one source-state field.

    This checks only explicit predicates. It does NOT infer WoW mechanics or
    turn an opaque condition_text into a gameplay predicate.
    """
    if known["field"] != required["field"]:
        return False
    if known == required:
        return True
    if known["op"] == "eq":
        return _compare(known["value"], required["op"], required["value"]) is True
    if known["op"] == "neq":
        return (required["op"] == "neq"
                and _equals(known["value"], required["value"]))
    if known["op"] not in {"lt", "lte", "gt", "gte"} or (
        required["op"] not in {"lt", "lte", "gt", "gte"}
    ):
        return False
    a, b = known["value"], required["value"]
    if any(type(x) not in (int, float) for x in (a, b)):
        return False
    if known["op"] in {"lt", "lte"} and required["op"] in {"lt", "lte"}:
        return a < b or (a == b and (
            known["op"] == "lt" or required["op"] == "lte"
        ))
    if known["op"] in {"gt", "gte"} and required["op"] in {"gt", "gte"}:
        return a > b or (a == b and (
            known["op"] == "gt" or required["op"] == "gte"
        ))
    return False


def _clause_entails(known: list[dict], required: list[dict]) -> bool:
    """Every required AND predicate is established by a known AND predicate."""
    return all(
        any(_predicate_entails(item, condition) for item in known)
        for condition in required
    )


def audit_priority_shadowing(
    source_rules: list[dict], *, view_context: dict,
    min_targets: int, max_targets: int | None = None,
) -> dict:
    """Flag lower-priority actions provably masked by earlier encoded rules.

    Applies to canonical priority rows of ANY specialization. A lower rule is
    shadowed only if each possible OR branch is covered by at least one earlier
    rule's explicit AND clause. Rules with unmodeled textual exceptions cannot
    establish such a proof. This is a REVIEW signal: never delete a rule,
    change its rank, or claim gameplay meaning is verified by this audit.

    Numeric and equality implications are deliberately incomplete. Missing
    proof is UNKNOWN, not proof of reachability or correctness. Only harmless
    row indices and counts are returned, never source prose or spell names.
    """
    rows = project_priority_view(
        source_rules, view_context=view_context,
        min_targets=min_targets, max_targets=max_targets,
    )
    by_id = {rule["id"]: rule for rule in source_rules}
    shadowed = []
    for row in rows:
        lower = by_id[row["source_rule_id"]]
        if lower["exceptions"]:
            continue
        lower_clauses = lower.get("when_any", [lower.get("when", [])])
        # Ignore branches that are impossible for this ST/AoE view. The
        # projector retains the original branches for faithful HTML output.
        lower_clauses = [
            clause for clause in lower_clauses
            if all(_target_predicate_possible(c, min_targets, max_targets)
                   for c in clause)
        ]
        if not lower_clauses:
            continue
        prior = []
        for upper_row in rows:
            if upper_row["source_rank"] >= row["source_rank"]:
                continue
            upper = by_id[upper_row["source_rule_id"]]
            if upper["exceptions"]:
                continue
            for clause in upper.get("when_any", [upper.get("when", [])]):
                # In an editorial draft, an empty structured guard often means
                # readiness is still described only in condition_text. Treat
                # it as UNKNOWN, never as a proven unconditional action.
                if not clause:
                    continue
                if all(_target_predicate_possible(c, min_targets, max_targets)
                       for c in clause):
                    prior.append((upper, clause))
        if not prior:
            continue
        # Different earlier rows may cover different OR alternatives. Do
        # not incorrectly require one earlier rule to cover every branch.
        if all(any(_clause_entails(lower_clause, prior_clause)
                   for _, prior_clause in prior)
               for lower_clause in lower_clauses):
            # Full coverage proves shadowing under encoded predicates.
            # Action attribution must be more cautious: if same/different
            # higher actions coexist, their actual winning subregions are
            # not solved here. Classify that case as mixed/REVIEW.
            higher_actions = {upper["action"] for upper, _ in prior}
            if higher_actions == {lower["action"]}:
                classification = "same_action"
            elif lower["action"] not in higher_actions:
                classification = "different_action"
            else:
                classification = "mixed_action"
            shadowed.append({
                "view_rank": row["view_rank"],
                "classification": classification,
            })
    different = [item["view_rank"] for item in shadowed
                 if item["classification"] == "different_action"]
    same = [item["view_rank"] for item in shadowed
            if item["classification"] == "same_action"]
    mixed = [item["view_rank"] for item in shadowed
             if item["classification"] == "mixed_action"]
    return {
        "schema_version": "priority-shadow-audit-v1",
        "view_row_count": len(rows),
        "provably_shadowed_view_ranks": [item["view_rank"] for item in shadowed],
        "different_action_shadowed_view_ranks": different,
        "same_action_shadowed_view_ranks": same,
        "mixed_action_shadowed_view_ranks": mixed,
        "priority_shadow_review_required": bool(different or mixed),
        "basis": "explicit_predicate_implication_only",
        "all_other_rows_reachable_verified": False,
        "source_meaning_verified": False,
        "automatic_publish_allowed": False,
    }

def audit_priority_view(
    source_rules: list[dict], rendered_rows: list[dict], *,
    view_context: dict, min_targets: int, max_targets: int | None = None,
) -> dict:
    """Fail closed if rendered rows differ from the canonical projection.

    The caller must pass the ACTUAL output-table row records, not a second
    independently edited expectation list. Only issue counts leave the private
    source packet; public reports never echo the source or spell labels.
    """
    from collections import Counter

    expected = project_priority_view(
        source_rules, view_context=view_context,
        min_targets=min_targets, max_targets=max_targets,
    )
    if not isinstance(rendered_rows, list) or len(rendered_rows) > MAX_RULES:
        raise ValueError("Rendered projection rows must be a bounded list")
    keys = (
        "source_rule_id", "source_rank", "view_rank", "action",
        "when", "condition_text", "reason", "exceptions", "evidence",
    )
    expected_ids = Counter(row["source_rule_id"] for row in expected)
    actual_ids = Counter(
        row.get("source_rule_id") for row in rendered_rows
        if isinstance(row, dict) and isinstance(row.get("source_rule_id"), str)
    )
    missing = sum((expected_ids - actual_ids).values())
    extra = sum((actual_ids - expected_ids).values())
    malformed = sum(
        not isinstance(row, dict) or
        any(field not in row for field in keys)
        for row in rendered_rows
    )
    expected_by_id = {row["source_rule_id"]: row for row in expected}
    altered = sum(
        isinstance(row, dict) and row.get("source_rule_id") in expected_by_id and
        (any(row.get(field) != expected_by_id[row["source_rule_id"]][field]
             for field in keys) or
         row.get("when_any") != expected_by_id[row["source_rule_id"]].get("when_any"))
        for row in rendered_rows
    )
    order_changed = (
        [row.get("source_rule_id") if isinstance(row, dict) else None
         for row in rendered_rows]
        != [row["source_rule_id"] for row in expected]
    )
    blockers = []
    if missing:
        blockers.append("source_rule_missing_from_view")
    if extra or malformed:
        blockers.append("unmapped_or_malformed_view_rule")
    if altered:
        blockers.append("source_rule_changed_during_projection")
    if order_changed:
        blockers.append("source_order_changed_during_projection")
    return {
        "source_rule_count": len(source_rules),
        "expected_view_row_count": len(expected),
        "actual_view_row_count": len(rendered_rows),
        "missing_source_rule_count": missing,
        "extra_source_rule_count": extra,
        "changed_source_rule_count": altered,
        "malformed_view_row_count": malformed,
        "source_order_changed": order_changed,
        "blocker_codes": blockers,
        "projection_preserved": not blockers,
        "source_meaning_independently_verified": False,
        "gameplay_meaning_verified": False,
        "automatic_publish_allowed": False,
        "source_text_in_report": False,
    }


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
    invalid_action_markers = []
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
        if not _verify_action_marker(rule, packet["payloads"]):
            invalid_action_markers.append(ident)
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
        not _rule_exercised_as_winner(rule, cases, rules)
        for rule in rules
    )
    exception_rules = sum(bool(rule["exceptions"]) for rule in rules)
    blockers = []
    if invalid_evidence:
        blockers.append("invalid_source_evidence")
    if invalid_action_markers:
        blockers.append("action_not_in_cited_source_span")
    if duplicate_decisions:
        blockers.append("same_conditions_conflicting_actions")
    if not cases:
        blockers.append("no_decision_cases")
    minimum = annotations.get("minimum_decision_cases")
    if minimum is not None:
        if type(minimum) is not int or not 1 <= minimum <= MAX_CASES:
            raise ValueError("minimum_decision_cases must be an integer 1..MAX_CASES")
        if len(cases) < minimum:
            blockers.append("insufficient_decision_cases")
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
        "invalid_action_marker_rule_count": len(invalid_action_markers),
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
