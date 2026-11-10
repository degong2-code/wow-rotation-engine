"""Offline tests of source-hash capture and review-only delta detection."""
from copy import deepcopy
from datetime import timedelta
import json
import unittest

from engine.source_snapshots import (
    INPUT_SCHEMA, capture, compare, normalized_digest, validate_snapshot,
)

URL = "https://www.wowhead.com/guide/classes/mage/fire/rotation-cooldowns-pve-dps"
R1 = "fire:rotation:table-1:row-1"
R2 = "fire:rotation:table-1:row-2"


def make_input(when="2026-11-10T10:00:00+00:00", body="Synthetic example sentence A, not game advice.",
               second=False):
    passages = [{"rule_id": R1, "text": body}]
    if second:
        passages.append({"rule_id": R2, "text": "Synthetic example B, not sourced game advice."})
    return {
        "schema_version": INPUT_SCHEMA, "guide_id": "fire", "source_url": URL,
        "captured_at": when, "passages": passages
    }


class SnapshotEvidenceTests(unittest.TestCase):
    def test_capture_does_not_persist_source_text(self):
        raw = make_input()
        snap = capture(raw)
        compact = json.dumps(snap, ensure_ascii=False)
        self.assertNotIn("Synthetic example sentence A", compact)
        self.assertFalse(snap["automatic_publish_allowed"])
        self.assertFalse(snap["external_source_verified"])
        self.assertFalse(snap["source_text_in_snapshot"])
        self.assertEqual(len(snap["observations"]), 1)
        validate_snapshot(snap)

    def test_normalization_ignores_formatting_only_differences(self):
        a = normalized_digest("Test   sentence\n number one.")
        b = normalized_digest("  Test sentence number one.  ")
        self.assertEqual(a, b)

    def test_unicode_nfc_normalization(self):
        self.assertEqual(normalized_digest("Caf\u00e9 test"), normalized_digest("Cafe\u0301 test"))

    def test_changed_text_requires_review_without_approval(self):
        a = capture(make_input())
        b = capture(make_input("2026-11-10T12:00:00+00:00", "Synthetic changed sentence, still not game advice."))
        d = compare(a,b)
        self.assertEqual(d["changed_observed_rules"],[R1])
        self.assertEqual(d["affected_rule_ids"],[R1])
        self.assertTrue(d["requires_human_review"])
        self.assertFalse(d["automatic_publish_allowed"])
        self.assertFalse(d["source_meaning_verified"])

    def test_formatting_only_change_is_not_a_content_change(self):
        a = capture(make_input(body="Synthetic  example\nsentence  A, not game advice."))
        b = capture(make_input("2026-11-10T12:00:00+00:00"))
        d = compare(a,b)
        self.assertEqual(d["changed_observed_rules"],[])
        self.assertEqual(d["unchanged_observed_rules"],[R1])
        self.assertFalse(d["requires_human_review"])

    def test_new_observation_is_not_source_article_addition(self):
        a = capture(make_input())
        b = capture(make_input("2026-11-10T12:00:00+00:00", second=True))
        d = compare(a,b)
        self.assertEqual(d["newly_observed_rules"],[R2])
        self.assertEqual(d["changed_observed_rules"],[])
        self.assertEqual(d["affected_rule_ids"],[R2])
        self.assertTrue(d["requires_human_review"])

    def test_missing_observation_is_not_source_article_deletion(self):
        a = capture(make_input(second=True))
        b = capture(make_input("2026-11-10T12:00:00+00:00"))
        d = compare(a,b)
        self.assertEqual(d["no_longer_observed_rules"],[R2])
        self.assertTrue(d["requires_human_review"])

    def test_unsupported_source_url_rejected(self):
        doc = make_input()
        doc["source_url"] = "https://example.com/clone"
        with self.assertRaisesRegex(ValueError, "source URL"):
            capture(doc)

    def test_unknown_rule_id_rejected(self):
        doc = make_input()
        doc["passages"][0]["rule_id"] = "fire:made-up"
        with self.assertRaisesRegex(ValueError, "unknown or cross-guide"):
            capture(doc)

    def test_duplicate_rule_id_rejected(self):
        doc = make_input()
        doc["passages"].append(deepcopy(doc["passages"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            capture(doc)

    def test_empty_text_rejected(self):
        doc = make_input()
        doc["passages"][0]["text"] = "  "
        with self.assertRaisesRegex(ValueError, "length"):
            capture(doc)

    def test_no_local_time_without_offset(self):
        doc = make_input("2026-11-10T12:00:00")
        with self.assertRaisesRegex(ValueError, "timezone"):
            capture(doc)

    def test_same_timestamp_not_a_new_version(self):
        a = capture(make_input())
        with self.assertRaisesRegex(ValueError, "later"):
            compare(a,a)

    def test_source_id_tampering_blocked(self):
        a = capture(make_input())
        b = deepcopy(a)
        b["observations"][0]["v11_fragment_sha256"] = "f"*64
        with self.assertRaisesRegex(ValueError, "locator changed"):
            validate_snapshot(b)

    def test_approval_escalation_in_snapshot_rejected(self):
        a = capture(make_input())
        a["automatic_publish_allowed"] = True
        with self.assertRaisesRegex(ValueError, "unverified source"):
            validate_snapshot(a)

    def test_text_spoof_added_to_snapshot_rejected(self):
        a = capture(make_input())
        a["observations"][0]["text"] = "This should not be present"
        with self.assertRaisesRegex(ValueError, "unknown observation properties"):
            validate_snapshot(a)

    def test_wrong_comparison_guide_rejected(self):
        a = capture(make_input())
        b = capture(make_input("2026-11-10T12:00:00+00:00"))
        b["guide_id"] = "frost"
        with self.assertRaisesRegex(ValueError, "registration mismatch"):
            compare(a,b)

    def test_unmatched_source_hash_rejected(self):
        a = capture(make_input())
        a["observations"][0]["observed_text_sha256"]="not-a-sha"
        with self.assertRaisesRegex(ValueError, "text hash"):
            validate_snapshot(a)


if __name__ == "__main__":
    unittest.main()
