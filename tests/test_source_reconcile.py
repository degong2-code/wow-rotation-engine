"""Synthetic HTML versus captured-ledger reconciliation; no real guide content."""
import copy
import json
import unittest

from engine.source_coverage import SCHEMA as OBSERVATION_SCHEMA
from engine.source_reconcile import DECISIONS_SCHEMA, discover, reconcile
from engine.source_structure import inspect_html

HTML = (
    '<h1>Example</h1><button role="tab" aria-controls="p1">Single</button>'
    '<section id="p1" hidden><h2>Single Example</h2>'
    '<table><tr id="r1"><td><span aria-describedby="t1">?</span>'
    '<span title="Unique synthetic tooltip phrase.">?</span></td></tr></table>'
    '<div id="t1" hidden>First synthetic tooltip phrase.</div>'
    '</section><details><summary>Other Notes</summary>'
    '<p>Advanced synthetic notes text.</p></details>'
    '<script>WH.markup.printHtml('
    '"[tooltip name=x]WHML synthetic explanation[/tooltip][span tooltip=x]?[/span]",'
    '"guide-body", false);</script>'
)

def ledger():
    url = "https://example.invalid/guide"
    return {"schema_version": OBSERVATION_SCHEMA,
            "guide": {"specialization": "Synthetic Spec", "source_url": url,
                      "patch": "Synthetic", "revision": "A"},
            "accesses": [{"id": "local", "kind": "page_html", "source_url": url,
                          "patch": "Synthetic", "revision": "A",
                          "html_sha256": inspect_html(HTML)["source_sha256"]}],
            "states": [{"path": [], "access_id": "local", "inventory_checked": True,
                        "choices": [],
                        "entries": [{"id": "sample", "kind": "notes",
                                     "text": "Synthetic page notes unrelated to tooltip"}]}]}


class ReconciliationTests(unittest.TestCase):
    def structure(self):
        return inspect_html(HTML)

    def test_unmapped_contains_distinct_tip_references_and_panels(self):
        structure = self.structure()
        candidates, notes = discover(structure)
        self.assertEqual(len([x for x in candidates if x["kind"] == "tooltip"]), 2)
        self.assertEqual(len([x for x in candidates if x["kind"] == "whml_reference"]), 1)
        # Hidden t1 is already counted as its tooltip body; no double count.
        self.assertFalse(any(x["kind"] == "panel" and x.get("dom_id") == "t1"
                             for x in candidates))
        out = reconcile(structure, ledger())
        self.assertGreaterEqual(len(out["unmapped_candidates"]), 4)
        self.assertFalse(out["candidate_comparison_complete"])
        self.assertFalse(out["real_site_completeness_verified"])

    def test_explicit_mapping_requires_correct_entry_kind_and_body(self):
        structure = self.structure()
        candidates, _ = discover(structure)
        cid = next(x["id"] for x in candidates if x["kind"] == "tooltip")
        data = ledger()
        data["states"][0]["entries"].append({
            "id": "tip", "kind": "tooltip",
            "text": "First synthetic tooltip phrase.", "source_candidate_ids": [cid]})
        out = reconcile(structure, data)
        self.assertEqual(out["invalid_mappings"], [])
        self.assertEqual(out["mapped_candidate_count"], 1)

    def test_empty_text_cannot_hide_source_body_gap(self):
        structure = self.structure()
        cid = next(x["id"] for x in discover(structure)[0] if x["kind"] == "tooltip")
        data = ledger()
        data["states"][0]["entries"].append({
            "id": "tip", "kind": "tooltip", "text": "", "source_candidate_ids": [cid]})
        out = reconcile(structure, data)
        self.assertIn("missing_recorded_body", [x["issue"] for x in out["invalid_mappings"]])
        self.assertIn("missing_content", [x["type"] for x in out["declared_observation_gaps"]])

    def test_exact_unique_digest_automatic_matching(self):
        structure = self.structure()
        data = ledger()
        data["states"][0]["entries"].append({
            "id": "tip", "kind": "tooltip", "text": "Unique synthetic tooltip phrase."})
        out = reconcile(structure, data)
        self.assertEqual(out["auto_matched_candidate_ids"], [next(x["id"] for x in discover(structure)[0] if
                               x["kind"] == "tooltip" and x["subtype"] == "title")])
        self.assertEqual(out["exact_digest_matched_count"], 1)

    def test_wrong_type_and_unknown_id_are_not_accepted(self):
        structure = self.structure()
        data = ledger()
        data["states"][0]["entries"][0]["source_candidate_ids"] = ["tooltip:999:0"]
        result = reconcile(structure, data)
        self.assertIn("unknown_candidate", [x["issue"] for x in result["invalid_mappings"]])
        real_id = next(x["id"] for x in discover(structure)[0] if x["kind"] == "tooltip")
        data["states"][0]["entries"][0]["source_candidate_ids"] = [real_id]
        result = reconcile(structure, data)
        self.assertIn("tip_must_link_to_tooltip", [x["issue"] for x in result["invalid_mappings"]])

    def test_ignored_candidate_requires_reason_and_remains_visible(self):
        structure = self.structure()
        cid = discover(structure)[0][0]["id"]
        decisions = {"schema_version": DECISIONS_SCHEMA,
                     "not_relevant": [{"candidate_id": cid,
                                       "reason": "Site navigation only, not guide content"}]}
        result = reconcile(structure, ledger(), decisions)
        self.assertEqual(result["review_exclusion_count"], 1)
        self.assertNotIn(cid, [x["id"] for x in result["unmapped_candidates"]])
        decisions["not_relevant"][0]["reason"] = "no"
        with self.assertRaisesRegex(ValueError, "reason"):
            reconcile(structure, ledger(), decisions)

    def test_report_contains_no_original_explanation_body(self):
        out = reconcile(self.structure(), ledger())
        wire = json.dumps(out)
        self.assertNotIn("First synthetic tooltip phrase.", wire)
        self.assertNotIn("Advanced synthetic notes text.", wire)
        self.assertNotIn("WHML synthetic explanation", wire)
        self.assertFalse(out["source_text_in_report"])
        self.assertFalse(out["automatic_publish_allowed"])

    def test_truncated_inventory_never_completes(self):
        s = self.structure()
        s["candidate_lists_truncated"] = True
        out = reconcile(s, ledger())
        self.assertFalse(out["candidate_comparison_complete"])
        self.assertTrue(any("limit" in x for x in out["warnings"]))

    def test_nonlist_source_locator_rejected(self):
        structure = self.structure()
        data = ledger()
        data["states"][0]["entries"][0]["source_candidate_ids"] = "tooltip:1:0"
        with self.assertRaisesRegex(ValueError, "must be a list"):
            reconcile(structure, data)

    def test_different_html_cannot_be_reconciled_as_same_source(self):
        structure = inspect_html(HTML.replace("Example", "Different"))
        data = ledger()
        cid = next(x["id"] for x in discover(structure)[0] if x["kind"] == "tooltip")
        data["states"][0]["entries"].append({
            "id": "tip", "kind": "tooltip",
            "text": "First synthetic tooltip phrase.", "source_candidate_ids": [cid]})
        result = reconcile(structure, data)
        self.assertFalse(result["declared_source_binding_matches"])
        self.assertFalse(result["candidate_comparison_complete"])
        self.assertIn("source_binding_mismatch",
                      [x["issue"] for x in result["invalid_mappings"]])

    def test_search_index_does_not_prove_html_source(self):
        data = ledger()
        data["accesses"][0]["kind"] = "search_index"
        result = reconcile(self.structure(), data)
        self.assertFalse(result["declared_source_binding_matches"])
        self.assertFalse(result["candidate_comparison_complete"])

    def test_wrong_revision_keeps_observation_gap(self):
        s = self.structure()
        data = ledger()
        data["accesses"][0]["revision"] = "old"
        result = reconcile(s, data)
        self.assertIn("source_version_conflict",
                      [x["type"] for x in result["declared_observation_gaps"]])

    def test_distinct_duplicate_tooltips_require_separate_evidence(self):
        structure = inspect_html('<span data-hint-body="Synthetic first." '
                                 'aria-describedby="tip">?</span>'
                                 '<div id="tip" hidden>Second synthetic tip.</div>')
        candidates, _ = discover(structure)
        ids = [x["id"] for x in candidates if x["kind"] == "tooltip"]
        self.assertEqual(len(ids), 2)
        data = ledger()
        data["states"][0]["entries"].append({
            "id": "tip", "kind": "tooltip", "text": "Synthetic first.",
            "source_candidate_ids": [ids[0]]})
        result = reconcile(structure, data)
        self.assertEqual(len([x for x in result["unmapped_candidates"]
                              if x["kind"] == "tooltip"]), 1)

    def test_missing_position_does_not_create_new_content_gap(self):
        structure = self.structure()
        data = ledger()
        data["states"][0]["entries"].append({
            "id": "tip", "kind": "tooltip", "text": "Unique synthetic tooltip phrase."})
        result = reconcile(structure, data)
        self.assertFalse(any(x["type"] == "missing_content"
                             for x in result["declared_observation_gaps"]))
        self.assertIn("tooltip", [x["kind"] for x in result["unmapped_candidates"]])


if __name__ == "__main__":
    unittest.main()
