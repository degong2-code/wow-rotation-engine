"""Private, source-anchored opener *timeline* QA.

Complements gameplay_decision_qa's ordered opener checks. The author supplies
all timings, GCD lanes, guards, and state effects; none are inferred from WHML.
A beat is an editorial decision point, not a number of elapsed GCDs. Events
sharing a beat examine the SAME incoming state and apply effects together.

No private action labels, source excerpts, or author case IDs enter reports.
Matching authored expectations is not independent gameplay optimization proof.
"""
from __future__ import annotations

from collections import Counter
import json
from typing import Any

from .gameplay_decision_qa import (
    _check_context, _check_predicates, _check_source, _compare, _equals,
    _valid_name, _verify_action_marker, _verify_evidence,
)

SCHEMA = "opener-timeline-private-v1"
REPORT = "opener-timeline-audit-v1"
PHASES = {"prepull", "pull", "combat"}
LANES = {"gcd", "off_gcd"}
ANCHORS = {"start", "finish", "impact", "use"}
MAX_BRANCHES = 100
MAX_EVENTS = 100
MAX_CASES = 500


def _key(context: dict) -> str:
    return json.dumps(sorted(context.items()), ensure_ascii=False)


def _event_signature(event: dict) -> tuple:
    return (
        event["beat"], event["phase"], event["lane"], event["action"],
        event.get("time_ms"), event.get("time_anchor"),
        event.get("within_beat_order"),
    )


def _check_time(event: dict) -> None:
    value, anchor = event.get("time_ms"), event.get("time_anchor")
    if (value is None) != (anchor is None):
        raise ValueError("time_ms and time_anchor must be supplied together")
    if value is None:
        return
    if type(value) is not int or not -600000 <= value <= 600000:
        raise ValueError("time_ms must be a bounded integer relative to pull")
    if anchor not in ANCHORS:
        raise ValueError("time_anchor must identify start/finish/impact/use")
    # An impact or finish can occur after a prepull start; do not infer when
    # casts land or how long they take.
    if anchor in {"start", "use"}:
        phase = event["phase"]
        if ((phase == "prepull" and value >= 0)
                or (phase == "pull" and value != 0)
                or (phase == "combat" and value < 0)):
            raise ValueError("Explicit start/use time contradicts phase")


def _check_event(event: Any) -> None:
    if not isinstance(event, dict):
        raise ValueError("Timeline event must be an object")
    _valid_name(event.get("id"), "event id")
    _valid_name(event.get("action"), "event action")
    if type(event.get("beat")) is not int or not 0 <= event["beat"] <= 200:
        raise ValueError("beat must be an editorial decision index 0..200")
    if event.get("phase") not in PHASES or event.get("lane") not in LANES:
        raise ValueError("phase/lane must be explicit")
    _check_time(event)
    order = event.get("within_beat_order")
    if order is not None and (type(order) is not int or not 0 <= order <= 20):
        raise ValueError("within_beat_order must be an integer 0..20")
    _check_predicates(event.get("when", []))
    _check_context(event.get("set_state", {}), "event set_state")
    marker = event.get("action_source_marker")
    _valid_name(marker, "action source marker")


def _check_expected(events: Any) -> None:
    if not isinstance(events, list) or len(events) > MAX_EVENTS:
        raise ValueError("Expected events must be a bounded list")
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("Expected event must be an object")
        if set(event) - {"action", "beat", "phase", "lane",
                         "time_ms", "time_anchor", "within_beat_order"}:
            raise ValueError("Unsupported expected event field")
        _valid_name(event.get("action"), "expected action")
        if type(event.get("beat")) is not int or not 0 <= event["beat"] <= 200:
            raise ValueError("Invalid expected beat")
        if event.get("phase") not in PHASES or event.get("lane") not in LANES:
            raise ValueError("Invalid expected phase/lane")
        _check_time(event)
        order = event.get("within_beat_order")
        if order is not None and (type(order) is not int or not 0 <= order <= 20):
            raise ValueError("Expected within_beat_order must be 0..20")


def _guard(event: dict, state: dict) -> bool | None:
    unknown = False
    for predicate in event.get("when", []):
        field = predicate["field"]
        if field not in state:
            unknown = True
            continue
        result = _compare(state[field], predicate["op"], predicate["value"])
        if result is False:
            return False
        if result is None:
            unknown = True
    return None if unknown else True


def _simulate(events: list[dict], initial_state: dict) -> tuple[str, list, set, dict]:
    """Replay only author-declared guards and effects, never inferred mechanics.

    Unordered events in a beat read the SAME initial state and commit together.
    When within_beat_order is explicitly declared, the earlier off-GCD action
    may modify state BEFORE the later GCD action checks its guard. This is
    required for activations such as Doom Winds -> empowered strike.
    """
    state = dict(initial_state)
    selected = []
    exercised = set()
    phase_order = {"prepull": 0, "pull": 1, "combat": 2}
    last_phase = 0
    last_start_ms = None
    for beat in sorted({event["beat"] for event in events}):
        group = [event for event in events if event["beat"] == beat]
        ordered = any(e.get("within_beat_order") is not None for e in group)
        certain = []
        if ordered:
            # Do not silently evaluate an unsequenced conditional against the
            # wrong intra-beat state. This is a review, not a guessed order.
            if any(e.get("within_beat_order") is None for e in group):
                return "underdetermined", [], set(), dict(state)
            for event in sorted(group, key=lambda e: e["within_beat_order"]):
                status = _guard(event, state)
                if status is None:
                    return "underdetermined", [], set(), dict(state)
                if status is False:
                    continue
                if (event["lane"] == "gcd" and
                        any(e["lane"] == "gcd" for e in certain)):
                    return "ambiguous", [], set(), dict(state)
                if (certain and
                        event["within_beat_order"] ==
                        certain[-1]["within_beat_order"]):
                    return "ambiguous", [], set(), dict(state)
                certain.append(event)
                # Explicitly ordered effects are visible to *later* actions
                # in the same decision beat, never to earlier actions.
                state.update(event.get("set_state", {}))
        else:
            uncertain = []
            for event in group:
                status = _guard(event, state)
                if status is True:
                    certain.append(event)
                elif status is None:
                    uncertain.append(event)
            if uncertain:
                return "underdetermined", [], set(), dict(state)
            if sum(e["lane"] == "gcd" for e in certain) > 1:
                return "ambiguous", [], set(), dict(state)
            changes = {}
            for event in certain:
                for field, value in event.get("set_state", {}).items():
                    if field in changes and not _equals(changes[field], value):
                        return "ambiguous", [], set(), dict(state)
                    changes[field] = value
            # Without declared order, changes are NOT visible within a beat.
            state.update(changes)

        # Check source-declared phases/times without inventing the execution
        # order of an unordered simultaneous event group.
        phase_sequence = [phase_order[e["phase"]] for e in certain]
        if ordered:
            for current in phase_sequence:
                if current < last_phase:
                    return "ambiguous", [], set(), dict(state)
                last_phase = current
        elif phase_sequence:
            if min(phase_sequence) < last_phase:
                return "ambiguous", [], set(), dict(state)
            last_phase = max(phase_sequence)
        observed = [e["time_ms"] for e in certain
                    if e.get("time_ms") is not None
                    and e.get("time_anchor") in {"start", "use"}]
        if ordered:
            for instant in observed:
                if last_start_ms is not None and instant < last_start_ms:
                    return "ambiguous", [], set(), dict(state)
                last_start_ms = instant
        elif observed:
            if last_start_ms is not None and min(observed) < last_start_ms:
                return "ambiguous", [], set(), dict(state)
            last_start_ms = max(observed)
        selected.extend(_event_signature(event) for event in certain)
        exercised.update(e["id"] for e in certain)
    return "ready", sorted(selected), exercised, dict(state)


def assess_opener_timeline(packet: dict, annotations: dict) -> dict:
    """Check declared branches and counterexamples against private source.

    The report is safe for CI logs; the private inputs are not publishable.
    """
    _check_source(packet)
    if annotations.get("schema_version") != SCHEMA:
        raise ValueError("Unexpected timeline annotation schema")
    digests = {p["sha256"] for p in packet["payloads"]}
    if annotations.get("source_sha256") not in digests or len(digests) != 1:
        raise ValueError("Timeline must lock exactly one original WHML revision")
    branches, cases = annotations.get("branches"), annotations.get("cases")
    if (not isinstance(branches, list) or not 1 <= len(branches) <= MAX_BRANCHES
            or not isinstance(cases, list) or not 1 <= len(cases) <= MAX_CASES):
        raise ValueError("Expected bounded, nonempty branches and cases")

    contexts = {}
    invalid_evidence = invalid_markers = 0
    event_ids = set()
    for branch in branches:
        _check_context(branch.get("context"), "branch context")
        key = _key(branch["context"])
        if key in contexts:
            raise ValueError("Duplicate branch choice context")
        events = branch.get("events")
        if not isinstance(events, list) or not 1 <= len(events) <= MAX_EVENTS:
            raise ValueError("Branch events must be a bounded, nonempty list")
        local_ids = set()
        for event in events:
            _check_event(event)
            if event["id"] in local_ids:
                raise ValueError("Duplicate event ID in branch")
            local_ids.add(event["id"])
            event_ids.add((key, event["id"]))
            if not _verify_evidence(event, packet["payloads"]):
                invalid_evidence += 1
            if not _verify_action_marker(event, packet["payloads"]):
                invalid_markers += 1
        contexts[key] = events

    results = []
    covered = set()
    exercised = set()
    case_ids = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("Timeline case must be an object")
        ident = _valid_name(case.get("id"), "case id")
        if ident in case_ids:
            raise ValueError("Duplicate case id")
        case_ids.add(ident)
        _check_context(case.get("context"), "case context")
        _check_context(case.get("initial_state"), "case initial state")
        if "expected_final_state" in case:
            _check_context(case["expected_final_state"], "case expected final state")
        _check_expected(case.get("expected_events"))
        key = _key(case["context"])
        if key not in contexts:
            result = "no_branch"
        else:
            covered.add(key)
            result, got, winners, final_state = _simulate(
                contexts[key], case["initial_state"])
            if result == "ready":
                expected = sorted(_event_signature(event)
                                  for event in case["expected_events"])
                # A declared postcondition asserts only specific, independently
                # justified state facts; omission is not treated as false.
                postconditions_match = all(
                    field in final_state and _equals(final_state[field], value)
                    for field, value in case.get("expected_final_state", {}).items()
                )
                result = "matched" if got == expected and postconditions_match else "mismatch"
                exercised.update((key, winner) for winner in winners)
        results.append({"case_index": len(results) + 1, "result": result})

    missing_branches = len(contexts) - len(covered)
    unexercised = len(event_ids - exercised)
    blockers = []
    if invalid_evidence:
        blockers.append("invalid_source_evidence")
    if invalid_markers:
        blockers.append("action_not_in_cited_source_span")
    if missing_branches:
        blockers.append("unreviewed_branch_contexts")
    if unexercised:
        blockers.append("unexercised_timeline_events")
    if any(x["result"] != "matched" for x in results):
        blockers.append("undecided_or_conflicting_timeline_cases")
    return {
        "schema_version": REPORT,
        "branch_count": len(branches),
        "case_count": len(cases),
        "event_count": len(event_ids),
        "case_outcome_counts": dict(sorted(Counter(x["result"] for x in results).items())),
        "case_results": results,
        "unreviewed_branch_count": missing_branches,
        "unexercised_event_count": unexercised,
        "invalid_evidence_count": invalid_evidence,
        "invalid_action_marker_count": invalid_markers,
        "blocker_codes": blockers,
        "all_declared_cases_matched": not blockers,
        "original_source_meaning_independently_verified": False,
        "timing_and_gcd_game_mechanics_verified": False,
        "all_combat_states_tested": False,
        "automatic_publish_allowed": False,
        "source_text_in_report": False,
    }
