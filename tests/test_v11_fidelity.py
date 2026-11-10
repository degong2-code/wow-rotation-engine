"""Synthetic V11 fidelity checks. No user V11 text or images in GitHub."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from engine.v2.build import ROOT
from engine.v2.create_guide import render_arcane, validate_draft
from engine.v2.fidelity import (
    V11_COMPONENTS, REQUIRED_CREATE, audit_create_fragment,
    baseline_profile, structural_metrics,
)


class V11FidelityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.draft = json.loads(
            (ROOT / "content" / "new_guides" / "arcane.json").read_text(
                encoding="utf-8"
            )
        )

    def test_create_renders_canonical_v11_components(self):
        rendered = render_arcane(self.draft)
        report = audit_create_fragment(rendered["html"], self.draft)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["failures"], [])
        self.assertEqual(set(report["reused_v11_components"]), set(REQUIRED_CREATE))
        self.assertEqual(rendered["sections"], 9)
        self.assertEqual(report["structure"]["components"]["chapter-no"], 8)
        self.assertEqual(report["structure"]["components"]["quick-head"], 1)
        self.assertEqual(report["structure"]["components"]["glossary-row"], 12)
        self.assertEqual(report["structure"]["components"]["priority"], 4)
        self.assertGreaterEqual(report["structure"]["components"]["aside"], 4)

    def test_incomplete_description_schema_fails_closed(self):
        draft = deepcopy(self.draft)
        del draft["editorial"]
        with self.assertRaisesRegex(ValueError, "editorial contract"):
            validate_draft(draft)

    def test_missing_chapter_caution_fails_closed(self):
        draft = deepcopy(self.draft)
        draft["editorial"]["chapters"]["opener"]["caution"] = ""
        with self.assertRaisesRegex(ValueError, "context and exception"):
            validate_draft(draft)

    def test_missing_rotation_context_fails_closed(self):
        draft = deepcopy(self.draft)
        draft["rotation_groups"][0]["intro"] = ""
        with self.assertRaisesRegex(ValueError, "explanatory context"):
            validate_draft(draft)

    def test_uninformative_tooltip_fails_closed(self):
        draft = deepcopy(self.draft)
        draft["spells"][0]["hint"] = "?"
        with self.assertRaisesRegex(ValueError, "meaningful explanations"):
            validate_draft(draft)

    def test_review_state_cannot_be_promoted_by_fidelity(self):
        draft = deepcopy(self.draft)
        draft["editorial"]["cooldowns"][0]["review"] = "approved"
        with self.assertRaisesRegex(ValueError, "unreviewed cooldown"):
            validate_draft(draft)

    def test_layout_pass_does_not_imply_gameplay_or_evidence_pass(self):
        report = audit_create_fragment(render_arcane(self.draft)["html"], self.draft)
        self.assertTrue(report["editorial_review_required"])
        self.assertFalse(report["gameplay_accuracy_verified"])
        self.assertEqual(report["evidence_coverage"], {
            "rows_with_item_evidence": 0, "total_rows": 34,
        })
        self.assertFalse(self.draft["publication"]["automatic_publish_allowed"])

    def test_missing_presentation_component_is_detected(self):
        valid_html = render_arcane(self.draft)["html"]
        changed = valid_html.replace('class="quick-head"', 'class="bare-heading"', 1)
        report = audit_create_fragment(changed, self.draft)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("missing V11 component: quick-head", report["failures"])

    def test_seven_guide_profile_contains_only_counts(self):
        guide = (
            '<div class="manual-view" data-guide="one">'
            '<section class="overview" id="one-overview">'
            '<h2>합성 자료</h2></section></div>'
        )
        source = "".join(
            guide.replace('data-guide="one"', f'data-guide="g{i}"')
                 .replace('id="one-overview"', f'id="g{i}-overview"')
            for i in range(7)
        )
        profile = baseline_profile(source)
        self.assertEqual(profile["guide_count"], 7)
        self.assertEqual(len(profile["per_guide"]), 7)
        self.assertFalse(profile["source_text_exported"])
        self.assertNotIn("합성 자료", json.dumps(profile, ensure_ascii=False))
        with self.assertRaisesRegex(ValueError, "seven canonical"):
            baseline_profile(source + guide)


if __name__ == "__main__":
    unittest.main()
