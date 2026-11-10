"""No-network tests: partial candidates cannot become playable priorities."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from engine.condition_worklist import (
    DEFAULT, diagnose, load_overlay, original_rows, validate_ast,
    validate_overlay, worklist,
)
from engine.conditions import evaluate


class ConditionReviewTests(unittest.TestCase):
    def setUp(self):
        self.doc = load_overlay()

    def test_full_inventory_is_reconciled(self):
        all_rows=original_rows()
        self.assertEqual(len(all_rows),177)
        report=worklist()
        self.assertEqual(report["summary"]["total_rows"],177)
        self.assertEqual(report["summary"]["partial_candidate_pending"],2)
        self.assertEqual(report["summary"]["not_formalized"],175)
        self.assertEqual(report["summary"]["approved_full_conditions"],0)
        self.assertFalse(report["summary"]["publish_ready"])
        self.assertEqual(len(report["entries"]),177)
        self.assertTrue(all(not x["can_execute_rotation"] for x in report["entries"]))

    def test_candidate_sources_and_spells_match_baseline(self):
        self.assertEqual(validate_overlay(self.doc),[])
        source=original_rows()
        for item in self.doc["proposals"]:
            row=source[item["rule_id"]]
            self.assertEqual(row["fragment_sha256"],item["source_fragment_sha256"])
            self.assertEqual(row["spell_id"],item["spell_id"])

    def test_report_is_deterministic(self):
        self.assertEqual(
            json.dumps(worklist(),sort_keys=True,ensure_ascii=False),
            json.dumps(worklist(),sort_keys=True,ensure_ascii=False))

    def test_partial_predicate_truth_is_not_ability_recommendation(self):
        rid="frost:frost-rotation:table-1:row-6"
        result=diagnose(rid,{"hero":"spellslinger","debuffs":{"freezing":8}})
        self.assertTrue(result["syntactic_predicate_result"])
        self.assertIsNone(result["rotation_applicability"])
        self.assertFalse(result["can_recommend_ability"])
        self.assertFalse(result["source_verified"])

    def test_missing_game_context_is_unknown_not_false(self):
        rid="frost:frost-rotation:table-1:row-6"
        result=diagnose(rid,{"hero":"spellslinger"})
        self.assertIsNone(result["syntactic_predicate_result"])
        self.assertIsNone(result["rotation_applicability"])
        self.assertFalse(result["can_recommend_ability"])

    def test_false_partial_condition_still_not_full_decision(self):
        rid="frost:frost-rotation:table-1:row-6"
        result=diagnose(rid,{"hero":"spellslinger","debuffs":{"freezing":4}})
        self.assertFalse(result["syntactic_predicate_result"])
        self.assertIsNone(result["rotation_applicability"])
        self.assertFalse(result["can_recommend_ability"])

    def test_second_hero_threshold_is_distinct(self):
        rid="frost:frost-rotation:table-3:row-8"
        a=diagnose(rid,{"hero":"frostfire","debuffs":{"freezing":6}})
        b=diagnose(rid,{"hero":"frostfire","debuffs":{"freezing":12}})
        self.assertFalse(a["syntactic_predicate_result"])
        self.assertTrue(b["syntactic_predicate_result"])
        self.assertFalse(b["can_recommend_ability"])

    def test_modified_source_fragment_fails_closed(self):
        copied=deepcopy(self.doc)
        copied["proposals"][0]["source_fragment_sha256"]="f"*64
        self.assertTrue(any("original source fragment changed" in e
                            for e in validate_overlay(copied)))

    def test_modified_spell_fails_closed(self):
        copied=deepcopy(self.doc)
        copied["proposals"][0]["spell_id"]=999999
        self.assertTrue(any("referenced spell changed" in e
                            for e in validate_overlay(copied)))

    def test_duplicate_candidate_fails(self):
        copied=deepcopy(self.doc)
        copied["proposals"].append(deepcopy(copied["proposals"][0]))
        self.assertTrue(any("duplicate rule_id" in e
                            for e in validate_overlay(copied)))

    def test_premature_approval_fails(self):
        copied=deepcopy(self.doc)
        copied["proposals"][0]["review"]="approved"
        self.assertTrue(any("cannot be approved" in e
                            for e in validate_overlay(copied)))

    def test_full_candidate_cannot_skip_provenance_review(self):
        copied=deepcopy(self.doc)
        copied["proposals"][0]["completeness"]="full"
        self.assertTrue(any("only explicitly partial" in e
                            for e in validate_overlay(copied)))

    def test_publish_true_fails(self):
        copied=deepcopy(self.doc)
        copied["proposals"][0]["automatic_publish_allowed"]=True
        self.assertTrue(any("cannot be approved" in e
                            for e in validate_overlay(copied)))

    def test_unsupported_condition_field_rejected(self):
        with self.assertRaises(ValueError):
            validate_ast({"field":"password:token","op":"eq","value":1})

    def test_logical_node_with_extra_metadata_rejected(self):
        with self.assertRaises(ValueError):
            validate_ast({"all":[{"field":"hero","op":"eq","value":"test"}],
                          "source_verified":True})

    def test_comparison_type_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            validate_ast({"field":"debuff:freezing","op":"gte","value":"six"})

    def test_empty_ast_and_unbounded_composition_rejected(self):
        with self.assertRaises(ValueError):
            validate_ast({"all":[]})
        with self.assertRaises(ValueError):
            validate_ast({"any":[{"field":"hero","op":"eq","value":"x"}]*17})

    def test_partial_debuff_evaluation_is_tristate(self):
        node={"field":"debuff:freezing","op":"gte","value":6}
        self.assertIsNone(evaluate(node,{}))
        self.assertFalse(evaluate(node,{"debuffs":{"freezing":5}}))
        self.assertTrue(evaluate(node,{"debuffs":{"freezing":7}}))

    def test_missing_candidate_has_no_evaluation(self):
        rid="fire:rotation:table-1:row-1"
        result=diagnose(rid,{"hero":"sunfury"})
        self.assertFalse(result["candidate_found"])
        self.assertIsNone(result["syntactic_predicate_result"])
        self.assertFalse(result["can_recommend_ability"])

    def test_unknown_rule_id_is_rejected(self):
        with self.assertRaises(ValueError):
            diagnose("imaginary-rule",{})


if __name__ == "__main__":
    unittest.main()
