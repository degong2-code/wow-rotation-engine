"""Live official-data classification: audit evidence, not approval."""
import json
from pathlib import Path
import re
import unittest

from engine.spell_names import audit

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "content" / "review" / "blizzard-spell-20261110.json"


class OfficialEvidenceTests(unittest.TestCase):
    def test_live_observation_classifies_all_baseline_ids_once(self):
        doc=json.loads(EVIDENCE.read_text(encoding="utf-8"))
        spells=json.loads((ROOT/"content"/"public"/"spells.json").read_text(encoding="utf-8"))["spells"]
        known={x["spell_id"] for x in spells}
        matched=doc["observations_matched_existing_name_ids"]
        missing=doc["observations_not_found_ids"]
        mismatch=doc["observations_mismatched_names"]
        classified=matched+missing+[x["spell_id"] for x in mismatch]+doc["observations_other_error_ids"]
        self.assertEqual(len(spells),178)
        self.assertEqual(len(known),176)
        self.assertEqual(len(classified),176)
        self.assertEqual(len(classified),len(set(classified)))
        self.assertEqual(set(classified),known)
        self.assertEqual((len(matched),len(mismatch),len(missing)),(150,1,25))
        self.assertEqual(doc["baseline_name_records"],178)
        self.assertEqual(doc["total_requested_spell_ids"],176)

    def test_observation_does_not_modify_canonical_names(self):
        doc=json.loads(EVIDENCE.read_text(encoding="utf-8"))
        miss=doc["observations_mismatched_names"][0]
        baseline=json.loads((ROOT/"content"/"public"/"spells.json").read_text(encoding="utf-8"))["spells"]
        self.assertIn(miss["inherited_name_ko"],
                      [x["name_ko"] for x in baseline if x["spell_id"]==miss["spell_id"]])
        self.assertNotEqual(miss["inherited_name_ko"],miss["observed_name_ko"])
        self.assertEqual(miss["review"],"pending")
        self.assertFalse(doc["automatic_publish_allowed"])
        self.assertEqual(doc["all_rules_review"],"pending")
        self.assertFalse(audit()["publish_ready"])

    def test_provenance_is_explicit(self):
        doc=json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(doc["locale"],"ko_KR")
        self.assertEqual(doc["namespace"],"static-kr")
        self.assertTrue(doc["workflow_run_url"].startswith("https://github.com/"))
        self.assertRegex(doc["original_snapshot_sha256"],r"^[0-9a-f]{64}$")
        self.assertRegex(doc["original_audit_sha256"],r"^[0-9a-f]{64}$")
        self.assertRegex(doc["baseline_spells_git_blob_sha"],r"^[0-9a-f]{40}$")


if __name__=="__main__":
    unittest.main()
