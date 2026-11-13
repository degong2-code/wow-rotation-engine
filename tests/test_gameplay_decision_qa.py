"""Small synthetic decisions covering precedence, ambiguity and source grounding."""
import json
import unittest

from engine.gameplay_decision_qa import assess_annotations, SCHEMA
from engine.source_editorial_packet import packet_from_html

WHML = ("[h2]Fictional rotation[/h2]"
        "[li]Spend on proc [span tooltip=proc]?</span>[/li]"
        "[li]Build if not proc[/li]"
        "[tooltip name=proc]Fictional stack and charge explanation[/tooltip]"
        "[h2]Fictional opener[/h2]"
        "[li]Before pull[/li][li]First action[/li][li]Second action[/li]")
PACKET = packet_from_html(
    "<!doctype html><html><script>WH.markup.printHtml("
    + json.dumps(WHML) + ',"guide-body",false);</script></html>'
)
DIGEST = PACKET["payloads"][0]["sha256"]


def reference(substring):
    start = WHML.index(substring)
    return [{"payload_sha256": DIGEST, "start": start, "end": start + len(substring)}]


def rule(ident, kind, action, *, rank=None, step=None, context=None,
         when=None, evidence=None, reason="Fictional source-supported rationale"):
    return {
        "id": ident, "kind": kind, "action": action,
        "rank": rank, "step": step, "context": context or {},
        "when": when or [], "reason": reason, "exceptions": [],
        "evidence": evidence if evidence is not None else reference("[li]Spend on proc"),
    }


def case(ident, action, *, state=None, context=None):
    return {"id": ident, "kind": "priority",
            "context": context or {"hero": "A", "targets": "single"},
            "state": state or {}, "expected_action": action}


def report(rules, cases):
    return assess_annotations(
        PACKET, {"schema_version": SCHEMA, "rules": rules, "cases": cases}
    )


class GameplayDecisionQATests(unittest.TestCase):
    def test_high_priority_proc_and_lower_filler_are_selectable(self):
        rules = [
            rule("proc", "priority", "Synthetic Spender", rank=1,
                 when=[{"field": "proc", "op": "eq", "value": True}]),
            rule("filler", "priority", "Synthetic Builder", rank=2),
        ]
        result = report(rules, [
            case("proc-active", "Synthetic Spender", state={"proc": True}),
            case("proc-inactive", "Synthetic Builder", state={"proc": False}),
        ])
        self.assertTrue(result["all_declared_cases_matched"])
        self.assertFalse(result["gameplay_meaning_verified"])
        self.assertFalse(result["automatic_publish_allowed"])

    def test_unknown_higher_priority_is_not_silently_skipped(self):
        rules = [
            rule("proc", "priority", "Synthetic Spender", rank=1,
                 when=[{"field": "proc", "op": "eq", "value": True}]),
            rule("filler", "priority", "Synthetic Builder", rank=2),
        ]
        result = report(rules, [case("unknown-proc", "Synthetic Builder")])
        self.assertEqual(result["case_results"][0]["result"], "underdetermined")
        self.assertIn("undecided_or_conflicting_decision_cases", result["blocker_codes"])

    def test_same_rank_conflict_detected_for_matching_state(self):
        rules = [
            rule("a", "priority", "Synthetic A", rank=1),
            rule("b", "priority", "Synthetic B", rank=1),
        ]
        result = report(rules, [case("both", "Synthetic A")])
        self.assertEqual(result["case_results"][0]["result"], "ambiguous")
        self.assertEqual(result["conflicting_identical_rule_pairs"], 1)

    def test_different_potion_contexts_are_not_a_conflict(self):
        rules = [
            rule("potion-a", "priority", "Synthetic A", rank=1,
                 context={"potion": "PotionA"}),
            rule("potion-b", "priority", "Synthetic B", rank=1,
                 context={"potion": "PotionB"}),
        ]
        result = report(rules, [
            case("a", "Synthetic A", context={"potion": "PotionA"}),
            case("b", "Synthetic B", context={"potion": "PotionB"}),
        ])
        self.assertEqual(result["case_outcome_counts"], {"matched": 2})

    def test_opener_sequence_differs_with_potion_choice(self):
        rules = [
            rule("a1", "opener", "Precast Synthetic", step=1,
                 context={"potion": "PotionA"}),
            rule("a2", "opener", "Drink Potion A", step=2,
                 context={"potion": "PotionA"}),
            rule("b1", "opener", "Drink Potion B", step=1,
                 context={"potion": "PotionB"}),
            rule("b2", "opener", "Cast Synthetic", step=2,
                 context={"potion": "PotionB"}),
        ]
        result = report(rules, [
            {"id": "a", "kind": "opener", "context": {"potion": "PotionA"},
             "state": {}, "expected_actions": ["Precast Synthetic", "Drink Potion A"]},
            {"id": "b", "kind": "opener", "context": {"potion": "PotionB"},
             "state": {}, "expected_actions": ["Drink Potion B", "Cast Synthetic"]},
        ])
        self.assertTrue(result["all_declared_cases_matched"])

    def test_opener_conflict_at_same_step_fails_closed(self):
        rules = [
            rule("a", "opener", "Synthetic A", step=1),
            rule("b", "opener", "Synthetic B", step=1),
        ]
        result = report(rules, [
            {"id": "opener", "kind": "opener", "context": {}, "state": {},
             "expected_actions": ["Synthetic A"]}
        ])
        self.assertEqual(result["case_results"][0]["result"], "ambiguous")

    def test_source_sha_mismatch_invalidates_rule(self):
        original = rule("a", "priority", "Synthetic A", rank=1)
        original["evidence"][0]["payload_sha256"] = "0" * 64
        result = report([original], [case("a", "Synthetic A")])
        self.assertEqual(result["invalid_evidence_rule_count"], 1)
        self.assertFalse(result["all_declared_cases_matched"])

    def test_evidence_out_of_bounds_invalidates_rule(self):
        original = rule("a", "priority", "Synthetic A", rank=1)
        original["evidence"][0]["end"] = 1000000
        result = report([original], [case("a", "Synthetic A")])
        self.assertEqual(result["invalid_evidence_rule_count"], 1)

    def test_no_cases_never_claims_coverage(self):
        result = report([rule("a", "priority", "Synthetic A", rank=1)], [])
        self.assertIn("no_decision_cases", result["blocker_codes"])
        self.assertFalse(result["all_declared_cases_matched"])

    def test_missing_expected_action_is_rejected(self):
        with self.assertRaises(ValueError):
            report([rule("a", "priority", "Synthetic A", rank=1)],
                   [{"id": "bad", "kind": "priority", "context": {},
                     "state": {}}])

    def test_numeric_threshold_branches(self):
        rules = [
            rule("high", "priority", "Use on 3", rank=1,
                 when=[{"field": "stacks", "op": "gte", "value": 3}]),
            rule("low", "priority", "Generate below 3", rank=2),
        ]
        result = report(rules, [
            case("below", "Generate below 3", state={"stacks": 2}),
            case("equal", "Use on 3", state={"stacks": 3}),
            case("above", "Use on 3", state={"stacks": 4}),
        ])
        self.assertTrue(result["all_declared_cases_matched"])


    def test_text_exception_never_silently_passes(self):
        overridden = rule("exception", "priority", "Synthetic A", rank=1)
        overridden["exceptions"] = ["When the synthetic object moves, do something else"]
        result = report([overridden], [case("exception", "Synthetic A")])
        self.assertEqual(result["unmodeled_exception_rule_count"], 1)
        self.assertIn("unmodeled_rule_exceptions", result["blocker_codes"])
        self.assertFalse(result["all_declared_cases_matched"])

    def test_unexercised_branch_is_reported_even_if_other_cases_match(self):
        rules = [
            rule("proc", "priority", "Spender", rank=1,
                 when=[{"field": "proc", "op": "eq", "value": True}]),
            rule("filler", "priority", "Builder", rank=2),
        ]
        result = report(rules, [case("inactive", "Builder", state={"proc": False})])
        self.assertEqual(result["case_outcome_counts"], {"matched": 1})
        self.assertEqual(result["unexercised_rule_count"], 1)
        self.assertIn("unexercised_rule_branches", result["blocker_codes"])

    def test_missing_opener_step_is_an_unknown_sequence(self):
        result = report([
            rule("first", "opener", "Synthetic A", step=1),
            rule("third", "opener", "Synthetic C", step=3),
        ], [{"id": "gap", "kind": "opener", "context": {}, "state": {},
             "expected_actions": ["Synthetic A", "Synthetic C"]}])
        self.assertEqual(result["case_results"][0]["result"], "underdetermined")

    def test_case_identifier_is_private_even_when_case_passes(self):
        result = report(
            [rule("a", "priority", "Synthetic A", rank=1)],
            [case("source-only-skill-name", "Synthetic A")]
        )
        self.assertTrue(result["all_declared_cases_matched"])
        output = json.dumps(result)
        self.assertNotIn("source-only-skill-name", output)
        self.assertEqual(result["case_results"][0]["case_index"], 1)

    def test_cli_uses_private_packet_without_echoing_whml(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from engine.gameplay_decision_qa import main
        from unittest.mock import patch
        from contextlib import redirect_stdout
        from io import StringIO
        with TemporaryDirectory() as temp:
            root = Path(temp)
            packet = root / "private-packet.json"
            annotation = root / "private-annotation.json"
            result_file = root / "audit.json"
            packet.write_text(json.dumps(PACKET), encoding="utf-8")
            annotation.write_text(json.dumps({
                "schema_version": SCHEMA,
                "rules": [rule("a", "priority", "Synthetic A", rank=1)],
                "cases": [case("private-case-identifier", "Synthetic A")]
            }), encoding="utf-8")
            with redirect_stdout(StringIO()) as captured:
                self.assertEqual(main([
                    "--source-packet", str(packet),
                    "--annotations", str(annotation),
                    "--report", str(result_file),
                ]), 0)
            self.assertTrue(result_file.exists())
            self.assertNotIn("private-case-identifier", captured.getvalue())
            self.assertNotIn("Fictional stack", result_file.read_text())


    def test_source_marker_must_occur_in_the_cited_action_span(self):
        invalid = rule("invalid", "priority", "Synthetic A", rank=1)
        invalid["action_source_marker"] = "[spell=999999]"
        result = report([invalid], [case("case", "Synthetic A")])
        self.assertEqual(result["invalid_action_marker_rule_count"], 1)
        self.assertIn("action_not_in_cited_source_span", result["blocker_codes"])
        valid = rule("valid", "priority", "Synthetic A", rank=1)
        valid["action_source_marker"] = "Spend on proc"
        result2 = report([valid], [case("case", "Synthetic A")])
        self.assertEqual(result2["invalid_action_marker_rule_count"], 0)

    def test_case_count_gate_for_real_source_reviews(self):
        annotations = {
            "schema_version": SCHEMA,
            "rules": [rule("r", "priority", "Synthetic A", rank=1)],
            "cases": [case("only-one", "Synthetic A")],
            "minimum_decision_cases": 6,
        }
        result = assess_annotations(PACKET, annotations)
        self.assertIn("insufficient_decision_cases", result["blocker_codes"])
        self.assertFalse(result["all_declared_cases_matched"])

    def test_shadowed_filler_does_not_count_as_exercised(self):
        rules = [
            rule("high", "priority", "Synthetic A", rank=1),
            rule("lower", "priority", "Synthetic B", rank=2),
        ]
        result = report(rules, [case("always-high", "Synthetic A")])
        self.assertEqual(result["unexercised_rule_count"], 1)
        self.assertIn("unexercised_rule_branches", result["blocker_codes"])


    def test_historical_tooltip_only_action_citation_must_not_pass(self):
        from copy import deepcopy
        bad = rule("historical", "priority", "Synthetic A", rank=1)
        body = PACKET["payloads"][0]["original_whml"]
        tooltip_start = body.index("[tooltip name=proc]")
        tooltip_end = body.index("[/tooltip]", tooltip_start) + len("[/tooltip]")
        # A different action is mentioned in the prose tooltip but not in the
        # first action row. Earlier generic validation could accept it.
        bad["action_source_marker"] = "Fictional stack"
        bad["evidence"].append({
            "payload_sha256": DIGEST,
            "start": tooltip_start, "end": tooltip_end
        })
        result = report([bad], [case("invalid", "Synthetic A")])
        self.assertEqual(result["invalid_action_marker_rule_count"], 1)
        self.assertIn("action_not_in_cited_source_span", result["blocker_codes"])
        positive = deepcopy(bad)
        positive["action_source_marker"] = "Spend on proc"
        result2 = report([positive], [case("valid", "Synthetic A")])
        self.assertEqual(result2["invalid_action_marker_rule_count"], 0)

    def test_missing_higher_state_is_not_evidence_that_lower_rule_wins(self):
        rules = [
            rule("high", "priority", "Synthetic A", rank=1,
                 when=[{"field": "proc", "op": "eq", "value": True}]),
            rule("low", "priority", "Synthetic B", rank=2),
        ]
        result = report(rules, [
            case("unknown-top-condition", "Synthetic B", state={}),
            case("certain-high", "Synthetic A", state={"proc": True}),
        ])
        self.assertEqual(result["unexercised_rule_count"], 1)
        self.assertIn("unexercised_rule_branches", result["blocker_codes"])
        self.assertEqual(result["case_results"][0]["result"], "underdetermined")

    def test_tied_conflicting_action_is_not_counted_as_tested_winner(self):
        rules = [
            rule("a", "priority", "Synthetic A", rank=1),
            rule("b", "priority", "Synthetic B", rank=1)
        ]
        result = report(rules, [case("tie", "Synthetic A")])
        self.assertEqual(result["unexercised_rule_count"], 2)
        self.assertEqual(result["case_results"][0]["result"], "ambiguous")

    def test_private_rule_text_not_in_public_report(self):
        rules = [rule("secret", "priority", "Copyrighted Fictional Ability", rank=1,
                      reason="A detailed source-only paragraph about the ability")]
        result = report(rules, [case("case-1", "Copyrighted Fictional Ability")])
        self.assertNotIn("Copyrighted Fictional Ability", json.dumps(result))
        self.assertNotIn("source-only paragraph", json.dumps(result))
        self.assertTrue(result["all_declared_cases_matched"])
        self.assertFalse(result["source_meaning_independently_verified"])



class SourceProjectionContractTests(unittest.TestCase):
    """One source decision list, multiple view tables: regression and controls."""

    @staticmethod
    def canonical(ident, rank, action, when=None, *, hero="A"):
        return {
            "id": ident, "kind": "priority", "rank": rank,
            "action": action, "context": {"hero": hero},
            "when": when or [], "condition_text": "Original condition for " + ident,
            "reason": "Original purpose for " + ident, "exceptions": [],
            "evidence": [{"payload_sha256": DIGEST, "start": 0, "end": 12}],
        }

    @staticmethod
    def condition(field, op, value):
        return {"field": field, "op": op, "value": value}

    def arcane_example(self):
        c = self.condition
        return [
            self.canonical("orb", 1, "Synthetic Orb", [c("charges", "lt", 3)]),
            self.canonical("pulse", 2, "Synthetic Pulse", [
                c("charges", "lt", 3), c("pulse_talent", "eq", True),
            ]),
            self.canonical("five-target", 3, "Synthetic Barrage", [
                c("target_count", "gte", 5), c("stacks", "gte", 12),
                c("orb_ready", "eq", True),
            ]),
            self.canonical("filler", 4, "Synthetic Filler"),
        ]

    def test_same_source_projects_to_st_and_aoe_without_rewriting(self):
        from engine.gameplay_decision_qa import project_priority_view, audit_priority_view
        original = self.arcane_example()
        st = project_priority_view(
            original, view_context={"hero": "A"}, min_targets=1, max_targets=1
        )
        aoe = project_priority_view(
            original, view_context={"hero": "A"}, min_targets=3
        )
        self.assertEqual([r["source_rule_id"] for r in st],
                         ["orb", "pulse", "filler"])
        self.assertEqual([r["source_rule_id"] for r in aoe],
                         ["orb", "pulse", "five-target", "filler"])
        self.assertEqual(st[0]["when"][0],
                         {"field": "charges", "op": "lt", "value": 3})
        self.assertEqual(aoe[2]["when"][0],
                         {"field": "target_count", "op": "gte", "value": 5})
        self.assertTrue(audit_priority_view(
            original, st, view_context={"hero": "A"},
            min_targets=1, max_targets=1,
        )["projection_preserved"])
        self.assertTrue(audit_priority_view(
            original, aoe, view_context={"hero": "A"}, min_targets=3
        )["projection_preserved"])

    def test_threshold_narrowing_from_under_three_to_zero_fails(self):
        from copy import deepcopy
        from engine.gameplay_decision_qa import project_priority_view, audit_priority_view
        original = self.arcane_example()
        st = project_priority_view(
            original, view_context={"hero": "A"}, min_targets=1, max_targets=1
        )
        bad = deepcopy(st)
        bad[0]["when"] = [{"field": "charges", "op": "eq", "value": 0}]
        bad[0]["condition_text"] = "No charges"
        result = audit_priority_view(
            original, bad, view_context={"hero": "A"},
            min_targets=1, max_targets=1,
        )
        self.assertFalse(result["projection_preserved"])
        self.assertIn("source_rule_changed_during_projection", result["blocker_codes"])
        self.assertFalse(result["gameplay_meaning_verified"])

    def test_omitted_conditional_and_extra_row_are_both_rejected(self):
        from engine.gameplay_decision_qa import project_priority_view, audit_priority_view
        original = self.arcane_example()
        aoe = project_priority_view(
            original, view_context={"hero": "A"}, min_targets=3
        )
        without_pulse = [r for r in aoe if r["source_rule_id"] != "pulse"]
        missing = audit_priority_view(
            original, without_pulse, view_context={"hero": "A"}, min_targets=3,
        )
        self.assertEqual(missing["missing_source_rule_count"], 1)
        extra = audit_priority_view(
            original, aoe + [aoe[0]], view_context={"hero": "A"}, min_targets=3,
        )
        self.assertEqual(extra["extra_source_rule_count"], 1)
        self.assertFalse(extra["projection_preserved"])

    def test_reordering_or_silent_reason_changes_are_rejected(self):
        from copy import deepcopy
        from engine.gameplay_decision_qa import project_priority_view, audit_priority_view
        original = self.arcane_example()
        rows = project_priority_view(
            original, view_context={"hero": "A"}, min_targets=3,
        )
        reordered = [rows[1], rows[0], *rows[2:]]
        order = audit_priority_view(
            original, reordered, view_context={"hero": "A"}, min_targets=3,
        )
        self.assertTrue(order["source_order_changed"])
        altered = deepcopy(rows)
        altered[0]["reason"] = "Different and ungrounded claim"
        changed = audit_priority_view(
            original, altered, view_context={"hero": "A"}, min_targets=3,
        )
        self.assertIn("source_rule_changed_during_projection", changed["blocker_codes"])
        self.assertNotIn("Synthetic Orb", json.dumps(changed))

    def test_other_hero_or_unrelated_spec_not_incorrectly_imported(self):
        from engine.gameplay_decision_qa import project_priority_view
        c = self.condition
        rules = [
            self.canonical("a-stacks", 1, "Synthetic Lightning", [
                c("stacks", "gte", 10),
            ], hero="A"),
            self.canonical("a-targets", 2, "Synthetic Chain", [
                c("target_count", "gte", 3), c("stacks", "gte", 9),
            ], hero="A"),
            self.canonical("b-unique", 1, "Synthetic Totem", hero="B"),
        ]
        single = project_priority_view(
            rules, view_context={"hero": "A"},
            min_targets=1, max_targets=1,
        )
        aoe = project_priority_view(
            rules, view_context={"hero": "A"}, min_targets=3,
        )
        b = project_priority_view(
            rules, view_context={"hero": "B"}, min_targets=1,
        )
        self.assertEqual([x["source_rule_id"] for x in single], ["a-stacks"])
        self.assertEqual([x["source_rule_id"] for x in aoe],
                         ["a-stacks", "a-targets"])
        self.assertEqual([x["source_rule_id"] for x in b], ["b-unique"])

    def test_unknown_view_context_and_complex_unmodeled_condition_fail_closed(self):
        from engine.gameplay_decision_qa import project_priority_view
        with self.assertRaisesRegex(ValueError, "lacks required source context"):
            project_priority_view(
                self.arcane_example(), view_context={}, min_targets=1,
            )
        with self.assertRaisesRegex(ValueError, "bounded list"):
            source = self.arcane_example()
            source[0]["when"] = {"OR": [
                {"field": "charges", "op": "lt", "value": 3},
                {"field": "stacks", "op": "gte", "value": 20},
            ]}
            project_priority_view(
                source, view_context={"hero": "A"}, min_targets=1,
            )


    def test_or_predicate_held_together_and_target_view_filtered(self):
        from engine.gameplay_decision_qa import project_priority_view, audit_priority_view
        c = self.condition
        rules = [self.canonical("prism", 1, "Synthetic Bolt"), self.canonical("filler", 2, "Synthetic Blast")]
        # Original: (14+ stacks AND any of 6 power/no proc/no 4pc) OR 2+ targets.
        rules[0].pop("when")
        rules[0]["when_any"] = [
            [c("stacks", "gte", 14), c("power", "gte", 6)],
            [c("stacks", "gte", 14), c("clearcasting", "eq", False)],
            [c("stacks", "gte", 14), c("tier4", "eq", False)],
            [c("target_count", "gte", 2)],
        ]
        single = project_priority_view(rules, view_context={"hero":"A"}, min_targets=1, max_targets=1)
        aoe = project_priority_view(rules, view_context={"hero":"A"}, min_targets=2)
        self.assertEqual(len(single), 2)
        self.assertEqual(len(aoe), 2)
        self.assertEqual(len(single[0]["when_any"]), 4)
        self.assertTrue(audit_priority_view(rules, single, view_context={"hero":"A"},min_targets=1,max_targets=1)["projection_preserved"])
        from copy import deepcopy
        broken=deepcopy(single)
        broken[0]["when_any"] = [sum(rules[0]["when_any"], [])] # WRONG AND
        result=audit_priority_view(rules,broken,view_context={"hero":"A"},min_targets=1,max_targets=1)
        self.assertIn("source_rule_changed_during_projection", result["blocker_codes"])

    def test_or_target_only_rule_drops_out_of_single_not_aoe(self):
        from engine.gameplay_decision_qa import project_priority_view
        c=self.condition
        rule=self.canonical("orb", 1, "Synthetic Orb")
        rule.pop("when")
        rule["when_any"] = [
            [c("target_count","gte",2),c("orb_mastery","eq",True)],
            [c("target_count","gte",5),c("orb_ready","eq",True)],
        ]
        self.assertEqual(project_priority_view([rule],view_context={"hero":"A"},min_targets=1,max_targets=1),[])
        self.assertEqual(len(project_priority_view([rule],view_context={"hero":"A"},min_targets=2)),1)


class PriorityShadowGeneralizationTests(unittest.TestCase):
    """Regression: a higher generic guard must not erase a lower exception."""

    @staticmethod
    def c(field, op, value):
        return SourceProjectionContractTests.condition(field, op, value)

    @staticmethod
    def r(ident, rank, action, when=None, *, hero="A"):
        return SourceProjectionContractTests.canonical(
            ident, rank, action, when, hero=hero
        )

    def audit(self, rules, *, hero="A", min_targets=1, max_targets=1):
        from engine.gameplay_decision_qa import audit_priority_shadowing
        return audit_priority_shadowing(
            rules, view_context={"hero": hero},
            min_targets=min_targets, max_targets=max_targets,
        )

    def test_survival_style_zero_stack_guard_masks_talent_exception(self):
        c, r = self.c, self.r
        rules = [
            r("upper-general", 1, "Synthetic Builder", [c("stacks", "eq", 0)]),
            r("lower-talent", 6, "Synthetic Finisher", [
                c("stacks", "eq", 0), c("special_talent", "eq", True)
            ]),
            r("filler", 7, "Synthetic Filler"),
        ]
        audit = self.audit(rules)
        self.assertEqual(audit["different_action_shadowed_view_ranks"], [2])
        self.assertTrue(audit["priority_shadow_review_required"])
        self.assertFalse(audit["source_meaning_verified"])
        self.assertFalse(audit["automatic_publish_allowed"])
        self.assertNotIn("Synthetic Finisher", json.dumps(audit))

    def test_valid_mutually_exclusive_proc_paths_are_not_flagged(self):
        c, r = self.c, self.r
        audit = self.audit([
            r("proc", 1, "Synthetic Spend", [c("proc", "eq", True)]),
            r("no-proc", 2, "Synthetic Build", [c("proc", "eq", False)]),
        ])
        self.assertEqual(audit["provably_shadowed_view_ranks"], [])

    def test_numeric_threshold_implication_is_one_directional(self):
        c, r = self.c, self.r
        audit = self.audit([
            r("range", 1, "Synthetic Range", [c("stacks", "lt", 3)]),
            r("zero", 2, "Synthetic Zero", [c("stacks", "eq", 0)]),
        ])
        self.assertEqual(audit["different_action_shadowed_view_ranks"], [2])
        audit = self.audit([
            r("zero", 1, "Synthetic Zero", [c("stacks", "eq", 0)]),
            r("range", 2, "Synthetic Range", [c("stacks", "lt", 3)]),
        ])
        self.assertEqual(audit["provably_shadowed_view_ranks"], [])

    def test_source_or_clause_preserved_in_implication(self):
        c, r = self.c, self.r
        a = r("upper", 1, "Synthetic Arcane One")
        a.pop("when")
        a["when_any"] = [[c("charges", "gte", 3)],
                         [c("talent", "eq", True)]]
        b = r("lower", 2, "Synthetic Arcane Two",
              [c("charges", "gte", 4)])
        self.assertEqual(
            self.audit([a, b])["different_action_shadowed_view_ranks"], [2]
        )

    def test_unmodeled_upper_exception_must_not_claim_proof(self):
        c, r = self.c, self.r
        upper = r("upper", 1, "Synthetic Command", [c("stacks", "eq", 0)])
        upper["exceptions"] = ["In a specific unmodeled phase, skip this"]
        lower = r("lower", 2, "Synthetic Spend", [c("stacks", "eq", 0)])
        self.assertEqual(
            self.audit([upper, lower])["provably_shadowed_view_ranks"], []
        )

    def test_target_view_and_other_hero_do_not_produce_false_alert(self):
        c, r = self.c, self.r
        rules = [
            r("aoe-only", 1, "Synthetic AOE",
              [c("target_count", "gte", 3)]),
            r("single", 2, "Synthetic Single"),
            r("other-hero", 1, "Synthetic Other", hero="B"),
        ]
        result = self.audit(rules)
        self.assertEqual(result["view_row_count"], 1)
        self.assertEqual(result["provably_shadowed_view_ranks"], [])

    def test_same_action_is_redundancy_not_different_action(self):
        c, r = self.c, self.r
        audit = self.audit([
            r("first", 1, "Synthetic Action", [c("stacks", "gte", 2)]),
            r("second", 2, "Synthetic Action", [c("stacks", "gte", 3)]),
        ])
        self.assertEqual(audit["same_action_shadowed_view_ranks"], [2])
        self.assertEqual(audit["different_action_shadowed_view_ranks"], [])
        self.assertFalse(audit["priority_shadow_review_required"])

    def test_same_action_guard_prevents_false_different_action_claim(self):
        r = self.r
        audit = self.audit([
            r("first", 1, "Synthetic A"),
            r("second", 2, "Synthetic B"),
            r("third", 3, "Synthetic A"),
        ])
        self.assertIn(3, audit["same_action_shadowed_view_ranks"])
        self.assertNotIn(3, audit["different_action_shadowed_view_ranks"])


if __name__ == "__main__":
    unittest.main()
