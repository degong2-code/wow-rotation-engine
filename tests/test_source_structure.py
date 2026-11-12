"""Synthetic multi-control and hidden-tooltip HTML structure regression tests."""
import json
import unittest
from engine.source_structure import inspect_html

HTML = """
<main><h2>Example specialization / synthetic</h2>
<button id="master" aria-controls="heroA" aria-expanded="false">Hero A</button>
<section id="heroA" hidden>
 <div role="tablist">
  <button role="tab" aria-controls="stPanel">Single</button>
  <button role="tab" aria-controls="aoePanel">AoE</button>
 </div>
 <section id="stPanel" hidden>
  <h3>Single rotation</h3>
  <table><tr id="r1"><td>Example Skill
   <button aria-describedby="tip1">?</button>
   <span data-hint-body="Other private synthetic tooltip body.">?</span>
   <span tooltip="missingName" tooltip2="tip2">?</span>
  </td></tr></table>
  <div id="tip1" hidden>Secret synthetic tooltip body with a priority exception.</div>
  <div id="tip2" hidden>Second synthetic tooltip body.</div>
 </section>
 <section id="aoePanel" hidden><h3>Area rotation</h3>
  <details><summary>Further details</summary><p>Hidden synthetic note</p></details>
  <select id="choice"><option>Example 1</option><option>Example 2</option></select>
 </section>
</section>
<script>/* WH.markup.printHtml is a marker, not executed */</script>
</main>
"""

class StructureTests(unittest.TestCase):
    def test_nested_hidden_and_controls_found_without_clicks(self):
        r = inspect_html(HTML)
        self.assertGreaterEqual(len(r["hidden_region_candidates"]), 5)
        self.assertTrue(any(x["id"] == "stPanel" for x in r["hidden_region_candidates"]))
        self.assertTrue(any(x["type"] == "details_summary" for x in r["control_candidates"]))
        self.assertTrue(any(x["options"] == ["Example 1", "Example 2"] for x in r["control_candidates"]))
        self.assertTrue(any(x["targets"] == ["stPanel"] and
                            x["targets_in_html"] == ["stPanel"] for x in r["control_candidates"]))
        self.assertEqual(r["embedded_script_markers"]["WH.markup.printHtml"], 1)

    def test_multiple_tooltip_refs_and_inline_content(self):
        r = inspect_html(HTML)
        descriptions = [d for x in r["tooltip_trigger_candidates"] for d in x["descriptions"]]
        kinds = {(d["attribute"], d["status"]) for d in descriptions}
        self.assertIn(("aria-describedby", "reference_body"), kinds)
        self.assertIn(("data-hint-body", "inline_body"), kinds)
        self.assertIn(("tooltip", "unresolved_reference"), kinds)
        self.assertIn(("tooltip2", "reference_body"), kinds)
        self.assertTrue(any(x["reference"] == "missingName" for x in r["unresolved_tooltip_references"]))

    def test_location_clues_preserved_without_row_certainty_claim(self):
        r = inspect_html(HTML)
        self.assertTrue(any(x["table_row"] == "r1" and x["section"] == "Single rotation"
                            for x in r["tooltip_trigger_candidates"]))
        self.assertFalse(r["live_ui_completeness_verified"])
        self.assertFalse(r["gameplay_meaning_verified"])

    def test_source_body_not_copied_to_report(self):
        r = inspect_html(HTML)
        report = json.dumps(r, ensure_ascii=False)
        self.assertNotIn("Secret synthetic tooltip body", report)
        self.assertNotIn("Hidden synthetic note", report)
        self.assertNotIn("Other private synthetic tooltip body", report)
        self.assertFalse(r["source_text_in_report"])

    def test_unresolved_target_is_reported(self):
        r = inspect_html('<button aria-controls="dynamicPanel">Go</button>')
        self.assertEqual(r["control_candidates"][0]["targets_not_in_html"], ["dynamicPanel"])
        self.assertFalse(r["live_ui_completeness_verified"])

    def test_plain_text_question_mark_candidate(self):
        r = inspect_html('<span>?</span>')
        self.assertEqual(r["tooltip_trigger_candidates"][0]["descriptions"][0]["status"],
                         "body_not_found_in_static_html")

    def test_duplicate_identifiers(self):
        r = inspect_html('<div id="duplicate"></div><div id="duplicate"></div>')
        self.assertEqual(r["duplicate_ids"], ["duplicate"])

    def test_limits_and_input_types(self):
        with self.assertRaises(ValueError):
            inspect_html(22)
        with self.assertRaises(ValueError):
            inspect_html("X" * (12 * 1024 * 1024 + 1))


if __name__ == "__main__":
    unittest.main()
