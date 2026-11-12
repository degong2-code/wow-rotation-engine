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
