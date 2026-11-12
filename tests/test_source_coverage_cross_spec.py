"""Three synthetic cross-specialization UI patterns; no gameplay assertions."""
from copy import deepcopy
import unittest

from engine.source_coverage import SCHEMA, assess


def page(pattern):
    url = "https://example.invalid/" + pattern
    return {"schema_version": SCHEMA,
            "guide": {"specialization": "Synthetic pattern " + pattern,
                      "source_url": url, "patch": "synthetic",
                      "revision": "synthetic-2026"},
            "accesses": [{"id": "verified-html", "kind": "page_html",
                          "source_url": url, "patch": "synthetic",
                          "revision": "synthetic-2026"}],
            "states": []}


def insert(doc, path, controls=(), notes=True):
    doc["states"].append({
        "path": [{"control": k, "option": v} for k, v in path],
        "access_id": "verified-html", "inventory_checked": True,
        "choices": [{"control": key, "role": role, "options": values}
                    for key, role, values in controls],
        "entries": ([{"id": "synthetic_note", "kind": "notes",
                     "text": "Synthetic note, no real rotation content."}]
                    if notes else []),
    })


def dual_hero_with_opener():
    doc = page("two-hero-opener")
    insert(doc, [], [("hero", "decision", ["A", "B"])], False)
    for hero in ("A", "B"):
        insert(doc, [("hero", hero)],
               [("fight", "decision", ["single", "aoe"])], False)
        for fight in ("single", "aoe"):
            insert(doc, [("hero", hero), ("fight", fight)],
                   [("opener", "decision", ["overview", "sequence"])], False)
            for mode in ("overview", "sequence"):
                insert(doc, [("hero", hero), ("fight", fight), ("opener", mode)])
    return doc


def conditional_extra_option():
    doc = page("conditional-talent")
    insert(doc, [], [("hero", "decision", ["A", "B"])], False)
    insert(doc, [("hero", "A")],
           [("talent-toggle", "decision", ["on", "off"])], False)
    for toggle in ("on", "off"):
        insert(doc, [("hero", "A"), ("talent-toggle", toggle)])
    insert(doc, [("hero", "B")])
    return doc


def potion_example():
    doc = page("potion-timing")
    insert(doc, [], [("hero", "decision", ["A", "B"])], False)
    for hero in ("A", "B"):
        insert(doc, [("hero", hero)],
               [("potion", "illustrative", ["example-X", "example-Y"])])
    return doc


class CrossSpecializationPatternTests(unittest.TestCase):
    def test_multiple_hero_fight_openers_are_complete_if_declared(self):
        doc = dual_hero_with_opener()
        result = assess(doc)
        self.assertTrue(result["declared_coverage_candidate"])
        self.assertEqual(result["declared_states"], 15)
        self.assertFalse(result["real_site_completeness_verified"])

    def test_one_missing_aoe_opener_is_detected(self):
        doc = dual_hero_with_opener()
        doc["states"].pop()
        types = [x["type"] for x in assess(doc)["gaps"]]
        self.assertIn("unvisited_choice", types)

    def test_extra_toggle_only_for_one_hero_does_not_force_second_hero(self):
        doc = conditional_extra_option()
        self.assertTrue(assess(doc)["declared_coverage_candidate"])
        self.assertEqual(len(doc["states"]), 5)

    def test_nested_talent_off_state_must_be_visited(self):
        doc = conditional_extra_option()
        doc["states"] = [x for x in doc["states"]
                         if not any(y["option"] == "off" for y in x["path"])]
        self.assertIn("unvisited_choice", [x["type"] for x in assess(doc)["gaps"]])

    def test_consumable_example_does_not_require_two_more_openers(self):
        doc = potion_example()
        result = assess(doc)
        self.assertTrue(result["declared_coverage_candidate"])
        self.assertEqual(result["declared_states"], 3)

    def test_indexed_only_material_fails_real_site_completeness(self):
        doc = potion_example()
        doc["accesses"][0]["kind"] = "search_index"
        for x in doc["states"]:
            x["inventory_checked"] = False
        result = assess(doc)
        self.assertFalse(result["declared_coverage_candidate"])
        self.assertIn("inventory_not_checked", [g["type"] for g in result["gaps"]])
        self.assertFalse(result["real_site_completeness_verified"])

    def test_same_url_different_revision_does_not_mix(self):
        doc = potion_example()
        doc["accesses"].append({**deepcopy(doc["accesses"][0]),
                                "id": "old", "revision": "old"})
        doc["states"][1]["access_id"] = "old"
        result = assess(doc)
        self.assertIn("source_version_conflict", [g["type"] for g in result["gaps"]])

    def test_missing_tooltip_body_blocks_even_with_position(self):
        doc = potion_example()
        doc["states"][1]["entries"].append({
            "id": "candidate-tip", "kind": "tooltip", "text": None,
            "position": {"section": "synthetic priority", "near": "example"}})
        result = assess(doc)
        self.assertIn("missing_content", [x["type"] for x in result["gaps"]])


if __name__ == "__main__":
    unittest.main()
