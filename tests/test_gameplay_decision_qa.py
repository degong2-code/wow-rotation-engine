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

    def test_private_rule_text_not_in_public_report(self):
        rules = [rule("secret", "priority", "Copyrighted Fictional Ability", rank=1,
                      reason="A detailed source-only paragraph about the ability")]
        result = report(rules, [case("case-1", "Copyrighted Fictional Ability")])
        self.assertNotIn("Copyrighted Fictional Ability", json.dumps(result))
        self.assertNotIn("source-only paragraph", json.dumps(result))
        self.assertTrue(result["all_declared_cases_matched"])
        self.assertFalse(result["source_meaning_independently_verified"])


if __name__ == "__main__":
    unittest.main()
