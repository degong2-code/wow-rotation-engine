"""Integration tests: private acquired HTML -> WHML structural audit."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from zipfile import ZipFile
import json

from engine.source_acquisition_pipeline import (
    inspect_and_store, require_authorized_navigation
)
from engine.source_page_acquire import SourceAccessError

FIXTURE = Path(__file__).resolve().parents[1] / "examples" / "synthetic-source-structure.html"


class SourcePipelineTests(TestCase):

    def test_verified_body_hash_equality_is_not_publish_approval(self):
        from engine.embedded_markup import inspect_embedded_whml
        html = FIXTURE.read_text(encoding="utf-8")
        expected = next(x["sha256"] for x in inspect_embedded_whml(html)["payloads"]
                        if x["target"] == "guide-body")
        with TemporaryDirectory() as temp:
            same = inspect_and_store(dom_html=html, output=Path(temp) / "same",
                                     kind="saved_html", expected_guide_sha256=expected)
            other = inspect_and_store(dom_html=html, output=Path(temp) / "other",
                                      kind="saved_html", expected_guide_sha256="0" * 64)
            self.assertTrue(same["matches_known_baseline"])
            self.assertFalse(same["source_change_review_required"])
            self.assertFalse(other["matches_known_baseline"])
            self.assertTrue(other["source_change_review_required"])
            self.assertFalse(same["source_patch_verified"])
            self.assertFalse(same["automatic_publish_allowed"])

    def test_invalid_expected_hash_fails_before_saving_source(self):
        html = FIXTURE.read_text(encoding="utf-8")
        with TemporaryDirectory() as temp:
            output = Path(temp) / "unsafe"
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                inspect_and_store(dom_html=html, output=output, kind="saved_html",
                                  expected_guide_sha256="invalid")
            self.assertFalse(output.exists())

    def test_saved_html_to_full_metadata_audit(self):
        html = FIXTURE.read_text(encoding="utf-8")
        with TemporaryDirectory() as temp:
            root = Path(temp)
            result = inspect_and_store(dom_html=html, output=root,
                                       kind="saved_html")
            self.assertEqual(result["guide_body_payloads"], 1)
            self.assertEqual(len(result["guide_body_sha256s"]), 1)
            self.assertEqual(len(result["guide_body_sha256s"][0]), 64)
            self.assertGreater(result["guide_body_character_counts"][0], 10)
            self.assertEqual(result["named_tooltip_definition_count"], 1)
            self.assertEqual(result["tooltip_reference_count"], 1)
            self.assertTrue((root / "analysis.html").exists())
            self.assertTrue((root / "structure-audit.json").exists())
            self.assertTrue((root / "pipeline-audit.json").exists())
            self.assertFalse(result["source_patch_verified"])
            self.assertFalse(result["automatic_publish_allowed"])
            report = (root / "pipeline-audit.json").read_text(encoding="utf-8")
            self.assertNotIn("A synthetic explanation", report)

    def test_non_guide_rejected_without_writing_snapshot(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(SourceAccessError, "No literal guide-body"):
                inspect_and_store(
                    dom_html="<!doctype html><html><body>Access blocked</body></html>",
                    output=root,
                    kind="saved_html",
                )
            self.assertFalse((root / "analysis.html").exists())

    def test_hydration_preserves_richer_network_response(self):
        raw = FIXTURE.read_text(encoding="utf-8")
        dom = "<!doctype html><html><body>Hydrated DOM</body></html>"
        with TemporaryDirectory() as temp:
            root = Path(temp)
            audit = inspect_and_store(dom_html=dom, raw_html=raw,
                                      output=root, kind="browser_url")
            self.assertEqual(audit["analysis_variant"], "network_response")
            self.assertEqual((root / "analysis.html").read_text(), raw)

    def test_wrong_domain_redirect_blocked(self):
        require_authorized_navigation(
            "https://www.wowhead.com/guide/example", "www.wowhead.com"
        )
        with self.assertRaisesRegex(SourceAccessError, "Cross-host"):
            require_authorized_navigation(
                "https://example.invalid/redirect", "www.wowhead.com"
            )
        with self.assertRaises(SourceAccessError):
            require_authorized_navigation(
                "http://127.0.0.1/hidden", "www.wowhead.com"
            )

    def test_missing_definition_is_reported_without_source_text(self):
        body = ('<!doctype html><html><body><script>WH.markup.printHtml('
                '"[span tooltip=missing]?[/span]", "guide-body", false);'
                '</script></body></html>')
        with TemporaryDirectory() as temp:
            audit = inspect_and_store(dom_html=body, output=Path(temp),
                                      kind="saved_html")
            self.assertEqual(audit["missing_named_tooltip_definitions"], 1)
            self.assertIn("tooltip_reference_without_definition", audit["issue_types"])
            self.assertNotIn('"missing"', json.dumps(audit))


    def test_cli_http_first_reaches_whml_audit_without_browser(self):
        from unittest.mock import patch
        from engine.source_acquisition_pipeline import main
        with TemporaryDirectory() as temp:
            output = Path(temp) / "private"
            html = FIXTURE.read_text(encoding="utf-8")
            with patch("engine.source_acquisition_pipeline.get_html", return_value=html) as fetch:
                with patch("sys.argv", [
                    "pipeline", "--http-url",
                    "https://www.wowhead.com/guide/classes/shaman/enhancement/rotation-cooldowns-pve-dps",
                    "--allow-remote", "--output", str(output)
                ]):
                    from contextlib import redirect_stdout
                    from io import StringIO
                    with redirect_stdout(StringIO()):
                        self.assertEqual(main(), 0)
            self.assertEqual(fetch.call_count, 1)
            audit = json.loads((output / "pipeline-audit.json").read_text(encoding="utf-8"))
            self.assertEqual(audit["acquisition_kind"], "http_direct")
            self.assertEqual(audit["guide_body_payloads"], 1)
            self.assertFalse(audit["source_patch_verified"])
            self.assertFalse(audit["automatic_publish_allowed"])

    def test_cli_http_forbidden_writes_no_source(self):
        from unittest.mock import patch
        from engine.source_acquisition_pipeline import main
        with TemporaryDirectory() as temp:
            output = Path(temp) / "private"
            with patch("engine.source_acquisition_pipeline.get_html",
                       side_effect=SourceAccessError("HTTP 403 Forbidden")):
                with patch("sys.argv", [
                    "pipeline", "--http-url",
                    "https://www.wowhead.com/guide/classes/shaman/enhancement/rotation-cooldowns-pve-dps",
                    "--allow-remote", "--output", str(output)
                ]):
                    with self.assertRaisesRegex(SourceAccessError, "403 Forbidden"):
                        main()
            self.assertFalse(output.exists())

    def test_private_zip_not_required_to_extract_assets(self):
        with TemporaryDirectory() as temp:
            zip_path = Path(temp) / "full_page.zip"
            with ZipFile(zip_path, "w") as archive:
                archive.writestr("example_files/bg.css", "not needed")
                archive.writestr("example.html", FIXTURE.read_text())
            from engine.source_page_acquire import read_saved_zip
            html, meta = read_saved_zip(zip_path)
            out = Path(temp) / "private"
            r = inspect_and_store(dom_html=html, kind=meta["kind"],
                                  metadata=meta, output=out)
            self.assertTrue((out / "analysis.html").exists())
            self.assertEqual(r["guide_body_payloads"], 1)
