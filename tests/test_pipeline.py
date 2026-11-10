"""Offline tests; fixtures deliberately make no real gameplay claims."""
import unittest
from copy import deepcopy
from pathlib import Path

from engine.conditions import evaluate
from engine.pipeline import load, validate, build, canonical_sha

DATA = load(Path(__file__).resolve().parents[1] / "examples" / "synthetic.json")


class ConditionTests(unittest.TestCase):
    def test_unknown_is_not_false(self):
        self.assertIsNone(evaluate({"field": "target_count", "op": "gte", "value": 2}, {}))

    def test_numeric_condition(self):
        rule = {"field": "target_count", "op": "gte", "value": 2}
        self.assertTrue(evaluate(rule, {"target_count": 3}))
        self.assertFalse(evaluate(rule, {"target_count": 1}))

    def test_all_tristate(self):
        rule = {"all": [{"field": "target_count", "op": "gte", "value": 2},
                        {"field": "buff:example", "op": "eq", "value": True}]}
        self.assertIsNone(evaluate(rule, {"target_count": 3}))
        self.assertFalse(evaluate(rule, {"target_count": 1}))

    def test_any_tristate(self):
        rule = {"any": [{"field": "target_count", "op": "gte", "value": 2},
                        {"field": "buff:example", "op": "eq", "value": True}]}
        self.assertTrue(evaluate(rule, {"target_count": 3}))
        self.assertIsNone(evaluate(rule, {"target_count": 1}))

    def test_unsupported_field_rejected(self):
        with self.assertRaises(ValueError):
            evaluate({"field": "secret_token", "op": "eq", "value": 1}, {})

    def test_missing_operator_rejected(self):
        with self.assertRaises(ValueError):
            evaluate({"field": "hero", "value": "demo"}, {})


class PipelineTests(unittest.TestCase):
    def test_valid_demo_fixture(self):
        self.assertEqual(validate(DATA), [])

    def test_demo_needs_explicit_optin(self):
        with self.assertRaisesRegex(ValueError, "Synthetic"):
            build(DATA)

    def test_demo_build_text(self):
        page = build(DATA, allow_demo=True)
        self.assertIn("합성 데이터 데모", page)
        self.assertIn("가상 공격 A", page)
        self.assertEqual(page, build(DATA, allow_demo=True))

    def test_duplicate_rule_rejected(self):
        data = deepcopy(DATA)
        data["specs"][0]["rules"][1]["id"] = data["specs"][0]["rules"][0]["id"]
        self.assertTrue(any("duplicate rule" in e for e in validate(data)))

    def test_unverified_never_approved(self):
        data = deepcopy(DATA)
        data["specs"][0]["rules"][0]["review"] = "approved"
        self.assertTrue(any("cannot approve" in e for e in validate(data)))

    def test_deterministic_hash(self):
        self.assertEqual(canonical_sha(DATA), canonical_sha(deepcopy(DATA)))


if __name__ == "__main__":
    unittest.main()
