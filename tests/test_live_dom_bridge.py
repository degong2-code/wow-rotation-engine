"""Fail-closed mapping of dynamic UI evidence to generic source-coverage draft."""
import json
import unittest

from engine.live_dom_bridge import public_audit, to_coverage_draft
from engine.source_coverage import assess


def synthetic_capture():
    a = {"index": 1, "kind": "tab", "dom_id": "heroA"}
    b = {"index": 2, "kind": "tab", "dom_id": "heroB"}
    def state(path, body, triggers=(), hover=()):
        return {"path": path,
                "observation": {
                    "body": body,
                    "controls": [], "tooltip_trigger_total": len(triggers),
                    "tooltip_triggers": list(triggers)},
                "hover_results": list(hover)}
    tip = {"index": 4, "id": "tip1", "row_id": "example-row", "near": "Synthetic Skill",
           "attributes": {"title": "Synthetic label"},
           "references": {"aria-describedby": [
               {"id": "two", "body": "A synthetic detailed tooltip."},
               {"id": "three", "body": "Second synthetic explanatory note."}
           ]}}
    hover = {"trigger_index": 4, "trigger": tip,
             "dynamic_tooltips": ["Synthetic runtime-hover detail."]}
    return {
        "schema_version": "live-dom-private-observation-v1",
        "source_url": "https://example.invalid/synthetic",
        "source_sha256": "a" * 64,
        "pending_state_count": 1,
        "pending_paths": [[b]],
        "depth_limited_state_count": 0,
        "states": [
            state([], "Synthetic guide introduction"),
            state([a], "Synthetic ability priority", [tip], [hover])
        ],
        "errors": []
    }


class LiveDOMBridgeTests(unittest.TestCase):
    def draft(self, capture=None):
        return to_coverage_draft(capture or synthetic_capture(),
                                 "Synthetic Spec", "synthetic-patch", "fixture-1")

    def test_root_child_and_pending_path_are_reported(self):
        led = self.draft()
        self.assertEqual(len(led["states"]), 2)
        gaps = assess(led)["gaps"]
        self.assertIn("unvisited_choice", [x["type"] for x in gaps])
        self.assertIn("inventory_not_checked", [x["type"] for x in gaps])
        self.assertFalse(assess(led)["declared_coverage_candidate"])
        self.assertEqual(led["accesses"][0]["html_sha256"], "a" * 64)

    def test_static_refs_and_runtime_hover_remain_separate(self):
        led = self.draft()
        tips = [e for e in led["states"][1]["entries"] if e["kind"] == "tooltip"]
        self.assertEqual(len(tips), 4)  # title, two references, and live hover
        self.assertTrue(any("Second synthetic" in t["text"] for t in tips))
        self.assertTrue(any("runtime-hover" in t["text"] for t in tips))
        self.assertEqual(assess(led)["declared_tooltips"], 4)

    def test_unhovered_tooltip_is_reported_as_missing_body(self):
        c = synthetic_capture()
        c["states"][1]["hover_results"] = []
        led = self.draft(c)
        self.assertIn("missing_content", {x["type"] for x in assess(led)["gaps"]})

    def test_truncated_tip_list_is_explicit_missing_content(self):
        c = synthetic_capture()
        c["states"][1]["observation"]["tooltip_trigger_total"] = 151
        led = self.draft(c)
        self.assertIn("missing_content", {x["type"] for x in assess(led)["gaps"]})

    def test_public_report_never_exposes_source_text(self):
        c = synthetic_capture()
        report = public_audit(c, self.draft(c))
        wire = json.dumps(report)
        self.assertNotIn("Synthetic runtime-hover detail", wire)
        self.assertNotIn("A synthetic detailed tooltip", wire)
        self.assertFalse(report["real_site_completeness_verified"])
        self.assertFalse(report["automatic_publish_allowed"])

    def test_no_root_is_recorded_as_missing(self):
        c = synthetic_capture()
        c["states"] = c["states"][1:]
        led = self.draft(c)
        self.assertIn("missing_content", {x["type"] for x in assess(led)["gaps"]})

    def test_unsupported_public_audit_input_rejected(self):
        with self.assertRaises(ValueError):
            self.draft({"schema_version": "live-dom-capture-report-v1"})

    def test_existing_capture_count_without_paths_never_passes(self):
        c = synthetic_capture()
        c.pop("pending_paths")
        led = self.draft(c)
        self.assertIn("unvisited_choice", {x["type"] for x in assess(led)["gaps"]})


if __name__ == "__main__":
    unittest.main()
