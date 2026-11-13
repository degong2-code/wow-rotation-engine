"""Source-locked review of 12 *actual* Enhancement opener choice paths.

This is a constrained source-evidence regression, not a live game simulator.
It uses a private, temporary WHML packet obtained through the existing
standard HTTPS path. Never expose WHML, tooltip prose or personal HTML in CI.
"""
from __future__ import annotations

from collections import Counter
import json
import re
from pathlib import Path
from tempfile import TemporaryDirectory

from engine.embedded_markup import _attrs
from engine.source_acquisition_pipeline import run_specialization
from engine.source_page_acquire import SourceAccessError
from engine.source_scoped_evidence import _nested_scopes
from engine.source_choice_visibility import source_scopes_visible

BASELINE = "6657591171c36c79797b739b2248e37b9d967094e7d33e8dd799293283bd5dbe"
# These are observed choice IDs in the user-verified 2026-10-13 original.
# This expected *evidence fingerprint* must never become a generic template.
EXPECTED_GROUPS = {
    "Opener-Pot-SB-ST": ("SB-OP-ST-LL", "SB-OP-ST-Reck", "SB-OP-ST-LP"),
    "Opener-Pot-SB-AOE": ("SB-OP-AOE-LL", "SB-OP-AOE-Reck", "SB-OP-AOE-LP"),
    "Opener-Pot-T-ST": ("T-OP-ST-LL", "T-OP-ST-Reck", "T-OP-ST-LP"),
    "Opener-Pot-T-AOE": ("T-OP-AOE-LL", "T-OP-AOE-Reck", "T-OP-AOE-LP"),
}
EXPECTED_DEFAULTS = {values[1] for values in EXPECTED_GROUPS.values()}
# Source-locked technical regression fingerprint, not a rotation template.
# (effective visible step count, first technical spell ID, precast count)
EXPECTED_PATH_SUMMARY = {
    "SB-OP-ST-LL": (8, 1295132, 2),
    "SB-OP-ST-Reck": (7, 187874, 1),
    "SB-OP-ST-LP": (7, 187874, 1),
    "SB-OP-AOE-LL": (7, 187874, 0),
    "SB-OP-AOE-Reck": (7, 187874, 1),
    "SB-OP-AOE-LP": (7, 187874, 0),
    "T-OP-ST-LL": (8, 187874, 1),
    "T-OP-ST-Reck": (8, 187874, 1),
    "T-OP-ST-LP": (8, 187874, 1),
    "T-OP-AOE-LL": (11, 470057, 0),
    "T-OP-AOE-Reck": (12, 1236994, 1),
    "T-OP-AOE-LP": (11, 470057, 0),
}

TAG = re.compile(r"\[([a-z][\w-]*)\b([^\]]*)\]", re.I)
SPELL = re.compile(r"^\s*=\s*(\d+)\b")
TYPES = {"rt-step", "rt-step-group"}


def inspect_original_opener_choices(packet: dict) -> dict:
    """Validate source-side choice coverage; never return private source text."""
    payloads = packet.get("payloads", [])
    if len(payloads) != 1 or payloads[0].get("sha256") != BASELINE:
        raise SourceAccessError("Original WHML revision differs from verified baseline")
    source = payloads[0]
    options = source["option_definitions"]
    groups = {}
    defaults = set()
    for option in options:
        group = option["radio_group"]
        if group.startswith("Opener-Pot-"):
            groups.setdefault(group, []).append(option["id"])
            if option["default_checked"]:
                defaults.add(option["id"])
    if groups != {k: list(v) for k, v in EXPECTED_GROUPS.items()}:
        raise SourceAccessError("Option group graph differs from user-verified source")
    if defaults != EXPECTED_DEFAULTS:
        raise SourceAccessError("An opener potion default changed")
    choices = {c for values in EXPECTED_GROUPS.values() for c in values}
    if len(choices) != 12:
        raise AssertionError("Internal choice audit cardinality is invalid")

    # Source UI conditions alone do not prove a gameplay effect. Record their
    # occurrence and check exact choice IDs, without trying to infer their
    # Boolean semantics from arbitrary source text.
    occurrences = Counter(
        entry["expression"] for entry in source["conditional_expressions"]
    )
    source_choices_missing = choices - set(occurrences)
    if source_choices_missing:
        raise SourceAccessError("Some observed potion choices have no conditional evidence")

    step_tags = []
    raw = source["original_whml"]
    scopes, _ = _nested_scopes(raw)
    group_positions = sorted((o["position"], o["radio_group"])
                             for o in options
                             if o["radio_group"] in EXPECTED_GROUPS)
    for tag in TAG.finditer(raw):
        kind = tag.group(1).lower()
        if kind not in TYPES:
            continue
        attrs = _attrs(tag.group(2))
        spell = SPELL.match(tag.group(2))
        group = next((g for pos, g in reversed(group_positions)
                      if pos <= tag.start()), None)
        parents = [x["attributes"]["display-options"] for x in scopes
                   if x["start"] < tag.start() < x["end"]
                   and "display-options" in x["attributes"]]
        step_tags.append({
            "kind": kind,
            "group": group,
            "parents": parents,
            "spell": int(spell.group(1)) if spell else None,
            "condition": attrs.get("display-options"),
            "has_prepull": "prepull" in tag.group(2).lower(),
            "has_pull": attrs.get("text", "").lower() == "pull",
            "at": tag.start(),
        })
    choice_step_counts = {
        choice: sum(tag["condition"] == choice for tag in step_tags)
        for choice in choices
    }

    # A real *action* change is confirmed for this specific source by
    # checking the actual tagged ability and prepull versus pull timing.
    # We avoid translating display-option IDs into generic gameplay logic.
    storm_aoe = {
        key: [t for t in step_tags if t["condition"] == key
              and t["kind"] == "rt-step-group" and t["spell"] == 187874]
        for key in ("SB-OP-AOE-Reck", "SB-OP-AOE-LL", "SB-OP-AOE-LP")
    }
    if not (any(t["has_prepull"] for t in storm_aoe["SB-OP-AOE-Reck"])
            and all(any(t["has_pull"] for t in storm_aoe[key])
                    for key in ("SB-OP-AOE-LL", "SB-OP-AOE-LP"))):
        raise SourceAccessError("Stormbringer AoE potion-dependent action timing changed")

    # Compact technical trace for source-shape investigation only.
    # Markup tags that have multiple or nontrivial predicates as REVIEW.
    declared = {option["id"] for option in options}
    trace = {}
    for group, group_choices in EXPECTED_GROUPS.items():
        # Resolve exactly declared UI identifiers, preserving source case.
        hero_label = "SB-Master" if "-SB-" in group else "T-Master"
        fight_label = "Op-AoE" if group.endswith("-AOE") else "Op-ST"
        hero = next((x for x in declared if x.casefold() == hero_label.casefold()), None)
        fight = next((x for x in declared if x.casefold() == fight_label.casefold()), None)
        if hero is None or fight is None:
            raise SourceAccessError("Parent hero/fight option definitions changed")
        for choice in group_choices:
            selected = {choice, hero, fight}
            resolved = []
            unknown = 0
            unknown_details = []
            for t in step_tags:
                if t["group"] != group:
                    continue
                expressions = ([t["condition"]] if t["condition"] else []) + t["parents"]
                visible = source_scopes_visible(expressions, selected, declared)
                if visible is None:
                    unknown += 1
                    unknown_details.append({"spell": t["spell"], "conditions": expressions})
                    continue
                if not visible:
                    continue
                resolved.append([t["kind"], t["spell"],
                                 "pre" if t["has_prepull"] else
                                 "pull" if t["has_pull"] else "unspecified"])
            trace[choice] = {"technical_step_trace": resolved,
                             "uninterpreted_scope_count": unknown,
                             "uninterpreted_scope_signatures": unknown_details[:5]}
    non_potion_scopes = sorted({p for t in step_tags
                                for p in t["parents"]
                                if p not in choices})

    # Check ALL 12 actual conditional step paths, including alternate
    # branch and prepull differences. The source itself may change; this is
    # an explicit revision-locked regression, not auto-adapted gameplay logic.
    for choice, expected in EXPECTED_PATH_SUMMARY.items():
        item = trace[choice]
        if item["uninterpreted_scope_count"]:
            raise SourceAccessError("Unresolved source visibility expressions")
        steps = item["technical_step_trace"]
        observed = (
            len(steps),
            steps[0][1] if steps else None,
            sum(step[2] == "pre" for step in steps),
        )
        if observed != expected:
            raise SourceAccessError("Actual source choice path changed")
    path_summaries = {
        choice: {"step_count": len(info["technical_step_trace"]),
                 "prepull_marker_count": sum(
                     step[2] == "pre" for step in info["technical_step_trace"])}
        for choice, info in trace.items()
    }

    return {
        "source_locked": True,
        "source_scoped_paths_matched": len(EXPECTED_PATH_SUMMARY),
        "source_scoped_paths_metadata": path_summaries,
        "non_potion_scope_count": len(non_potion_scopes),
        "choice_groups": len(groups),
        "branch_count": len(choices),
        "distinct_choices_with_source_conditions": len(choices - source_choices_missing),
        "choices_with_direct_step_markup": sum(v > 0 for v in choice_step_counts.values()),
        "direct_step_tags": len(step_tags),
        "direct_conditional_step_tags": sum(bool(t["condition"]) for t in step_tags),
        "storm_aoe_crash_prepull_vs_pull_confirmed": True,
        "original_source_meaning_independently_verified": False,
        "whole_opener_state_transitions_verified": False,
        "all_twelve_action_sequences_verified": False,
        "automatic_publish_allowed": False,
    }


def main() -> None:
    try:
        with TemporaryDirectory() as tmp:
            folder = Path(tmp)
            result = run_specialization(
                "고양 주술사", folder, expected_guide_sha256=BASELINE
            )
            if result.get("matches_known_baseline") is not True:
                print("opener_review_status=source_changed_review_required")
                return
            source = json.loads(
                (folder / "editorial-evidence-private.json").read_text(encoding="utf-8")
            )
            report = inspect_original_opener_choices(source)
            print("opener_review_status=source_choice_evidence_consistent")
            for name, value in report.items():
                print("opener_review_" + name + "=" + json.dumps(value, ensure_ascii=True))
    except (SourceAccessError, ValueError, AssertionError):
        print("opener_review_status=access_or_structure_review_required")


if __name__ == "__main__":
    main()
