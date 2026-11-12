"""Generic coverage audit tests. Every string is synthetic, not WoW evidence."""
from copy import deepcopy
import json
import unittest

from engine.source_coverage import SCHEMA, assess


def fixture():
    url = "https://example.invalid/synthetic"
    source = {"schema_version": SCHEMA,
              "guide": {"specialization": "SYNTHETIC SPEC", "source_url": url,
                        "patch": "synthetic-patch", "revision": "synthetic-rev"},
              "accesses": [{"id": "page", "kind": "rendered_ui", "source_url": url,
                            "patch": "synthetic-patch", "revision": "synthetic-rev"}],
              "states": []}
    def state(path, choices, entries):
        source["states"].append({"path": [{"control": a, "option": b} for a, b in path],
                                 "access_id": "page", "inventory_checked": True,
                                 "choices": choices, "entries": entries})
    def decision(name, opts):
        return {"control": name, "role": "decision", "options": opts}
    def entry(name, kind="notes"):
        return {"id": name, "kind": kind, "text": "Synthetic content about " + name + "."}
    state([], [decision("hero", ["A", "B"])], [])
    for hero in ("A", "B"):
        state([("hero", hero)], [decision("fight", ["single", "aoe"])], [])
        for fight in ("single", "aoe"):
            entries = [entry(hero + fight)]
            choices = []
            if (hero, fight) == ("A", "single"):
                entries += [{"id": "tip", "kind": "tooltip", "text": "Synthetic tooltip body.",
                             "position": {"section": "priority", "near": "Example Skill"}}]
                choices = [{"control": "potion", "role": "illustrative",
                            "options": ["sample-1", "sample-2"]}]
            state([("hero", hero), ("fight", fight)], choices, entries)
    return source


class SourceCoverageTests(unittest.TestCase):
    def test_hero_fight_complete_without_potion_cartesian_product(self):
        result = assess(fixture())
        self.assertTrue(result["declared_coverage_candidate"])
        self.assertEqual(result["declared_states"], 7)
        self.assertEqual(result["declared_tooltips"], 1)
        self.assertFalse(result["real_site_completeness_verified"])
        self.assertFalse(result["automatic_publish_allowed"])

    def test_missing_subchoice(self):
        d = fixture()
        d["states"].pop()
        self.assertIn("unvisited_choice", {g["type"] for g in assess(d)["gaps"]})

    def test_missing_tooltip_body(self):
        d = fixture()
        d["states"][2]["entries"][1]["text"] = None
        self.assertIn("missing_content", {g["type"] for g in assess(d)["gaps"]})

    def test_tooltip_position_unknown_not_content_failure(self):
        d = fixture()
        d["states"][2]["entries"][1].pop("position")
        r = assess(d)
        self.assertTrue(r["declared_coverage_candidate"])
        self.assertEqual(len(r["tooltip_positions_unknown"]), 1)

    def test_unchecked_state(self):
        d = fixture()
        d["states"][2]["inventory_checked"] = False
        self.assertIn("inventory_not_checked", {g["type"] for g in assess(d)["gaps"]})

    def test_version_clash_even_at_same_url(self):
        d = fixture()
        d["accesses"].append({"id": "old", "kind": "search_index",
                              "source_url": d["guide"]["source_url"],
                              "patch": "outdated", "revision": "old"})
        d["states"][2]["access_id"] = "old"
        self.assertIn("source_version_conflict", {g["type"] for g in assess(d)["gaps"]})

    def test_only_search_index_never_verifies_real_ui(self):
        d = fixture()
        d["accesses"][0]["kind"] = "search_index"
        r = assess(d)
        self.assertTrue(r["declared_coverage_candidate"])
        self.assertFalse(r["real_site_completeness_verified"])
        self.assertTrue(any("Indirect" in x for x in r["warnings"]))

    def test_new_child_control(self):
        d = fixture()
        leaf = d["states"][2]
        leaf["choices"].append({"control": "advanced", "role": "decision",
                                "options": ["opened"]})
        d["states"].append({"path": leaf["path"] + [{"control": "advanced", "option": "opened"}],
                            "access_id": "page", "inventory_checked": True,
                            "choices": [], "entries": [{"id": "new", "kind": "advanced",
                                                       "text": "Synthetic hidden text."}]})
        self.assertTrue(assess(d)["declared_coverage_candidate"])

    def test_empty_terminal_state(self):
        d = fixture()
        d["states"][3]["entries"] = []
        self.assertIn("empty_terminal_state", {g["type"] for g in assess(d)["gaps"]})

    def test_orphan_state(self):
        d = fixture()
        d["states"][0]["choices"][0]["options"].remove("B")
        self.assertIn("orphan_state", {g["type"] for g in assess(d)["gaps"]})

    def test_source_text_not_output(self):
        d = fixture()
        text = d["states"][2]["entries"][1]["text"]
        r = assess(d)
        self.assertNotIn(text, json.dumps(r, ensure_ascii=False))
        self.assertFalse(r["source_text_in_report"])

    def test_duplicate_state_rejected(self):
        d = fixture()
        d["states"].append(deepcopy(d["states"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate state"):
            assess(d)

    def test_duplicate_path_control_rejected(self):
        d = fixture()
        d["states"][2]["path"].append({"control": "hero", "option": "B"})
        with self.assertRaisesRegex(ValueError, "same control"):
            assess(d)


if __name__ == "__main__":
    unittest.main()
