"""Guide identity mismatch and version hint checks; no web calls."""
import unittest

from engine.guide_identity import inspect_identity
from engine.source_page_acquire import SourceAccessError
from engine.spec_source_resolver import resolve_specialization


def page(title="Enhancement Shaman Rotation Guide - Midnight - Wowhead",
         h1="Enhancement Shaman Rotation Guide - Midnight",
         content="12.1.5 Patch Updated: 2026/10/13"):
    return ('<!doctype html><html><head><title>' + title +
            '</title></head><body><h1>' + h1 + '</h1><main>' +
            content + '</main></body></html>')


class GuideIdentityTests(unittest.TestCase):
    def setUp(self):
        self.spec = resolve_specialization("고양 주술사")

    def test_guided_identity_and_date_extraction(self):
        result = inspect_identity(page(), self.spec,
                                  expected_patch="12.1.5",
                                  min_updated="2026-10-13")
        self.assertTrue(result["guide_identity_matched"])
        self.assertEqual(result["observed_guide_update_date"], "2026-10-13")
        self.assertEqual(result["visible_patch_candidates"], ["12.1.5"])
        self.assertFalse(result["current_patch_independently_verified"])

    def test_wrong_specialization_heading_rejected(self):
        with self.assertRaisesRegex(SourceAccessError, "Guide heading"):
            inspect_identity(page("Arcane Mage Rotation Guide - Midnight",
                                  "Arcane Mage Rotation Guide"), self.spec)

    def test_conflicting_title_rejected_even_if_h1_matches(self):
        with self.assertRaisesRegex(SourceAccessError, "page title"):
            inspect_identity(page(title="Arcane Mage Rotation Guide - Midnight"),
                             self.spec)

    def test_patch_in_script_cannot_be_claimed_as_visible(self):
        html = page(content="<script>const patched='12.1.5 Patch';</script>Text")
        with self.assertRaisesRegex(SourceAccessError, "Requested patch"):
            inspect_identity(html, self.spec, expected_patch="12.1.5")

    def test_outdated_guide_fails_closed(self):
        with self.assertRaisesRegex(SourceAccessError, "older than required"):
            inspect_identity(page(content="12.0.7 Patch Updated: 2026/04/20"),
                             self.spec, min_updated="2026-10-13")

    def test_no_metadata_is_unknown_not_current(self):
        result = inspect_identity(page(content="A test"), self.spec)
        self.assertIsNone(result["observed_guide_update_date"])
        self.assertEqual(result["visible_patch_candidates"], [])
        self.assertFalse(result["automatic_publish_allowed"])

    def test_meta_date_modified_fallback(self):
        html = page(content="A test").replace(
            "</head>", '<meta property="article:modified_time" content="2026-10-16T12:10:00Z"></head>'
        )
        r = inspect_identity(html, self.spec, min_updated="2026-10-13")
        self.assertEqual(r["observed_guide_update_date"], "2026-10-16")

    def test_korean_updated_text_detected(self):
        r = inspect_identity(page(content="12.1.5 패치 업데이트됨: 2026/10/13"), self.spec)
        self.assertEqual(r["observed_guide_update_date"], "2026-10-13")
        self.assertEqual(r["visible_patch_candidates"], ["12.1.5"])

    def test_invalid_patch_and_date_rejected(self):
        with self.assertRaises(ValueError):
            inspect_identity(page(), self.spec, expected_patch="latest")
        with self.assertRaises(ValueError):
            inspect_identity(page(), self.spec, min_updated="not a date")

    def test_no_body_keyword_spoofing(self):
        html = page(title="Wowhead", h1="Some guide",
                    content="This refers to Enhancement Shaman Rotation Guide")
        with self.assertRaises(SourceAccessError):
            inspect_identity(html, self.spec)


if __name__ == "__main__":
    unittest.main()
