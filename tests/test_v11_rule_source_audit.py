"""Source mapping tests use published links/section names only, no copied guide text."""
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from engine.v2.build import ROOT
from engine.v2.rule_source_audit import audit_rule_sources
from engine.v2.create_guide import create_private_preview


class RuleSourceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder = ROOT / "content" / "new_guides"
        cls.draft = json.loads((folder / "arcane.json").read_text(encoding="utf-8"))
        cls.source_audit = json.loads(
            (folder / "arcane_rule_source_audit.json").read_text(encoding="utf-8")
        )

    def test_all_34_rules_have_source_section_locations_but_are_not_approved(self):
        report = audit_rule_sources(self.draft, self.source_audit)
        self.assertEqual(report["source_sections_mapped"], 34)
        self.assertEqual(report["total_rules"], 34)
        self.assertEqual(report["verified_rule_conditions"], 0)
        self.assertEqual(report["gameplay_approved_rules"], 0)
        self.assertFalse(report["safe_to_publish"])
        self.assertEqual(report["alignment_counts"], {
            "aligned": 16, "conditional_talent": 3,
            "fallback_only": 4, "needs_refinement": 6,
            "source_variation": 5,
        })

    def test_new_or_missing_rotation_row_requires_new_evidence(self):
        missing = deepcopy(self.source_audit)
        del missing["records"]["arcane:rotation:spellslinger-st:row-1"]
        with self.assertRaisesRegex(ValueError, "Missing/stale source mapping"):
            audit_rule_sources(self.draft, missing)
        extra = deepcopy(self.source_audit)
        extra["records"]["arcane:rotation:spellslinger-st:row-99"] = (
            extra["records"]["arcane:rotation:spellslinger-st:row-1"]
        )
        with self.assertRaisesRegex(ValueError, "Missing/stale source mapping"):
            audit_rule_sources(self.draft, extra)

    def test_revision_must_match_guide_patch(self):
        changed = deepcopy(self.source_audit)
        changed["patch"] = "12.1.7"
        with self.assertRaisesRegex(ValueError, "schema, guide or patch mismatch"):
            audit_rule_sources(self.draft, changed)

    def test_unknown_guide_section_cannot_be_used(self):
        changed = deepcopy(self.source_audit)
        changed["records"]["arcane:rotation:sunfury-st:row-1"]["source_section_refs"] = [
            "wowhead:imaginary"
        ]
        with self.assertRaisesRegex(ValueError, "Unknown source-section"):
            audit_rule_sources(self.draft, changed)

    def test_source_urls_must_be_known_guide_domains_and_https(self):
        for fake in ("http://www.wowhead.com/test",
                     "https://example.com/guide",
                     "https://user:password@www.wowhead.com/guide"):
            with self.subTest(url=fake):
                changed = deepcopy(self.source_audit)
                changed["source_catalog"]["wowhead"]["url"] = fake
                with self.assertRaisesRegex(ValueError, "approved HTTPS"):
                    audit_rule_sources(self.draft, changed)

    def test_source_mapping_cannot_automatically_approve_gameplay(self):
        changed = deepcopy(self.source_audit)
        changed["records"]["arcane:rotation:sunfury-st:row-1"]["full_condition_verified"] = True
        with self.assertRaisesRegex(ValueError, "Cannot silently approve"):
            audit_rule_sources(self.draft, changed)
        changed = deepcopy(self.source_audit)
        changed["records"]["arcane:rotation:sunfury-st:row-1"]["gameplay_approved"] = True
        with self.assertRaisesRegex(ValueError, "Cannot silently approve"):
            audit_rule_sources(self.draft, changed)

    def test_source_conflict_must_point_to_two_sections(self):
        changed = deepcopy(self.source_audit)
        changed["records"]["arcane:rotation:spellslinger-st:row-1"]["source_section_refs"] = [
            "wowhead:spellslinger"
        ]
        with self.assertRaisesRegex(ValueError, "two section references"):
            audit_rule_sources(self.draft, changed)

    def test_source_audit_cannot_be_used_as_publication_license(self):
        changed = deepcopy(self.source_audit)
        changed["policy"]["publication_allowed"] = True
        with self.assertRaisesRegex(ValueError, "cannot embed guide text or authorize"):
            audit_rule_sources(self.draft, changed)
        changed = deepcopy(self.source_audit)
        changed["policy"]["source_section_pointer_is_not_exact_quote_evidence"] = False
        with self.assertRaisesRegex(ValueError, "never masquerade"):
            audit_rule_sources(self.draft, changed)

    def test_private_html_builder_requires_evidence_audit_before_source_read(self):
        with TemporaryDirectory() as tmp:
            target = Path(tmp)
            invalid = deepcopy(self.source_audit)
            invalid["records"].pop("arcane:rotation:sunfury-st:row-1")
            invalid_file = target / "invalid.json"
            invalid_file.write_text(json.dumps(invalid, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Missing/stale source mapping"):
                create_private_preview(
                    target / "source-missing.html",
                    ROOT / "content" / "new_guides" / "arcane.json",
                    target / "generated.html",
                    evidence_path=invalid_file,
                    allow_legacy_review=True,  # Explicit historical audit test only.
                )
            self.assertFalse((target / "generated.html").exists())


if __name__ == "__main__":
    unittest.main()
