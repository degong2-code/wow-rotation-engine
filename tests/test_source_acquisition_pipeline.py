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
from engine.spec_source_resolver import resolve_specialization

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


    def test_specialization_auto_resolution_identity_and_whml_audit(self):
        from engine.source_acquisition_pipeline import run_specialization
        spec = resolve_specialization("고양 주술사")
        synthetic = (
            '<!doctype html><html><head>'
            '<title>Enhancement Shaman Rotation Guide - Midnight - Wowhead</title></head>'
            '<body><h1>Enhancement Shaman Rotation Guide</h1>'
            '<main>12.1.5 Patch Updated: 2026/10/13</main>'
            '<script>WH.markup.printHtml('
            '"[tooltip name=Example]Synthetic source-only note[/tooltip]",'
            '"guide-body", false);</script></body></html>'
        )
        with TemporaryDirectory() as temp:
            output = Path(temp) / "source"
            seen = []
            def fetch(url):
                seen.append(url)
                return synthetic
            result = run_specialization("고양 주술사", output,
                                        expected_patch="12.1.5",
                                        min_updated="2026-10-13",
                                        fetch_html=fetch)
            self.assertEqual(seen, [spec.guide_url])
            self.assertTrue(result["guide_identity_matched"])
            self.assertTrue(result["expected_patch_visible"])
            self.assertEqual(result["observed_guide_update_date"], "2026-10-13")
            self.assertEqual(result["named_tooltip_definition_count"], 1)
            self.assertFalse(result["source_patch_verified"])
            self.assertFalse(result["automatic_publish_allowed"])
            self.assertNotIn("Synthetic source-only note",
                             (output / "pipeline-audit.json").read_text())

    def test_ambiguous_spec_fails_before_fetch(self):
        from engine.source_acquisition_pipeline import run_specialization
        from engine.spec_source_resolver import AmbiguousSpecialization
        with TemporaryDirectory() as temp:
            called = []
            with self.assertRaises(AmbiguousSpecialization):
                run_specialization("냉기", Path(temp) / "source",
                                   fetch_html=lambda u: called.append(u))
            self.assertEqual(called, [])

    def test_wrong_guide_title_fails_without_writing(self):
        from engine.source_acquisition_pipeline import run_specialization
        other = (
            '<!doctype html><html><head><title>Arcane Mage Rotation Guide</title></head>'
            '<body><h1>Arcane Mage Rotation Guide</h1><script>'
            'WH.markup.printHtml("[tooltip name=x]Synthetic[/tooltip]", "guide-body", false);'
            '</script></body></html>'
        )
        with TemporaryDirectory() as temp:
            output = Path(temp) / "source"
            with self.assertRaisesRegex(SourceAccessError, "Guide heading"):
                run_specialization("고양 주술사", output, fetch_html=lambda _: other)
            self.assertFalse(output.exists())

    def test_outdated_guide_fails_before_persisting(self):
        from engine.source_acquisition_pipeline import run_specialization
        old = (
            '<!doctype html><html><head>'
            '<title>Enhancement Shaman Rotation Guide - Midnight</title></head>'
            '<body><h1>Enhancement Shaman Rotation Guide</h1>'
            '12.0.7 Patch Updated: 2026/04/20</body></html>'
        )
        with TemporaryDirectory() as temp:
            output = Path(temp) / "source"
            with self.assertRaisesRegex(SourceAccessError, "older than required"):
                run_specialization("고양 주술사", output,
                                   min_updated="2026-10-13",
                                   fetch_html=lambda _: old)
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
            self.assertTrue((root / "scoped-evidence-private.json").exists())
            self.assertTrue((root / "scoped-audit.json").exists())
            scope_audit = json.loads((root / "scoped-audit.json").read_text())
            self.assertFalse(scope_audit["gameplay_meaning_verified"])
            self.assertFalse(scope_audit["automatic_publish_allowed"])
            self.assertNotIn("Fictional rotation", json.dumps(scope_audit))
            packet = json.loads((root / "editorial-evidence-private.json").read_text())
            self.assertTrue(packet["source_text_in_file"])
            self.assertFalse(packet["source_text_may_be_public"])
            self.assertEqual(len(packet["payloads"]), 1)
            self.assertTrue(packet["payloads"][0]["original_whml"])
            self.assertFalse(result["automatic_publish_allowed"])
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


    def test_pipeline_unbound_action_selector_is_review_not_success(self):
        import json
        whml = ('[ol][li display-options=MissingBuild]'
                '[spell=101]Source action[/li][/ol]')
        html = ('<!doctype html><html><script>WH.markup.printHtml('
                + json.dumps(whml) + ',"guide-body",false);'
                '</script></html>')
        with TemporaryDirectory() as tmp:
            report = inspect_and_store(
                dom_html=html, output=Path(tmp), kind="saved_html")
        self.assertEqual(
            report["source_selector_impact"]["unbound_selector_ordered_row_candidates"], 1)
        self.assertFalse(report["source_selector_references_resolved"])
        self.assertTrue(report["source_selector_action_review_required"])
        self.assertIn("conditional_option_without_definition", report["issue_types"])
        self.assertIn("unbound_selector_ordered_action_candidate", report["issue_types"])
        self.assertFalse(report["gameplay_meaning_verified"])
        self.assertFalse(report["automatic_publish_allowed"])
        self.assertNotIn("MissingBuild", json.dumps(report))
        self.assertNotIn("Source action", json.dumps(report))

    def test_pipeline_declared_action_control_remains_valid(self):
        import json
        whml = ('[display-option=BuildA radio=build checked]Build[/display-option]'
                '[ol][li display-options=BuildA]'
                '[spell=101]Source action[/li][/ol]')
        html = ('<!doctype html><html><script>WH.markup.printHtml('
                + json.dumps(whml) + ',"guide-body",false);'
                '</script></html>')
        with TemporaryDirectory() as tmp:
            report = inspect_and_store(
                dom_html=html, output=Path(tmp), kind="saved_html")
        self.assertTrue(report["source_selector_references_resolved"])
        self.assertFalse(report["source_selector_action_review_required"])
        self.assertNotIn("unbound_selector_ordered_action_candidate", report["issue_types"])


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


    def test_spec_cli_capture_ui_reuses_authorized_browser_path(self):
        from unittest.mock import patch
        from engine.source_acquisition_pipeline import main
        from contextlib import redirect_stdout
        from io import StringIO
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "source"
            with patch("engine.source_acquisition_pipeline.run_browser",
                       return_value={"gameplay_meaning_verified": False}) as browse:
                with patch("sys.argv", [
                    "pipeline", "--specialization", "생존 사냥꾼",
                    "--allow-remote", "--capture-ui", "--max-states", "12",
                    "--max-depth", "2", "--expected-patch", "12.1.5",
                    "--min-updated", "2026-10-13", "--output", str(output),
                ]):
                    with redirect_stdout(StringIO()):
                        self.assertEqual(main(), 0)
            args, kwargs = browse.call_args
            self.assertEqual(args[0], resolve_specialization("생존 사냥꾼").guide_url)
            self.assertIs(kwargs["specialization"],
                          resolve_specialization("생존 사냥꾼"))
            self.assertEqual(kwargs["max_states"], 12)
            self.assertEqual(kwargs["max_depth"], 2)
            self.assertTrue(kwargs["capture_ui"])
            self.assertEqual(kwargs["expected_patch"], "12.1.5")
            self.assertEqual(kwargs["min_updated"], "2026-10-13")

    @staticmethod
    def _synthetic_guide_version(patch, updated, *, name="Survival Hunter"):
        return (
            '<!doctype html><html><head><title>' + name +
            ' Rotation Guide - Wowhead</title></head><body>'
            '<h1>' + name + ' Rotation Guide</h1>'
            '<main>Patch ' + patch + ' Updated: ' + updated + '</main>'
            '<script>WH.markup.printHtml('
            '"[ol][li]Synthetic actionable source[/li][/ol]",'
            '"guide-body",false);</script></body></html>'
        )

    def _browser_stub(self, url, html):
        """Synthetic Playwright stub: no live site, no browser binary."""
        import sys
        from types import ModuleType
        from unittest.mock import MagicMock, patch
        browser_module = ModuleType("playwright")
        sync_api = ModuleType("playwright.sync_api")
        driver = MagicMock()
        page = driver.chromium.launch.return_value.new_page.return_value
        page.url = url
        page.goto.return_value.status = 200
        sync = MagicMock()
        sync.return_value.__enter__.return_value = driver
        sync_api.sync_playwright = sync
        return (
            patch.dict(sys.modules, {
                "playwright": browser_module, "playwright.sync_api": sync_api
            }),
            patch("engine.source_acquisition_pipeline.capture_loaded_page",
                  return_value=(html, html, None)),
        )

    def test_spec_browser_persists_ui_and_identity_in_one_private_report(self):
        from engine.source_acquisition_pipeline import run_browser
        from unittest.mock import patch
        spec = resolve_specialization("생존 사냥꾼")
        html = self._synthetic_guide_version("12.1.5", "2026/10/13")
        module_stub, html_stub = self._browser_stub(spec.guide_url, html)
        evidence = {
            "source_url": spec.guide_url, "source_sha256": "synthetic",
            "states": [], "errors": [], "pending_state_count": 0,
            "depth_limited_state_count": 0,
        }
        with TemporaryDirectory() as tmp, module_stub, html_stub:
            output = Path(tmp) / "private"
            with patch("engine.live_dom_capture.capture", return_value=evidence):
                result = run_browser(
                    spec.guide_url, output, capture_ui=True, specialization=spec,
                    expected_patch="12.1.5", min_updated="2026-10-13",
                )
            self.assertEqual(result["acquisition_kind"], "specialization_browser")
            self.assertTrue(result["guide_identity_matched"])
            self.assertEqual(result["observed_guide_update_date"], "2026-10-13")
            self.assertTrue(result["ui_capture_report_written"])
            self.assertEqual(result["ui_states_observed"], 0)
            self.assertTrue((output / "private-ui-capture.json").exists())
            self.assertTrue((output / "editorial-evidence-private.json").exists())
            stored = json.loads((output / "pipeline-audit.json").read_text())
            self.assertEqual(stored["resolved_guide_url"], spec.guide_url)
            self.assertEqual(stored["ui_states_observed"], 0)
            self.assertFalse(stored["real_site_completeness_verified"])
            self.assertFalse(stored["automatic_publish_allowed"])

    def test_spec_browser_rejects_stale_page_before_any_private_snapshot(self):
        from engine.source_acquisition_pipeline import run_browser
        spec = resolve_specialization("생존 사냥꾼")
        html = self._synthetic_guide_version("12.0.7", "2026/05/03")
        module_stub, html_stub = self._browser_stub(spec.guide_url, html)
        with TemporaryDirectory() as tmp, module_stub, html_stub:
            output = Path(tmp) / "private"
            with self.assertRaisesRegex(SourceAccessError, "Requested patch"):
                run_browser(
                    spec.guide_url, output, capture_ui=True, specialization=spec,
                    expected_patch="12.1.5", min_updated="2026-10-13",
                )
            self.assertFalse(output.exists())


    def test_spec_browser_rejects_dom_response_revision_conflict(self):
        from engine.source_acquisition_pipeline import run_browser
        from unittest.mock import patch
        spec = resolve_specialization("생존 사냥꾼")
        live = self._synthetic_guide_version("12.1.5", "2026/10/13")
        stale = self._synthetic_guide_version("12.0.7", "2026/05/03")
        module_stub, _ = self._browser_stub(spec.guide_url, live)
        with TemporaryDirectory() as tmp, module_stub:
            output = Path(tmp) / "private"
            with patch("engine.source_acquisition_pipeline.capture_loaded_page",
                       return_value=(live, stale, None)):
                with self.assertRaisesRegex(SourceAccessError,
                                           "disagree on guide revision"):
                    run_browser(spec.guide_url, output, specialization=spec)
            self.assertFalse(output.exists())

    def test_ui_state_identity_validator_rejects_stale_reload(self):
        from engine.live_dom_capture import capture, summarize
        from unittest.mock import MagicMock
        page = MagicMock()
        page.url = "https://www.wowhead.com/guide/synthetic"
        page.content.return_value = "<!doctype html><html></html>"
        def reject(_):
            raise SourceAccessError("Stale UI revision after reload")
        result = capture(page, max_states=1, validate_state=reject)
        self.assertEqual(result["states"], [])
        self.assertEqual(result["errors"][0]["type"], "SourceAccessError")
        self.assertTrue(summarize(result)["known_capture_gaps"])
        page.evaluate.assert_not_called()

    def test_spec_browser_rejects_another_specialization_before_saving(self):
        from engine.source_acquisition_pipeline import run_browser
        spec = resolve_specialization("생존 사냥꾼")
        html = self._synthetic_guide_version(
            "12.1.5", "2026/10/13", name="Arcane Mage"
        )
        module_stub, html_stub = self._browser_stub(spec.guide_url, html)
        with TemporaryDirectory() as tmp, module_stub, html_stub:
            output = Path(tmp) / "private"
            with self.assertRaisesRegex(SourceAccessError, "Guide heading"):
                run_browser(
                    spec.guide_url, output, capture_ui=True, specialization=spec,
                    expected_patch="12.1.5",
                )
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
