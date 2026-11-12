"""Retrospective good/bad controls without publishing any old guide content."""
import unittest
from hashlib import sha256

from engine.historical_html_audit import compare_historical_html


def sample(chapters=(2, 3), added=False):
    def guide(gid, count):
        sections = "".join(
            '<section id="' + gid + "-s" + str(i) +
            '"><h2>Historical synthetic heading</h2><p>Old source ' +
            str(i) + "</p></section>" for i in range(count)
        )
        return '<div class="manual-view" data-guide="' + gid + '" id="guide-' + gid + '">' \
            + "<div class=\"intro\">Intro</div>" + sections + '<footer>End</footer></div>'
    return (
        '<!doctype html><html><main>' +
        "".join(guide("g"+str(i), n) for i, n in enumerate(chapters, 1)) +
        (guide("g-new", 4) if added else "") +
        "</main></html>"
    ).encode()


class HistoricalHTMLAuditTests(unittest.TestCase):
    def test_create_adds_guide_without_changing_old_views(self):
        old, updated = sample(), sample(added=True)
        result = compare_historical_html(old, updated,
                                         expected_baseline_sha256=sha256(old).hexdigest())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["added_guide_count"], 1)
        self.assertEqual(result["unchanged_protected_guides"], 2)
        self.assertEqual(result["protected_section_count"], 5)
        self.assertFalse(result["content_accuracy_verified"])

    def test_update_whitelist_lets_one_section_change(self):
        old = sample()
        changed = old.replace(b"Old source 0", b"Revised synthetic content 0", 1)
        no_permission = compare_historical_html(old, changed)
        self.assertEqual(no_permission["status"], "FAIL")
        permission = compare_historical_html(
            old, changed, allowed_section_changes={"g1": ["g1-s0"]}
        )
        self.assertEqual(permission["status"], "PASS")
        self.assertEqual(permission["allowed_section_edits_observed"], 1)

    def test_update_with_unrelated_section_change_is_rejected(self):
        old = sample()
        changed = old.replace(b"Old source 1", b"Unapproved change", 1)
        r = compare_historical_html(
            old, changed, allowed_section_changes={"g1": ["g1-s0"]}
        )
        self.assertEqual(r["status"], "FAIL")
        self.assertTrue(r["failure_categories"])

    def test_changing_outside_sections_is_not_hidden_by_section_whitelist(self):
        old = sample()
        changed = old.replace(b"<footer>End</footer>", b"<footer>Edited</footer>", 1)
        r = compare_historical_html(
            old, changed, allowed_section_changes={"g1": ["g1-s0"]}
        )
        self.assertEqual(r["status"], "FAIL")

    def test_missing_guide_and_missing_section_are_rejected(self):
        old = sample()
        missing_guide = old.replace(b'data-guide="g1"', b'data-guide="wrong"', 1)
        result = compare_historical_html(old, missing_guide)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("removed_protected_guide", result["failure_categories"])
        missing_section = old.replace(b'id="g1-s0"', b'id="changed-section"', 1)
        result2 = compare_historical_html(old, missing_section)
        self.assertEqual(result2["status"], "FAIL")
        self.assertIn("protected_section_inventory_changed", result2["failure_categories"])

    def test_legacy_guide_can_have_different_chapter_counts(self):
        old = sample(chapters=(10, 8))
        updated = sample(chapters=(10, 8), added=True)
        self.assertEqual(compare_historical_html(old, updated)["status"], "PASS")

    def test_original_source_revision_hash_guard(self):
        old = sample()
        with self.assertRaisesRegex(ValueError, "baseline SHA-256"):
            compare_historical_html(old, old, expected_baseline_sha256="0" * 64)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            compare_historical_html(old, old, expected_baseline_sha256="bad")

    def test_report_does_not_reproduce_private_source_text(self):
        import json
        old = sample()
        candidate = old.replace(b"Old source 0", b"Secret changed content", 1)
        r = compare_historical_html(old, candidate)
        text = json.dumps(r)
        self.assertNotIn("Secret changed content", text)
        self.assertNotIn("Historical synthetic heading", text)
        self.assertFalse(r["automatic_publish_allowed"])


if __name__ == "__main__":
    unittest.main()
