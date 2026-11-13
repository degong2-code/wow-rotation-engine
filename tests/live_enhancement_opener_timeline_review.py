"""Enhancement 12.1.5: real source-anchored PARTIAL opener state/next-action QA.

The original WHML is fetched in an opt-in CI diagnostic, SHA-locked, kept in a
temporary directory and never printed. This test assesses only explicitly
reviewed decisions: Stormbringer's optional early strike and first cooldown
fallback; Totemic's Doom Winds off-GCD paired cast and next Lava Lash.

Potion-specific full timeline, all tooltips, independent game optimization and
complete Q0/Q1 remain REVIEW. Do not generalize its spell IDs or 12 branches.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from tempfile import TemporaryDirectory

from engine.embedded_markup import _attrs
from engine.opener_timeline_qa import SCHEMA, assess_opener_timeline
from engine.source_acquisition_pipeline import run_specialization
from engine.source_choice_visibility import source_scopes_visible
from engine.source_page_acquire import SourceAccessError
from engine.source_scoped_evidence import _nested_scopes
from tests.live_enhancement_opener_review import (
    BASELINE, EXPECTED_GROUPS, inspect_original_opener_choices,
)

STEP = re.compile(r"\[(rt-step(?:-group)?)\s*=\s*(\d+)([^\]]*)\]", re.I)
PREPULL_CRASH = {
    "SB-OP-ST-LL", "SB-OP-ST-Reck", "SB-OP-ST-LP",
    "SB-OP-AOE-Reck", "T-OP-ST-LL", "T-OP-ST-Reck", "T-OP-ST-LP",
}


def _pred(field: str, value: bool) -> list[dict]:
    return [{"field": field, "op": "eq", "value": value}]


def _expected(action: str, beat: int, phase: str, lane: str,
              time_ms: int | None = None) -> dict:
    e = {"action": action, "beat": beat, "phase": phase, "lane": lane}
    if time_ms is not None:
        e.update(time_ms=time_ms, time_anchor="start")
    return e


def _build_index(packet: dict) -> tuple[str, dict]:
    assert inspect_original_opener_choices(packet)["source_scoped_paths_matched"] == 12
    source = packet["payloads"][0]
    raw = source["original_whml"]
    options = source["option_definitions"]
    scopes, _ = _nested_scopes(raw)
    positions = sorted((x["position"], x["radio_group"]) for x in options
                       if x["radio_group"] in EXPECTED_GROUPS)
    declared = {x["id"] for x in options}
    indexed = {choice: [] for choices in EXPECTED_GROUPS.values() for choice in choices}
    for m in STEP.finditer(raw):
        group = next((group for pos, group in reversed(positions)
                      if pos < m.start()), None)
        if group not in EXPECTED_GROUPS:
            continue
        attrs = _attrs(m.group(3))
        expressions = ([attrs["display-options"]]
                       if "display-options" in attrs else [])
        expressions += [x["attributes"]["display-options"] for x in scopes
                        if x["start"] < m.start() < x["end"]
                        and "display-options" in x["attributes"]]
        for choice in EXPECTED_GROUPS[group]:
            hero_name = "SB-Master" if group.startswith("Opener-Pot-SB") else "T-Master"
            fight_name = "Op-AoE" if group.endswith("-AOE") else "Op-ST"
            selected = {choice, hero_name, fight_name}
            visible = source_scopes_visible(expressions, selected, declared)
            if visible is None:
                raise SourceAccessError("Uninterpreted WHML visibility conditions")
            if visible:
                indexed[choice].append({
                    "spell": int(m.group(2)), "start": m.start(),
                    "end": m.end(), "marker": m.group(1) + "=" + m.group(2),
                })
    return raw, indexed


def _event(source: str, steps: list, spell: int, ident: str,
           beat: int, phase: str, lane: str = "gcd", *,
           occurrence: int = 0, when: list | None = None,
           effect: dict | None = None, time_ms: int | None = None) -> dict:
    matching = [x for x in steps if x["spell"] == spell]
    if len(matching) <= occurrence:
        raise SourceAccessError("Actual source step action absent")
    step = matching[occurrence]
    e = {
        "id": ident, "kind": "opener", "rank": None, "step": beat + 1,
        "action": "spell:" + str(spell), "beat": beat, "phase": phase,
        "lane": lane, "when": when or [], "set_state": effect or {},
        "evidence": [{
            "payload_sha256": BASELINE, "start": step["start"],
            "end": step["end"],
        }],
        "action_source_marker": step["marker"],
    }
    if time_ms is not None:
        e.update(time_ms=time_ms, time_anchor="start")
    return e


def _doom_event(raw: str, ident: str, beat: int) -> dict:
    """Cite explicit opener Doom Winds action note, not a tooltip-only hit."""
    start = raw.index("Best Enhancement Shaman Opener")
    stop = raw.index("Pre-Combat Check", start)
    marker = "[spell=384352]"
    loc = raw.find(marker, start, stop)
    if loc < 0:
        raise SourceAccessError("Opener Doom Winds action citation absent")
    return {
        "id": ident, "action": "spell:384352", "beat": beat,
        "phase": "combat", "lane": "off_gcd",
        "when": _pred("doom_winds_ready", True),
        "set_state": {"doom_winds_active": True},
        "evidence": [{
            "payload_sha256": BASELINE, "start": loc, "end": loc + len(marker),
        }],
        "action_source_marker": marker,
    }


def _branch_context(group: str, choice: str) -> dict:
    return {
        "hero": "stormbringer" if "-SB-" in group else "totemic",
        "targets": "aoe" if group.endswith("AOE") else "single",
        "potion": choice,
    }


def build_partial_annotations(packet: dict) -> dict:
    raw, index = _build_index(packet)
    branches, cases = [], []
    for group, choices in EXPECTED_GROUPS.items():
        for choice in choices:
            context = _branch_context(group, choice)
            source_steps = index[choice]
            events = []
            precrash = choice in PREPULL_CRASH
            if context["hero"] == "stormbringer":
                crash_phase = "prepull" if precrash else "pull"
                crash_ms = -1000 if precrash else 0
                events.append(_event(raw, source_steps, 187874, "initial-crash",
                                     0, crash_phase, time_ms=crash_ms))
                blaze_phase = "pull" if precrash else "combat"
                events.append(_event(raw, source_steps, 470057, "blaze",
                                     1, blaze_phase))
                events.append(_event(raw, source_steps, 17364, "optional-strike",
                                     2, "combat", when=_pred("early_strike", True)))
                events.append(_event(raw, source_steps, 114051, "ascendance",
                                     3, "combat"))
                events.append(_event(raw, source_steps, 187874, "cd-crash",
                                     4, "combat", occurrence=1,
                                     when=_pred("crash_ready", True)))
                events.append(_event(raw, source_steps, 115356, "windstrike",
                                     4, "combat",
                                     when=_pred("crash_ready", False)))
                for early in (False, True):
                    for ready in (False, True):
                        actions = [
                            _expected("spell:187874", 0, crash_phase, "gcd",
                                      crash_ms),
                            _expected("spell:470057", 1, blaze_phase, "gcd"),
                        ]
                        if early:
                            actions.append(_expected("spell:17364", 2, "combat", "gcd"))
                        actions.append(_expected("spell:114051", 3, "combat", "gcd"))
                        actions.append(_expected(
                            "spell:187874" if ready else "spell:115356",
                            4, "combat", "gcd"))
                        cases.append({
                            "id": choice + "-strike" + str(int(early)) +
                                  "-crash" + str(int(ready)),
                            "context": context,
                            "initial_state": {
                                "early_strike": early, "crash_ready": ready,
                            },
                            "expected_events": actions,
                        })
            else:
                if context["targets"] == "single":
                    events.append(_event(raw, source_steps, 187874, "initial-crash",
                                         0, "prepull", time_ms=-1000))
                    events.append(_event(raw, source_steps, 470057, "blaze",
                                         1, "pull"))
                    beat_base = 2
                else:
                    events.append(_event(raw, source_steps, 470057, "blaze",
                                         0, "pull"))
                    beat_base = 1
                events.append(_event(raw, source_steps, 444995, "totem",
                                     beat_base, "combat"))
                events.append(_event(raw, source_steps, 197214, "sundering",
                                     beat_base + 1, "combat"))
                if context["targets"] == "single":
                    events.append(_event(raw, source_steps, 60103, "first-lava",
                                         beat_base + 2, "combat"))
                    pair_beat = beat_base + 3
                    partner = 1218047
                else:
                    pair_beat = beat_base + 2
                    partner = 187874
                events.append(_doom_event(raw, "doom-winds", pair_beat))
                events.append(_event(raw, source_steps, partner, "paired-gcd",
                                     pair_beat, "combat"))
                events.append(_event(raw, source_steps, 60103, "followup-lava",
                                     pair_beat + 1, "combat",
                                     occurrence=1 if context["targets"] == "single" else 0,
                                     when=_pred("doom_winds_active", True)))
                expectation = []
                if context["targets"] == "single":
                    expectation += [
                        _expected("spell:187874", 0, "prepull", "gcd", -1000),
                        _expected("spell:470057", 1, "pull", "gcd"),
                    ]
                else:
                    expectation.append(_expected("spell:470057", 0, "pull", "gcd"))
                expectation += [
                    _expected("spell:444995", beat_base, "combat", "gcd"),
                    _expected("spell:197214", beat_base + 1, "combat", "gcd"),
                ]
                if context["targets"] == "single":
                    expectation.append(
                        _expected("spell:60103", beat_base + 2, "combat", "gcd"))
                expectation += [
                    _expected("spell:384352", pair_beat, "combat", "off_gcd"),
                    _expected("spell:" + str(partner), pair_beat, "combat", "gcd"),
                    _expected("spell:60103", pair_beat + 1, "combat", "gcd"),
                ]
                cases.append({
                    "id": choice + "-doom-paired",
                    "context": context,
                    "initial_state": {
                        "doom_winds_ready": True, "doom_winds_active": False,
                    },
                    "expected_events": expectation,
                })
            branches.append({"context": context, "events": events})
    return {
        "schema_version": SCHEMA, "source_sha256": BASELINE,
        "branches": branches, "cases": cases,
    }


def review(packet: dict) -> dict:
    annotations = build_partial_annotations(packet)
    result = assess_opener_timeline(packet, annotations)
    if not result["all_declared_cases_matched"]:
        raise AssertionError("Partial state decisions differ: " +
                             str(result["blocker_codes"]))
    return {
        "source_sha_locked": True,
        "partial_opener_contexts_reviewed": result["branch_count"],
        "partial_state_cases_consistent": result["case_count"],
        "partial_action_events_exercised": result["event_count"],
        "partial_case_outcomes": result["case_outcome_counts"],
        "all_events_source_anchored": result["invalid_evidence_count"] == 0
                                  and result["invalid_action_marker_count"] == 0,
        "all_twelve_complete_opener_timelines_verified": False,
        "potion_action_timing_fully_simulated": False,
        "all_game_mechanics_verified": False,
        "independent_optimization_verified": False,
        "automatic_publish_allowed": False,
    }


def main() -> None:
    try:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            acquisition = run_specialization(
                "고양 주술사", root, expected_guide_sha256=BASELINE)
            if acquisition.get("matches_known_baseline") is not True:
                print("enhancement_timeline_review=source_revision_review_required")
                return
            packet = json.loads(
                (root / "editorial-evidence-private.json").read_text(encoding="utf8")
            )
            report = review(packet)
            print("enhancement_timeline_review=partial_source_anchored_consistent")
            for key, value in report.items():
                print("enhancement_timeline_" + key + "=" +
                      json.dumps(value, ensure_ascii=True))
    except (SourceAccessError, ValueError, AssertionError, KeyError, IndexError) as exc:
        print("enhancement_timeline_review=content_or_source_review_required")
        print("enhancement_timeline_error_class=" + type(exc).__name__)


if __name__ == "__main__":
    main()
