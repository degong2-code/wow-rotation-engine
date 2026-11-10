"""Offline evidence-coverage and risk-priority tests."""
from copy import deepcopy
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
import json
import unittest

from engine.spell_triage import analyze, git_blob_sha1, read_evidence
from engine.public_data import BASE


class SpellTriageTests(unittest.TestCase):
    def test_evidence_fully_partitions_176_ids(self):
        queue=analyze()
        counts=queue["summary"]
        self.assertEqual(counts["unique_spell_ids"],176)
        self.assertEqual(counts["raw_name_records"],178)
        self.assertEqual(counts["api_name_matches"],150)
        self.assertEqual(counts["api_name_mismatches"],1)
        self.assertEqual(counts["api_404"],25)
        self.assertEqual(counts["review_queue_ids"],26)
        self.assertEqual(counts["other_errors"],0)
        self.assertTrue(queue["evidence_categories_complete"])

    def test_only_glacial_spike_blocks_rotation_references(self):
        q=analyze()
        self.assertEqual(q["summary"]["priority_rotation_spell_ids"],1)
        self.assertEqual(q["summary"]["affected_priority_rows"],4)
        self.assertEqual(q["summary"]["glossary_only_review_ids"],25)
        first=q["records"][0]
        self.assertEqual(first["spell_id"],199786)
        self.assertEqual(first["triage_priority"],"P0_rotation_reference")
        self.assertEqual(first["priority_rule_count"],4)
        self.assertEqual({r["guide_id"] for r in first["affected_priority_rules"]},{"frost"})
        self.assertTrue(all(r["v11_fragment_sha256"] for r in first["affected_priority_rules"]))

    def test_mismatch_is_held_without_name_mutation(self):
        q=analyze()
        r=next(x for x in q["records"] if x["spell_id"]==1249809)
        self.assertEqual(r["triage_priority"],"P1_name_disagreement")
        self.assertEqual(r["inherited_names_ko"],["마무리 작업"])
        self.assertEqual(r["observed_name_ko"],"끝맺음")
        self.assertTrue(r["glossary_only"])
        self.assertFalse(r["automatic_name_correction_allowed"])
        self.assertFalse(r["automatic_publish_allowed"])
        self.assertFalse(r["client_verified"])

    def test_no_review_item_is_approved(self):
        q=analyze()
        self.assertFalse(q["automatic_publish_allowed"])
        self.assertEqual(q["summary"]["verified_by_client"],0)
        self.assertTrue(all(x["review"]=="pending_client_or_secondary_evidence"
                            for x in q["records"]))

    def test_mismatched_duplicate_and_unclassified_ids_fail_closed(self):
        e=read_evidence()
        for mutation in ("duplicate","unknown","missing"):
            d=deepcopy(e)
            if mutation=="duplicate":
                d["observations_not_found_ids"].append(199786)
            if mutation=="unknown":
                d["observations_not_found_ids"][0]=999999999
            if mutation=="missing":
                d["observations_not_found_ids"].pop()
            with self.subTest(mutation=mutation):
                with self.assertRaisesRegex(ValueError,"partition"):
                    analyze(evidence=d)

    def test_authorization_gate_tampering_is_rejected(self):
        e=read_evidence()
        e["automatic_publish_allowed"]=True
        with self.assertRaisesRegex(ValueError,"provenance"):
            analyze(evidence=e)

    def test_wrong_locale_fails(self):
        e=read_evidence()
        e["locale"]="en_US"
        with self.assertRaisesRegex(ValueError,"provenance"):
            analyze(evidence=e)

    def test_missing_snapshot_origin_hash_fails(self):
        e=read_evidence()
        e["baseline_spells_git_blob_sha"]="0"*40
        with self.assertRaisesRegex(ValueError,"dictionary changed"):
            analyze(evidence=e)

    def test_wrong_mismatch_name_fails(self):
        e=read_evidence()
        e["observations_mismatched_names"][0]["inherited_name_ko"]="not V11"
        with self.assertRaisesRegex(ValueError,"unchanged inherited"):
            analyze(evidence=e)

    def test_changing_baseline_data_invalidates_evidence(self):
        with TemporaryDirectory() as td:
            dest=Path(td)/"public"
            copytree(BASE,dest)
            path=dest/"spells.json"
            d=json.loads(path.read_text(encoding="utf-8"))
            d["spells"][0]["name_en"] += " testing"
            path.write_text(json.dumps(d,ensure_ascii=False),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"dictionary changed"):
                analyze(base=dest)

    def test_reproducible_queue_and_git_blob_reference(self):
        q=analyze()
        self.assertEqual(json.dumps(q,sort_keys=True,ensure_ascii=False),
                         json.dumps(analyze(),sort_keys=True,ensure_ascii=False))
        evidence=read_evidence()
        self.assertEqual(git_blob_sha1((BASE/"spells.json").read_bytes()),
                         evidence["baseline_spells_git_blob_sha"])

    def test_contaminated_english_metadata_marked_for_review(self):
        q=analyze()
        r=next(x for x in q["records"] if x["spell_id"]==1249809)
        self.assertTrue(r["inherited_english_metadata_may_include_commentary"])


if __name__=="__main__":
    unittest.main()
