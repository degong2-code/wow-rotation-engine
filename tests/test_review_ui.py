"""Review-only dynamic UI / readiness checks. No game-content claims."""
import json
from copy import deepcopy
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
import unittest

from engine.public_data import BASE, load
from engine.review_audit import audit
from engine.review_ui import render, safe_id, target_label


class DynamicReviewUITests(unittest.TestCase):
    def test_render_deterministic_and_has_seven_guides(self):
        html=render()
        self.assertEqual(html,render())
        self.assertEqual(html.count('class="guide-panel"'),7)
        self.assertEqual(html.count('class="rotation-group"'),23 if False else 0)
        self.assertIn('data-select-guide="fire"',html)
        self.assertIn('data-select-guide="assassination"',html)
        self.assertIn('data-select-hero="deathstalker"',html)
        self.assertIn("Advanced Tips · 주제 색인",html)
        self.assertNotIn("<img",html)

    def test_all_priority_tables_have_scenario_and_provenance(self):
        html=render()
        self.assertEqual(html.count('class="card rotation-group"'),23)
        self.assertEqual(html.count('원본 근거 식별자'),177)
        self.assertIn('대상 수 미지정',html)
        self.assertIn('조건 미해석 · 검토 대기',html)

    def test_names_are_escaped(self):
        with TemporaryDirectory() as tmp:
            copied=Path(tmp)/"public"
            copytree(BASE,copied)
            f=copied/"rules"/"fire.json"
            d=json.loads(f.read_text(encoding="utf-8"))
            d["class_ko"]="<script>alert('unsafe')</script>"
            f.write_text(json.dumps(d,ensure_ascii=False),encoding="utf-8")
            html=render(copied)
            self.assertNotIn("<script>alert('unsafe')</script>",html)
            self.assertIn("&lt;script&gt;",html)

    def test_known_and_unknown_target_ranges(self):
        self.assertEqual(target_label({"target_min":None,"target_max":None}),"대상 수 미지정")
        self.assertEqual(target_label({"target_min":3,"target_max":None}),"3명 이상")
        self.assertEqual(target_label({"target_min":1,"target_max":2}),"1~2명")

    def test_reject_unsafe_ids(self):
        with self.assertRaises(ValueError):
            safe_id("foo bar")
        with self.assertRaises(ValueError):
            safe_id("bad<script>")

    def test_readiness_gate_fail_closed(self):
        result=audit()
        self.assertTrue(result["schema_ok"])
        self.assertFalse(result["publish_ready"])
        self.assertEqual(result["summary"]["priority_rows"],177)
        self.assertEqual(result["summary"]["uninterpreted_conditions"],177)
        self.assertEqual(result["summary"]["advanced_tips_without_full_explanations"],79)
        self.assertEqual(result["summary"]["unresolved_rule_spell_ids"],13)
        self.assertEqual(result["summary"]["spell_name_records_unverified"],178)


if __name__=="__main__":
    unittest.main()
