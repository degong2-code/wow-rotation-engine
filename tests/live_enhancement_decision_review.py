"""User-verified 12.1.5 source case study: Stormbringer single-target.

Real guide HTML is fetched only during an opt-in public CI diagnostic, and is
never printed, uploaded, or committed. This is NOT live-game optimization proof.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from engine.gameplay_decision_qa import SCHEMA, assess_annotations
from engine.source_acquisition_pipeline import run_specialization
from engine.source_page_acquire import SourceAccessError
from engine.source_scoped_evidence import scoped_from_packet

SHA = "6657591171c36c79797b739b2248e37b9d967094e7d33e8dd799293283bd5dbe"
CONTEXT = {"hero": "Stormbringer", "targets": "single"}
SPELLS = [470057, 187874, 114051, 115356, 17364, 454009, 17364, 60103, 188196]
FLAGS = ("vb_ready", "crash_ready", "asc_ready", "asc_active",
         "windstrike_ready", "doom_winds_active", "stormstrike_ready",
         "tempest_ready", "tempest_proc", "bolt_ready", "lava_ready")

def eq(field, value):
    return {"field": field, "op": "eq", "value": value}

def stacks(amount):
    return {"field": "maelstrom_stacks", "op": "gte", "value": amount}

def build(packet):
    payloads = packet["payloads"]
    if len(payloads) != 1 or payloads[0]["sha256"] != SHA:
        raise SourceAccessError("Unverified source revision")
    whml = payloads[0]["original_whml"]
    begin = whml.index('[tooltip name="WindSB-ST"]')
    end = whml.index('[div display-options="T-Master"]', begin)
    rows = list(re.finditer(r"\[li\]([\s\S]*?)\[/li\]", whml[begin:end]))
    ids = []
    for row in rows:
        token = re.search(r"\[spell=(\d+)\]", row.group(1))
        if not token:
            raise SourceAccessError("A priority row lacks its action spell ID")
        ids.append(int(token.group(1)))
    if ids != SPELLS:
        raise SourceAccessError("The verified priority row signature has changed")

    def source_refs(row_index, tooltip=None):
        row = rows[row_index - 1]
        refs = [{"payload_sha256": SHA, "start": begin + row.start(),
                 "end": begin + row.end()}]
        if tooltip:
            if "tooltip=" + tooltip not in whml[refs[0]["start"]:refs[0]["end"]]:
                raise SourceAccessError("The tooltip is not referenced by its priority row")
            tip = re.search(r'\[tooltip name="' + re.escape(tooltip) +
                            r'"\][\s\S]*?\[/tooltip\]', whml)
            if tip is None:
                raise SourceAccessError("Source tooltip is missing")
            refs.append({"payload_sha256": SHA, "start": tip.start(), "end": tip.end()})
        if row_index == 6:
            note = re.search(r'\[li icon=angle-double-right\]Spend \[spell=187880\] '
                             r'on \[spell=454009\][\s\S]*?\[/li\]', whml)
            if note is None:
                raise SourceAccessError("Spender proc/fallback source note is missing")
            refs.append({"payload_sha256": SHA, "start": note.start(), "end": note.end()})
        return refs

    def rule(name, rank, action, row, conditions, reason, tip=None):
        refs = source_refs(row, tip)
        marker = f"[spell={action}]"
        if marker not in whml[refs[0]["start"]:refs[0]["end"]]:
            raise SourceAccessError("The asserted action is not in its priority row")
        return {"id": name, "kind": "priority", "rank": rank, "step": None,
                "context": dict(CONTEXT), "when": conditions,
                "action": f"spell:{action}", "action_source_marker": marker,
                "reason": reason, "exceptions": [], "evidence": refs}

    outside = [eq("asc_active", False), eq("doom_winds_active", False)]
    rules = [
        rule("r1", 1, 470057, 1, [eq("vb_ready", True)],
             "2세트 효과 발동과 쿨다운 정렬", "VBSB-ST"),
        rule("r2", 2, 187874, 2, [eq("crash_ready", True)],
             "버프 연계 및 쿨다운 사용", "CrashSB-ST"),
        rule("r3", 3, 114051, 3, [eq("asc_ready", True)],
             "원문의 3순위 쿨다운"),
        rule("r4", 4, 115356, 4, [eq("asc_active", True), eq("windstrike_ready", True)],
             "승천 중 GCD 및 재사용 대기시간 연계", "WindSB-ST"),
        rule("r5", 5, 17364, 5,
             [eq("doom_winds_active", True), eq("stormstrike_ready", True)],
             "파멸의 바람 중 타격"),
        rule("r6-proc", 6, 454009, 6,
             [stacks(10), eq("tempest_proc", True), eq("tempest_ready", True)] + outside,
             "10중첩 발동 효과 소모", "SpendSB-ST"),
        rule("r6-bolt", 6, 188196, 6,
             [stacks(10), eq("tempest_proc", False), eq("bolt_ready", True)] + outside,
             "10중첩 비발동 대체", "SpendSB-ST"),
        rule("r7", 7, 17364, 7, [eq("stormstrike_ready", True)],
             "상위 사용 기술이 없을 때 자원 생성용 타격"),
        rule("r8", 8, 60103, 8, [eq("lava_ready", True)],
             "상위 기술이 없을 때의 낮은 순위 타격"),
        rule("r9", 9, 188196, 9, [stacks(5), eq("bolt_ready", True)] + outside,
             "상위 기술이 없을 때 5중첩 이상 소모"),
    ]
    def state(**updates):
        result = {name: False for name in FLAGS}
        result["maelstrom_stacks"] = 0
        result.update(updates)
        return result
    scenarios = [
        ("cooldown-first", 470057, state(vb_ready=True, crash_ready=True)),
        ("crash-second", 187874, state(crash_ready=True)),
        ("asc-third", 114051, state(asc_ready=True)),
        ("asc-window", 115356, state(asc_active=True, windstrike_ready=True)),
        ("doom-window", 17364, state(doom_winds_active=True, stormstrike_ready=True)),
        ("ten-proc", 454009, state(maelstrom_stacks=10, tempest_proc=True,
                                    tempest_ready=True, bolt_ready=True)),
        ("ten-without-proc", 188196, state(maelstrom_stacks=10, bolt_ready=True)),
        ("ordinary-strike", 17364, state(stormstrike_ready=True)),
        ("lower-filler", 60103, state(lava_ready=True)),
        ("five-stacks", 188196, state(maelstrom_stacks=5, bolt_ready=True)),
        ("nine-stacks", 188196, state(maelstrom_stacks=9, bolt_ready=True)),
        ("avoid-manual-spend-in-asc", 115356,
         state(asc_active=True, windstrike_ready=True,
               maelstrom_stacks=10, tempest_proc=True, tempest_ready=True)),
        ("avoid-manual-spend-in-doom", 17364,
         state(doom_winds_active=True, stormstrike_ready=True,
               maelstrom_stacks=10, tempest_proc=True, tempest_ready=True)),
    ]
    cases = [{"id": ident, "kind": "priority", "context": dict(CONTEXT),
              "state": state0, "expected_action": f"spell:{action}"}
             for ident, action, state0 in scenarios]
    return {"schema_version": SCHEMA, "minimum_decision_cases": 6,
            "rules": rules, "cases": cases}


def review_historical_source_facts(packet):
    """Past editorial good/bad cases, verified against the SAME private WHML.

    This is source fact regression, NOT simulated DPS or proof of an optimal
    rotation. Its selectors rely on source provenance, not any fixed table
    markup in the generic engine.
    """
    whml = packet["payloads"][0]["original_whml"]
    scoped = scoped_from_packet(packet)["payloads"][0]
    indexed = {}
    for row in scoped["source_list_rows"]:
        containing = row.get("containing_list")
        if (row["kind"] != "source_list_item" or not containing
                or containing["tag"] != "ol"
                or row["inside_tooltip_definition"]):
            continue
        tabs = [tab["label_whml"] for tab in row["containing_tabs"]]
        if not tabs or tabs[-1] not in {"Single-Target Priority", "AoE Priority"}:
            continue
        for hero in ("SB-Master", "T-Master"):
            if not any(s["expression"] == hero
                       for s in row["active_display_scopes"]):
                continue
            key = (tabs[-1], hero, containing["start"])
            indexed.setdefault(key, []).append(row)

    def group(tab, hero, count):
        choices = [(loc, rows) for (tab0, hero0, loc), rows in indexed.items()
                   if tab0 == tab and hero0 == hero]
        if len(choices) != 1 or len(choices[0][1]) != count:
            raise SourceAccessError("Historic priority table shape changed")
        rows = choices[0][1]
        if [r["containing_list"]["ordinal"] for r in rows] != list(range(1, count + 1)):
            raise SourceAccessError("Historic priority row ordering is not preserved")
        return rows

    st = "Single-Target Priority"
    aoe = "AoE Priority"
    ts = group(st, "T-Master", 12)
    ta = group(aoe, "T-Master", 12)
    sa = group(aoe, "SB-Master", 10)
    ss = group(st, "SB-Master", 9)

    def spell(row):
        match = re.search(r"\[spell=(\d+)\]", row["original_whml_fragment"])
        if match is None:
            raise SourceAccessError("Historic source priority action is unidentifiable")
        return int(match.group(1))

    def require(condition):
        if not condition:
            raise SourceAccessError("Historic source fact conflicts with acquired guide")

    # F01/F02: Totemic ST and AoE reverse the ordering of the same two actions.
    require((spell(ts[2]), spell(ts[3])) == (60103, 197214))
    require((spell(ta[2]), spell(ta[3])) == (197214, 60103))
    require("[spell=201900]" in ts[2]["original_whml_fragment"]
            and "[spell=453405]" in ts[2]["original_whml_fragment"])
    require("[spell=201900]" in ta[3]["original_whml_fragment"]
            and "[spell=453405]" in ta[3]["original_whml_fragment"])

    # F03/F04: a proc at 10, otherwise a different action at 9+ in AoE.
    require(spell(sa[5]) == 454009 and "[b]10[/b]" in sa[5]["original_whml_fragment"])
    require(spell(sa[6]) == 188443 and "[b]9+[/b]" in sa[6]["original_whml_fragment"])
    require(spell(ss[5]) == 454009 and "[b]10[/b]" in ss[5]["original_whml_fragment"])

    # F05: a normal 10-stack consumer takes precedence over 5+ fallback.
    for rows, consumer in ((ts, 188196), (ta, 188443)):
        require(spell(rows[8]) == consumer and "[b]10[/b]" in rows[8]["original_whml_fragment"])
        require(spell(rows[11]) == consumer and "[b]5+[/b]" in rows[11]["original_whml_fragment"])

    # F06/F07/F08/F09: critical meaning resides in adjacent tooltip notes,
    # not merely the priority row. All are source-anchored; no interpretation
    # is generalized to a different specialization or a newer revision.
    tips = {t["name"]: t["body_whml"] for t in packet["payloads"][0]["tooltip_definitions"]}
    require("[spell=1250364]" in tips["SpendT-ST"]
            and "[spell=60103]" in tips["SpendT-ST"]
            and "[spell=201900]" in tips["SpendT-ST"])
    require("[spell=114051]" in tips["SpendSB-ST"]
            and "[spell=384352]" in tips["SpendSB-ST"]
            and "[spell=384444]" in tips["SpendSB-ST"])
    require("off the GCD" in tips["DoomT-ST"] and "[spell=1218047]" in tips["DoomT-ST"])
    require("GCD" in tips["DoomT-AoE"] and "[spell=187874]" in tips["DoomT-AoE"])

    # Historical §35 considered potion choices irrelevant. §38 corrected it.
    # The actual Stormbringer AoE opener changes *Crash Lightning* prepull
    # timing for Recklessness versus the two alternative potions.
    steps = re.findall(r"\[rt-step-group\s*=\s*187874\b([^\]]*)\]", whml)
    def has_step(choice, need):
        return any('display-options="' + choice + '"' in attrs and need in attrs
                   for attrs in steps)
    require(has_step("SB-OP-AOE-Reck", "prepull"))
    require(has_step("SB-OP-AOE-LL", 'text="Pull"'))
    require(has_step("SB-OP-AOE-LP", 'text="Pull"'))

    # This checks 10 grouped historical assertions and 4 different source
    # combinations. It deliberately does not claim a whole-rotation verdict.
    return {
        "historical_source_fact_groups_checked": 10,
        "hero_target_priority_combinations_checked": 4,
        "historic_potion_generalization_refuted": True,
        "source_scope_index_passed": True,
        "whole_rotation_validated": False,
        "gameplay_meaning_verified": False,
        "automatic_publish_allowed": False,
    }


def review(packet):
    annotations = build(packet)
    report = assess_annotations(packet, annotations)
    if not report["all_declared_cases_matched"]:
        raise AssertionError("Source-locked cases disagree: " +
                             json.dumps(report["blocker_codes"]))
    # Counterexample proves that the 13 passing cases do NOT cover all states.
    example = dict(annotations)
    example["minimum_decision_cases"] = 1
    example["cases"] = [{
        "id": "under-five-and-all-other-actions-unavailable",
        "kind": "priority", "context": dict(CONTEXT),
        "state": {**{key: False for key in FLAGS}, "maelstrom_stacks": 4},
        "expected_action": "unproven"
    }]
    gap = assess_annotations(packet, example)
    assert gap["case_results"][0]["result"] == "no_rule"
    past = review_historical_source_facts(packet)
    return {
        **past,
        "source_baseline_matched": True,
        "declared_cases_consistent": report["decision_case_count"],
        "source_anchored_rules": report["annotation_rule_count"],
        "incomplete_state_detected": True,
        "whole_rotation_validated": False,
        "gameplay_meaning_verified": False,
        "automatic_publish_allowed": False,
    }

def main():
    try:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            result = run_specialization("고양 주술사", root, expected_guide_sha256=SHA)
            if result["matches_known_baseline"] is not True:
                print("source_locked_case_study=revision_changed_review_required")
                return
            packet = json.loads((root / "editorial-evidence-private.json").read_text())
            record = review(packet)
            print("source_locked_case_study=subset_consistent")
            for key, value in record.items():
                print("case_study_" + key + "=" + str(value).lower())
    except (SourceAccessError, ValueError):
        print("source_locked_case_study=access_or_source_review_required")

if __name__ == "__main__":
    main()
