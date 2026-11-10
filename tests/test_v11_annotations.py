"""Synthetic-only V11 note-marker and existing table presentation tests."""
from copy import deepcopy
from html.parser import HTMLParser
import json
import unittest

from bs4 import BeautifulSoup

from engine.v2.build import ROOT
from engine.v2.annotations import render_legend, render_note, validate_notes
from engine.v2.create_guide import render_arcane, validate_draft


class V11AnnotationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.draft = json.loads(
            (ROOT / "content" / "new_guides" / "arcane.json").read_text(
                encoding="utf-8"
            )
        )
        cls.html = render_arcane(cls.draft)["html"]
        cls.soup = BeautifulSoup(cls.html, "html.parser")

    def test_annotation_contract_targets_existing_rules_and_mechanics(self):
        notes = validate_notes(self.draft)
        self.assertEqual(len(notes), 6)
        self.assertEqual(sum(kind == "rule" for kind, _ in notes), 4)
        self.assertEqual(sum(kind == "mechanic" for kind, _ in notes), 2)
        self.assertEqual(sum(n["marker"] == "!" for n in notes.values()), 3)
        self.assertEqual(sum(n["marker"] == "?" for n in notes.values()), 3)

    def test_original_v11_tooltip_classes_and_accessibility_are_used(self):
        markers = self.soup.select("#guide-arcane button.note-marker.tip-trigger")
        # Four priority rows + two mechanics + one quick-reference duplication.
        self.assertEqual(len(markers), 7)
        self.assertTrue(all(b.get("type") == "button" for b in markers))
        self.assertTrue(all(b.get("aria-label") for b in markers))
        self.assertTrue(all(b.get("data-hint-title") for b in markers))
        self.assertTrue(all(b.get("data-hint-body") for b in markers))
        targets = {x.get("id") for x in self.soup.select("#guide-arcane [id]")}
        self.assertTrue(all(
            b["data-hint-href"].startswith("#arcane-")
            and b["data-hint-href"][1:] in targets for b in markers
        ))
        self.assertTrue(all(
            ("critical" in b.get("class", [])) == (b.get_text(strip=True) == "!")
            for b in markers
        ))

    def test_rule_note_is_located_in_matching_priority_row(self):
        marker = self.soup.select_one(
            'tr[data-rule-id="arcane:rotation:spellslinger-st:row-1"]'
            ' button.note-marker'
        )
        self.assertIsNotNone(marker)
        self.assertEqual(marker.get_text(strip=True), "!")
        self.assertEqual(marker["data-note"], "arcane-tier4-fork")

    def test_note_appears_in_original_quick_reference_table(self):
        marker = self.soup.select_one(
            '#arcane-overview .overview-table [data-note="arcane-tier4-fork"]'
        )
        self.assertIsNotNone(marker)
        self.assertEqual(marker.get_text(strip=True), "!")

    def test_mechanic_note_appears_in_flow_or_comparison_heading(self):
        detailed = self.soup.select_one(
            '.mechanic-flow[data-mechanic-id="clearcasting-salvo-window"]'
            ' h3 button.note-marker'
        )
        critical = self.soup.select_one(
            '.mechanic-comparison[data-mechanic-id="hero-barrage-thresholds"]'
            ' h3 button.note-marker.critical'
        )
        self.assertIsNotNone(detailed)
        self.assertIsNotNone(critical)
        self.assertEqual(detailed.get_text(strip=True), "?")
        self.assertEqual(critical.get_text(strip=True), "!")

    def test_legend_explains_question_and_warning_markers(self):
        legend = self.soup.select_one("#arcane-overview .tiny-rule .note-key")
        self.assertIsNotNone(legend)
        self.assertEqual(legend.get_text(strip=True), "?")
        self.assertIsNotNone(
            self.soup.select_one("#arcane-overview .note-key.important")
        )
        self.assertIn("클릭하면 설명 고정", render_legend())

    def test_new_comparison_uses_original_v11_table_styles(self):
        comparisons = self.soup.select("#arcane-basics table.comparison")
        self.assertEqual(len(comparisons), 2)
        self.assertTrue(all(
            table.parent and "table-scroll" in table.parent.get("class", [])
            for table in comparisons
        ))
        self.assertEqual(len(comparisons[1].select("tbody tr")), 4)
        self.assertEqual(
            [th.get_text(" ", strip=True) for th in comparisons[1].select("th")],
            ["상황", "판단 조건", "행동 후보", "이유"],
        )

    def test_unknown_note_target_is_rejected(self):
        draft = deepcopy(self.draft)
        draft["editorial"]["annotations"]["notes"][0]["target_id"] = "unknown"
        with self.assertRaisesRegex(ValueError, "existing rule/mechanism"):
            validate_draft(draft)

    def test_duplicate_note_target_is_rejected(self):
        draft = deepcopy(self.draft)
        first, second = draft["editorial"]["annotations"]["notes"][:2]
        second["target_id"] = first["target_id"]
        with self.assertRaisesRegex(ValueError, "Duplicate V11 note target"):
            validate_draft(draft)

    def test_javascript_href_or_external_anchor_is_rejected(self):
        draft = deepcopy(self.draft)
        draft["editorial"]["annotations"]["notes"][0]["detail_anchor"] = (
            'javascript:alert(1)'
        )
        with self.assertRaisesRegex(ValueError, "detail anchor"):
            validate_draft(draft)

    def test_unknown_note_severity_or_unreviewed_status_is_rejected(self):
        for key, bad_value, error in (
            ("marker", "*", "notes use"),
            ("review", "approved", "cannot be approved"),
        ):
            draft = deepcopy(self.draft)
            draft["editorial"]["annotations"]["notes"][0][key] = bad_value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, error):
                validate_draft(draft)

    def test_note_text_is_html_escaped(self):
        note = deepcopy(self.draft["editorial"]["annotations"]["notes"][0])
        note["body"] = '확인 <img src=x onerror=alert(1)> & 주의'
        rendered = render_note(note)
        self.assertNotIn("<img", rendered)
        self.assertNotIn('onerror="', rendered)
        self.assertIn("&lt;img", rendered)
        self.assertIn("&amp;", rendered)

    def test_gameplay_remains_review_pending_despite_presentational_pass(self):
        report = render_arcane(self.draft)["fidelity"]
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["gameplay_accuracy_verified"])
        self.assertEqual(
            report["evidence_coverage"],
            {"rows_with_item_evidence": 0, "total_rows": 34},
        )


if __name__ == "__main__":
    unittest.main()
