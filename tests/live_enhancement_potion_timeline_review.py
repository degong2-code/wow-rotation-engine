"""Source-locked 12-choice Enhancement potion PLACEMENT audit, not DPS proof.

Checks one actual potion-action token in a visible ordered list per source
choice, plus source-declared relative placement/timing against nearby opener
abilities. The item effects, GCD rules beyond first-GCD co-use, proc stats,
gameplay optimization and complete rotation remain outside this scope.
No original source text or user HTML is logged or stored publicly.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory

from engine.opener_timeline_qa import SCHEMA, assess_opener_timeline
from engine.source_page_acquire import SourceAccessError
from engine.source_acquisition_pipeline import run_specialization
from engine.source_scoped_evidence import _nested_scopes
from engine.source_choice_visibility import source_scopes_visible
from live_enhancement_opener_review import (
    BASELINE, EXPECTED_GROUPS, inspect_original_opener_choices,
)
from live_enhancement_opener_timeline_review import (
    _build_index, _event, _expected, _pred,
)

POTIONS = {"LL": 1295132, "Reck": 1236994, "LP": 1236616}
POTION_TOKEN = re.compile(r"\[spell\s*=\s*(1295132|1236994|1236616)\]")


def _evidence_by_choice(packet: dict) -> dict:
    """Only choice-gated ordered-list potion *actions*, not adjacent notes."""
    inspect_original_opener_choices(packet)
    source = packet["payloads"][0]
    raw = source["original_whml"]
    start = raw.index("Best Enhancement Shaman Opener")
    stop = raw.index("Pre-Combat Check", start)
    options = source["option_definitions"]
    declared = {o["id"] for o in options}
    positions = sorted((o["position"], o["radio_group"]) for o in options
                       if o["radio_group"] in EXPECTED_GROUPS)
    scopes, issues = _nested_scopes(raw)
    # The original page may include unrelated WHML bracket mismatches.
    # The action gate below checks the exact relevant enclosing scopes and
    # requires one unique action independently for every actual choice.
    result = {}
    for group, choices in EXPECTED_GROUPS.items():
        hero = "SB-Master" if "-SB-" in group else "T-Master"
        fight = "Op-AoE" if group.endswith("-AOE") else "Op-ST"
        for choice in choices:
            ident = POTIONS[choice.split("-")[-1]]
            hits = []
            for m in POTION_TOKEN.finditer(raw, start, stop):
                if int(m.group(1)) != ident:
                    continue
                position = m.start()
                owner = next((g for at, g in reversed(positions)
                              if at < position), None)
                if owner != group:
                    continue
                parents = [s for s in scopes if s["start"] < position < s["end"]]
                if not any(p["tag"] == "li" for p in parents):
                    continue
                if not any(p["tag"] == "ol" for p in parents):
                    continue
                expr = [p["attributes"]["display-options"] for p in parents
                        if "display-options" in p["attributes"]]
                gated = any(choice in re.findall(r"[A-Za-z0-9_-]+", x)
                            for x in expr)
                if not gated:
                    continue
                if source_scopes_visible(expr, {choice, hero, fight}, declared) is True:
                    hits.append({
                        "start": m.start(), "end": m.end(),
                        "marker": m.group(0), "spell": ident,
                    })
            if len(hits) != 1:
                raise SourceAccessError(
                    "Potion action not uniquely identified in choice-gated ordered list"
                )
            result[choice] = hits[0]
    return result


def _potion_event(hit: dict, beat: int, phase: str, *,
                  time_ms: int | None = None) -> dict:
    event = {
        "id": "selected-potion",
        "action": "potion:" + str(hit["spell"]),
        "beat": beat, "phase": phase, "lane": "off_gcd",
        "when": [], "set_state": {"selected_potion_used": True},
        "evidence": [{
            "payload_sha256": BASELINE,
            "start": hit["start"], "end": hit["end"],
        }],
        "action_source_marker": hit["marker"],
    }
    if time_ms is not None:
        event["time_ms"] = time_ms
        event["time_anchor"] = "use"
    return event


def _expected_potion(hit: dict, beat: int, phase: str,
                     time_ms: int | None = None) -> dict:
    e = {"action": "potion:" + str(hit["spell"]),
         "beat": beat, "phase": phase, "lane": "off_gcd"}
    if time_ms is not None:
        e.update(time_ms=time_ms, time_anchor="use")
    return e


def build_potion_cases(packet: dict) -> dict:
    source, indexed = _build_index(packet)
    hits = _evidence_by_choice(packet)
    branches, cases = [], []
    for group, choices in EXPECTED_GROUPS.items():
        storm = "-SB-" in group
        aoe = group.endswith("-AOE")
        for choice in choices:
            potion = choice.split("-")[-1]
            context = {
                "hero": "stormbringer" if storm else "totemic",
                "targets": "aoe" if aoe else "single",
                "potion": choice,
            }
            seq = indexed[choice]
            events, expectations = [], []

            def spell(ident: int, beat: int, phase: str,
                      time_ms: int | None = None, *,
                      when: list | None = None) -> None:
                e = _event(source, seq, ident, "s" + str(beat), beat,
                           phase, time_ms=time_ms, when=when)
                events.append(e)
                expectations.append(_expected(
                    "spell:" + str(ident), beat, phase, "gcd", time_ms))

            def pot(beat: int, phase: str,
                    time_ms: int | None = None) -> None:
                events.append(_potion_event(hits[choice], beat, phase,
                                            time_ms=time_ms))
                expectations.append(_expected_potion(
                    hits[choice], beat, phase, time_ms))

            if storm and not aoe:
                if potion == "LL":
                    pot(0, "prepull", -12000)
                    spell(187874, 1, "prepull", -1000)
                    spell(470057, 2, "pull")
                elif potion == "Reck":
                    spell(187874, 0, "prepull", -1000)
                    pot(1, "prepull")
                    spell(470057, 2, "pull")
                else:
                    spell(187874, 0, "prepull", -1000)
                    spell(470057, 1, "pull")
                    spell(17364, 2, "combat", when=_pred("early_strike", True))
                    pot(3, "combat")
                    spell(114051, 4, "combat")
            elif storm and aoe:
                if potion == "Reck":
                    spell(187874, 0, "prepull", -1000)
                    pot(1, "prepull")
                    spell(470057, 2, "pull")
                else:
                    # The guide explicitly places both item use and
                    # Crash Lightning at the very first combat GCD, with
                    # no claimed ordering between those simultaneous events.
                    spell(187874, 0, "pull", 0)
                    pot(0, "pull", 0)
                    spell(470057, 1, "combat")
            elif not aoe:
                spell(187874, 0, "prepull", -1000)
                if potion == "Reck":
                    pot(1, "prepull")
                    spell(470057, 2, "pull")
                else:
                    spell(470057, 1, "pull")
                    pot(2, "combat")
                spell(444995, 3, "combat")
            else:
                if potion == "Reck":
                    pot(0, "prepull")
                    spell(470057, 1, "pull")
                else:
                    spell(470057, 0, "pull")
                    pot(1, "combat")
                spell(444995, 2, "combat")

            if sum(e["id"] == "selected-potion" for e in events) != 1:
                raise AssertionError("Potion branch must contain exactly one potion")
            branches.append({"context": context, "events": events})
            # With LP, the optional Stormstrike branch must be checked both
            # when present and when skipped, without manufacturing a stack
            # count or a proc outcome.
            choices_of_strike = (False, True) if storm and not aoe and potion == "LP" else (False,)
            for early in choices_of_strike:
                selected_events = [e for e in expectations
                                   if not (e["action"] == "spell:17364" and not early)]
                cases.append({
                    "id": choice + "-strike" + str(int(early)),
                    "context": context,
                    "initial_state": {
                        "early_strike": early,
                        "selected_potion_used": False,
                    },
                    "expected_events": selected_events,
                    "expected_final_state": {"selected_potion_used": True},
                })
    return {
        "schema_version": SCHEMA,
        "source_sha256": BASELINE,
        "branches": branches,
        "cases": cases,
    }


def negative_controls(packet: dict, annotations: dict) -> int:
    """Deliberate deviations that must fail, not simply match authored steps."""
    rejected = 0

    def one(choice: str, early: int = 0) -> dict:
        data = deepcopy(annotations)
        data["branches"] = [b for b in data["branches"]
                            if b["context"]["potion"] == choice]
        data["cases"] = [c for c in data["cases"]
                         if c["id"] == choice + "-strike" + str(early)]
        if len(data["branches"]) != 1 or len(data["cases"]) != 1:
            raise AssertionError("Missing known potion regression anchor")
        return data

    def fails(data: dict) -> None:
        nonlocal rejected
        report = assess_opener_timeline(packet, data)
        if report["all_declared_cases_matched"]:
            raise AssertionError("Incorrect potion sequence incorrectly accepted")
        if report["case_results"][0]["result"] not in {
            "mismatch", "ambiguous", "underdetermined",
        }:
            raise AssertionError("Unexpected potion negative result")
        rejected += 1

    # ST Liquid Luster needs ramp before pull, not just any prepot.
    wrong_ll_time = one("SB-OP-ST-LL")
    next(e for e in wrong_ll_time["branches"][0]["events"]
         if e["id"] == "selected-potion")["time_ms"] = -1000
    fails(wrong_ll_time)

    # Stormbringer AoE Liquid Luster belongs with first GCD, not prepull.
    wrong_aoe_time = one("SB-OP-AOE-LL")
    pot = next(e for e in wrong_aoe_time["branches"][0]["events"]
               if e["id"] == "selected-potion")
    pot.update(phase="prepull", beat=0, time_ms=-1000)
    fails(wrong_aoe_time)

    # Stormbringer ST Light's Potential must follow optional strike,
    # and precede Ascendance, not happen before the setup.
    before_strike = one("SB-OP-ST-LP", 1)
    pot = next(e for e in before_strike["branches"][0]["events"]
               if e["id"] == "selected-potion")
    pot["beat"] = 1
    fails(before_strike)

    # Totemic AoE Recklessness has a PREcombat use, unlike its alternatives.
    wrong_totemic = one("T-OP-AOE-Reck")
    pot = next(e for e in wrong_totemic["branches"][0]["events"]
               if e["id"] == "selected-potion")
    pot["phase"], pot["beat"] = "combat", 2
    fails(wrong_totemic)

    # Mutually exclusive potions: a duplicate action must be rejected.
    duplicate = one("T-OP-ST-LL")
    pot = next(e for e in duplicate["branches"][0]["events"]
               if e["id"] == "selected-potion")
    extra = deepcopy(pot)
    extra["id"] = "incorrect-second-potion"
    extra["beat"] = 4
    duplicate["branches"][0]["events"].append(extra)
    fails(duplicate)

    return rejected


def review(packet: dict) -> dict:
    annotated = build_potion_cases(packet)
    result = assess_opener_timeline(packet, annotated)
    if not result["all_declared_cases_matched"]:
        raise AssertionError(
            "Source-locked potion placement decisions inconsistent: " +
            str(result["blocker_codes"])
        )
    negative = negative_controls(packet, annotated)
    return {
        "original_whml_sha_locked": True,
        "actual_potion_contexts_source_anchored": result["branch_count"],
        "potion_placement_state_cases_matched": result["case_count"],
        "potion_placement_negative_cases_rejected": negative,
        "one_real_source_potion_action_per_choice": True,
        "potion_effect_stacks_verified": False,
        "item_cooldown_and_gcd_independently_verified": False,
        "all_opener_abilities_modeled": False,
        "gameplay_optimality_verified": False,
        "automatic_publish_allowed": False,
    }


def main() -> None:
    try:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            acquisition = run_specialization(
                "고양 주술사", root, expected_guide_sha256=BASELINE)
            if acquisition.get("matches_known_baseline") is not True:
                print("enhancement_potion_timeline=source_revision_review_required")
                return
            packet = json.loads(
                (root / "editorial-evidence-private.json").read_text("utf8"))
            result = review(packet)
            print("enhancement_potion_timeline=source_scoped_partial_consistent")
            for key, value in result.items():
                print("enhancement_potion_" + key + "=" +
                      json.dumps(value, ensure_ascii=True))
    except (SourceAccessError, ValueError, KeyError,
            AssertionError, IndexError) as exc:
        print("enhancement_potion_timeline=source_or_content_review_required")
        print("enhancement_potion_error_class=" + type(exc).__name__)
        known = {
            "Nested source container issue needs review": "unrelated_nested_scope_issue",
            "Potion action not uniquely identified in choice-gated ordered list":
                "potion_action_unique_match_failed",
            "Source-locked potion placement decisions inconsistent": "source_case_mismatch",
        }
        print("enhancement_potion_review_reason=" +
              known.get(str(exc), "needs_private_diagnostic"))


if __name__ == "__main__":
    main()
