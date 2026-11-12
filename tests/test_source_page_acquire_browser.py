"""Chromium acquisition tests; only synthetic local fixtures, no Wowhead requests."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from engine.source_page_acquire import (
    acquisition_audit, capture_loaded_page, write_private_snapshot
)

HERE = Path(__file__).resolve().parents[1]
WHML_FIXTURE = HERE / "examples" / "synthetic-source-structure.html"
DYNAMIC_FIXTURE = HERE / "examples" / "synthetic-live-dom.html"


class BrowserAcquisitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise unittest.SkipTest("Playwright only available in optional Chromium workflow")
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def test_rendered_html_contains_inline_markup_and_optional_mhtml(self):
        page = self.browser.new_page()
        try:
            page.goto(WHML_FIXTURE.as_uri(), wait_until="domcontentloaded")
            rendered, source, mhtml = capture_loaded_page(
                page, None, required_markers=("WH.markup.printHtml",),
                capture_mhtml=True
            )
            self.assertIn("WH.markup.printHtml", rendered)
            self.assertIsNone(source)  # file:// has no HTTP response body
            self.assertIn("multipart/related", mhtml.lower())
            report = acquisition_audit(
                rendered, origin="browser_url", source_html=source, mhtml=mhtml
            )
            self.assertTrue(report["optional_mhtml_saved"])
            self.assertFalse(report["site_version_verified"])
            with TemporaryDirectory() as folder:
                output = Path(folder)
                write_private_snapshot(output, rendered, report, mhtml=mhtml)
                self.assertTrue((output / "page.html").exists())
                self.assertTrue((output / "page.mhtml").exists())
                self.assertFalse((output / "network-response.html").exists())
                self.assertNotIn(
                    "Synthetic", (output / "audit.json").read_text(encoding="utf-8")
                )
        finally:
            page.close()

    def test_dynamic_html_snapshot_preserves_page_logic_markup(self):
        page = self.browser.new_page()
        try:
            page.goto(DYNAMIC_FIXTURE.as_uri(), wait_until="domcontentloaded")
            rendered, source, mhtml = capture_loaded_page(
                page, None, required_markers=("betaMode",)
            )
            self.assertIn("betaMode", rendered)
            self.assertIn("heroB", rendered)
            self.assertIsNone(mhtml)
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
