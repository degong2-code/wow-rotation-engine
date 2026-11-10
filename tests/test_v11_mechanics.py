"""Synthetic-only tests of the V11 mechanics knowledge-to-HTML layer."""
from copy import deepcopy
from html import escape
import json
import unittest

from bs4 import BeautifulSoup

from engine.v2.build import ROOT
from engine.v2.create_guide import render_arcane
from engine.v2.mechanics import rich, validate


class V11MechanicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.draft = json.loads(
            (ROOT / "content" / "new_guides" / "arcane.json").read_text(encoding="utf8")
        )
        cls.mechanics = cls.draft["editorial"]["mechanics"]

    def test_v11_flows_are_linked_to_existing_rules_not_claimed_verified(self):
        result = validate(self.mechanics, self.draft)
        self.assertEqual(result["flows"], 3)
        self.assertEqual(result["comparisons"], 2)
        self.assertEqual(result["linked_rule_count"], 7)
        self.assertFalse(result["external_evidence_verified"])

    def test_original_v11_flow_and_comparison_classes_are_rendered(self):
        page = BeautifulSoup(render_arcane(self.draft)["html"], "html.parser")
        self.assertEqual(len(page.select("#arcane-basics p.sequence")), 2)
        self.assertEqual(len(page.select("#arcane-opener p.sequence")), 1)
        self.assertEqual(len(page.select("#arcane-basics table.comparison")), 2)
        self.assertEqual(len(page.select(".mechanic-flow ol.steps")), 3)
        self.assertEqual(len(page.select("#arcane-rotation tbody tr")), 34)
        self.assertEqual(len(page.select("#arcane-advanced [data-tip-id]")), 10)
        for section in ("overview", "pre", "basics", "opener",
                        "cooldowns", "advanced", "practice"):
            self.assertGreater(
                len(page.select("#arcane-" + section + " .spell.tip-trigger")),
                0, section
            )
        self.assertEqual(len(page.select("#arcane-basics table.comparison tbody tr")), 3)

    def test_no_icon_or_tooltip_is_guessed_for_unverified_spell(self):
        page = BeautifulSoup(render_arcane(self.draft)["html"], "html.parser")
        tokens = page.select('.spell[data-spell="arcane-salvo"]')
        self.assertTrue(tokens)
        self.assertTrue(all(not t.select_one("img") for t in tokens))

    def test_declared_inline_spell_token_is_escaped_and_linked(self):
        known = {"arcane-blast": {"ko": "합성 주문"}}
        def symbol(spell):
            return '<span class="spell" data-spell="arcane-blast">합성</span>'
        output = rich('앞 <b>태그</b> [[spell:arcane-blast]] 뒤', known, symbol)
        self.assertIn('&lt;b&gt;태그&lt;/b&gt;', output)
        self.assertIn('data-spell="arcane-blast"', output)
        self.assertNotIn('<b>태그</b>', output)

    def test_unknown_or_malformed_spell_tokens_are_rejected(self):
        spell_map = {"arcane-blast": {"ko": "합성"}}
        renderer = lambda spell: "<span>기술</span>"
        for text in ("[[spell:not-real]]", "[[spell:arcane-blast",
                     "[[spell:../unsafe]]", "[[spell:arcane-blast]]]]"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                rich(text, spell_map, renderer)

    def test_unknown_related_rule_fails_before_generation(self):
        bad = deepcopy(self.mechanics)
        bad["flows"][0]["related_rule_ids"] = ["arcane:missing:row-99"]
        with self.assertRaisesRegex(ValueError, "existing rule IDs"):
            validate(bad, self.draft)

    def test_unreviewed_mechanics_cannot_be_falsely_approved(self):
        bad = deepcopy(self.mechanics)
        bad["flows"][0]["review"] = "approved"
        with self.assertRaisesRegex(ValueError, "cannot be marked approved"):
            validate(bad, self.draft)

    def test_unknown_spell_in_flow_or_comparison_fails(self):
        for section in ("flows", "comparisons"):
            bad = deepcopy(self.mechanics)
            if section == "flows":
                bad["flows"][0]["steps"][0]["key"] = "unknown"
            else:
                bad["comparisons"][0]["rows"][0]["action_key"] = "unknown"
            with self.subTest(section=section), self.assertRaisesRegex(ValueError, "Unknown"):
                validate(bad, self.draft)

    def test_mechanism_explanation_is_not_validated_as_external_evidence(self):
        result = render_arcane(self.draft)
        audit = result["fidelity"]
        self.assertEqual(audit["evidence_coverage"]["rows_with_item_evidence"], 0)
        self.assertFalse(audit["gameplay_accuracy_verified"])
        self.assertFalse(audit["actionable_mechanisms"]["external_evidence_verified"])
        self.assertGreaterEqual(audit["actionable_mechanisms"]["contextual_spell_links"], 30)


if __name__ == "__main__":
    unittest.main()
