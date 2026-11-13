"""Positive/negative source visibility controls (not gameplay assertions)."""
import unittest

from engine.source_choice_visibility import (
    source_option_visible, source_scopes_visible,
)


class SourceVisibilityTests(unittest.TestCase):
    def setUp(self):
        self.declared = {"Hero-A", "Hero-B", "ST", "AOE",
                         "Pot-A", "Pot-B", "Pot-C"}

    def test_single_visible_choice(self):
        self.assertTrue(source_option_visible("Pot-A", {"Pot-A"}, self.declared))
        self.assertFalse(source_option_visible("Pot-A", {"Pot-B"}, self.declared))

    def test_or_choice_includes_two_alternatives(self):
        self.assertTrue(source_option_visible("Pot-A|Pot-B", {"Pot-B"}, self.declared))
        self.assertFalse(source_option_visible("Pot-A|Pot-B", {"Pot-C"}, self.declared))

    def test_nested_scopes_must_both_match(self):
        self.assertTrue(source_scopes_visible(["Hero-A", "ST", "Pot-A|Pot-B"],
                                              {"Hero-A", "ST", "Pot-B"},
                                              self.declared))
        self.assertFalse(source_scopes_visible(["Hero-A", "AOE", "Pot-A|Pot-B"],
                                               {"Hero-A", "ST", "Pot-B"},
                                               self.declared))

    def test_hero_or_does_not_force_one_hero(self):
        self.assertTrue(source_scopes_visible(["Hero-A|Hero-B", "ST"],
                                              {"Hero-B", "ST"},
                                              self.declared))

    def test_unknown_option_requires_review(self):
        self.assertIsNone(source_option_visible("Unknown", {"Pot-A"}, self.declared))
        self.assertIsNone(source_option_visible("Pot-A|Unknown",
                                                {"Pot-A"}, self.declared))

    def test_negated_potion_and_parenthesized_default_scope(self):
        self.assertTrue(source_option_visible("!Pot-B", {"Pot-A"}, self.declared))
        self.assertFalse(source_option_visible("!Pot-B", {"Pot-B"}, self.declared))
        default = "!(Pot-A)&!(Pot-B)&!(Pot-C)"
        self.assertFalse(source_option_visible(default, {"Pot-C"}, self.declared))
        self.assertTrue(source_option_visible(default, {"Hero-A"}, self.declared))

    def test_and_or_precedence_and_grouping(self):
        self.assertTrue(source_option_visible(
            "Hero-A&(ST|AOE)", {"Hero-A", "AOE"}, self.declared))
        self.assertFalse(source_option_visible(
            "Hero-B&(ST|AOE)", {"Hero-A", "AOE"}, self.declared))

    def test_unrecognized_logic_is_not_silently_accepted(self):
        for expression in ("Pot-A,Pot-B", "Pot-A||Pot-B", "",
                           "Pot-A^Pot-B", "Pot-A&", "!(Pot-A"):
            self.assertIsNone(source_option_visible(
                expression, {"Pot-A"}, self.declared))

    def test_unmatched_known_scope_can_safely_exclude_unknown_inner(self):
        self.assertFalse(source_scopes_visible(["AOE", "Unsupported"],
                                               {"ST", "Pot-A"}, self.declared))

    def test_unknown_matching_scope_stays_review(self):
        self.assertIsNone(source_scopes_visible(["ST", "Unsupported"],
                                                {"ST"}, self.declared))


if __name__ == "__main__":
    unittest.main()
