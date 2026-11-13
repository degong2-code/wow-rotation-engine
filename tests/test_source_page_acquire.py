"""Offline coverage of reusable page acquisition; never downloads real guide."""
from pathlib import Path
from tempfile import TemporaryDirectory
import io
import json
import unittest
from unittest.mock import Mock
from zipfile import ZipFile

from engine.source_page_acquire import (
    SourceAccessError, _validate_remote_url, acquisition_audit,
    capture_loaded_page, read_saved_html, read_saved_zip, write_private_snapshot
)

SYNTHETIC = (
    '<!doctype html><html><head><title>Synthetic Guide</title></head><body>'
    '<main>Fictional rotation</main><script>WH.markup.printHtml('
    '"[tooltip name=example]Private synthetic explanation[/tooltip]", '
    '"guide-body", false);</script></body></html>'
)


class AcquireTests(unittest.TestCase):
    def test_html_saved_without_companion_folder(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "Synthetic Guide.html"
            path.write_text(SYNTHETIC, encoding="utf-8")
            html, metadata = read_saved_html(path)
            self.assertIn("WH.markup.printHtml", html)
            self.assertFalse(metadata["companion_folder_required"])

    def test_zip_prefers_real_main_html_and_ignores_files(self):
        with TemporaryDirectory() as folder:
            archive = Path(folder) / "saved.zip"
            with ZipFile(archive, "w") as z:
                z.writestr("Saved Page_files/stylesheet.css", "body { color: red }")
                z.writestr("Saved Page_files/sidebar.html",
                           "<html><body>" + ("Irrelevant resource text " * 300) + "</body></html>")
                z.writestr("Saved Page.html", SYNTHETIC)
            html, meta = read_saved_zip(archive)
            self.assertEqual(html, SYNTHETIC)
            self.assertEqual(meta["archive_entries"], 3)
            self.assertEqual(meta["html_candidates"], 2)
            self.assertEqual(meta["resource_entries_ignored"], 2)
            self.assertFalse(meta["companion_folder_required"])

    def test_companion_resources_cannot_escape_zip(self):
        with TemporaryDirectory() as folder:
            archive = Path(folder) / "saved.zip"
            with ZipFile(archive, "w") as z:
                z.writestr("../not-extracted.js", "private")
                z.writestr("page.html", SYNTHETIC)
            html, _ = read_saved_zip(archive)
            self.assertEqual(html, SYNTHETIC)
            self.assertFalse((Path(folder).parent / "not-extracted.js").exists())

    def test_error_on_non_html_zip(self):
        with TemporaryDirectory() as folder:
            archive = Path(folder) / "saved.zip"
            with ZipFile(archive, "w") as z:
                z.writestr("assets.css", "body{}")
            with self.assertRaises(SourceAccessError):
                read_saved_zip(archive)

    def test_403_fails_without_fallback_bypass(self):
        page = Mock()
        response = Mock()
        response.status = 403
        with self.assertRaisesRegex(SourceAccessError, "HTTP 403"):
            capture_loaded_page(page, response)
        page.content.assert_not_called()

    def test_missing_guide_marker_is_explicit_failure(self):
        page = Mock()
        page.content.return_value = "<!doctype html><html><body>Challenge</body></html>"
        response = Mock()
        response.status = 200
        response.headers = {"content-type": "text/html"}
        response.body.return_value = b"<html><body>Challenge</body></html>"
        with self.assertRaisesRegex(SourceAccessError, "Required guide"):
            capture_loaded_page(page, response,
                                required_markers=("WH.markup.printHtml",))

    def test_browser_raw_response_recovers_missing_dom_script(self):
        page = Mock()
        page.content.return_value = "<!doctype html><html><body>Rendered view</body></html>"
        response = Mock()
        response.status = 200
        response.headers = {"content-type": "text/html"}
        response.body.return_value = SYNTHETIC.encode("utf-8")
        dom, raw, mhtml = capture_loaded_page(
            page, response, required_markers=("WH.markup.printHtml",))
        self.assertIn("WH.markup.printHtml", raw)
        self.assertNotIn("WH.markup.printHtml", dom)
        self.assertIsNone(mhtml)

    def test_analysis_auto_chooses_full_network_markup_if_dom_is_hydrated(self):
        dom = "<!doctype html><html><body>Hydrated page without script</body></html>"
        audit = acquisition_audit(dom, origin="browser_url", source_html=SYNTHETIC)
        self.assertEqual(audit["analysis_html_variant"], "network_response")
        self.assertEqual(audit["guide_body_payloads"], 1)
        with TemporaryDirectory() as folder:
            write_private_snapshot(Path(folder), dom, audit, source_html=SYNTHETIC)
            self.assertEqual(
                (Path(folder) / "analysis.html").read_text(), SYNTHETIC
            )
            self.assertEqual(
                (Path(folder) / "page.html").read_text(), dom
            )

    def test_dom_can_be_more_complete_than_network_response(self):
        raw = "<!doctype html><html><body>Static</body></html>"
        audit = acquisition_audit(SYNTHETIC, origin="browser_url", source_html=raw)
        self.assertEqual(audit["analysis_html_variant"], "rendered_dom")
        self.assertEqual(audit["guide_body_payloads"], 1)

    def test_public_audit_contains_no_source_text(self):
        audit = acquisition_audit(SYNTHETIC, origin="saved_html")
        output = json.dumps(audit, ensure_ascii=False)
        self.assertEqual(audit["guide_body_payloads"], 1)
        self.assertEqual(audit["guide_named_tooltips"], 1)
        self.assertNotIn("Private synthetic explanation", output)
        self.assertNotIn("Synthetic Guide", output)
        self.assertFalse(audit["real_site_completeness_verified"])

    def test_private_write_and_separate_safe_audit(self):
        with TemporaryDirectory() as folder:
            report = acquisition_audit(SYNTHETIC, origin="saved_html")
            write_private_snapshot(Path(folder), SYNTHETIC, report)
            self.assertIn("Private synthetic explanation",
                          (Path(folder) / "page.html").read_text())
            self.assertNotIn("Private synthetic explanation",
                             (Path(folder) / "audit.json").read_text())

    def test_remote_requires_https_and_public_origin(self):
        for url in ["http://wowhead.com", "file:///tmp/foo",
                    "https://localhost:9000", "https://127.0.0.1",
                    "https://user:password@wowhead.com"]:
            with self.subTest(url=url), self.assertRaises(SourceAccessError):
                _validate_remote_url(url)
        _validate_remote_url(
            "https://www.wowhead.com/guide/classes/shaman/enhancement/rotation-cooldowns-pve-dps"
        )


if __name__ == "__main__":
    unittest.main()
