"""True browser interaction regression for generic nested UI acquisition."""
from pathlib import Path
import unittest

from engine.live_dom_capture import capture, summarize

HERE = Path(__file__).resolve().parents[1]
FIXTURE = HERE / "examples" / "synthetic-live-dom.html"


class LiveDOMTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise unittest.SkipTest("Playwright is an optional browser-only dependency")
        cls.runner = sync_playwright().start()
        cls.browser = cls.runner.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runner.stop()

    def test_dynamic_hero_nested_tab_and_tooltip(self):
        page = self.browser.new_page()
        try:
            page.goto(FIXTURE.as_uri())
            data = capture(page, max_states=20, max_depth=3, max_tooltips_per_state=15)
            text = [s["observation"]["body"] for s in data["states"]]
            self.assertTrue(any("Rule alpha single" in t for t in text))
            self.assertTrue(any("Rule alpha AoE" in t for t in text))
            self.assertTrue(any("Beta Special" in t for t in text))
            self.assertTrue(any("Expanded synthetic advanced note" in t for t in text))
            triggered = [h for s in data["states"] for h in s["hover_results"]]
            self.assertTrue(any("Synthetic separate referenced tooltip body"
                                in str(h["trigger"]["references"]) for h in triggered))
            self.assertTrue(any(
                "Synthetic hover-generated additional explanatory rule." in
                " ".join(h["dynamic_tooltips"]) for h in triggered
            ))
            self.assertTrue(any(
                "Synthetic tooltip only available from a bare question mark." in
                " ".join(h["dynamic_tooltips"]) for h in triggered
            ))
            self.assertFalse(data["errors"], data["errors"])
            public = summarize(data)
            self.assertGreaterEqual(public["observed_state_count"], 5)
            self.assertNotIn("Beta Special", str(public))
            self.assertNotIn("Synthetic separate referenced", str(public))
            self.assertFalse(public["real_site_completeness_verified"])
            self.assertFalse(public["automatic_publish_allowed"])
        finally:
            page.close()

    def test_private_url_components_not_exported(self):
        private = {
            "source_url": "https://user:secret@example.invalid/private/file?token=abc#anchor",
            "source_sha256": "a" * 64,
            "states": [], "errors": [], "pending_state_count": 0,
        }
        public = summarize(private)
        import json
        output = json.dumps(public)
        self.assertEqual(public["host"], "example.invalid")
        for secret in ("user:secret", "/private/file", "token=abc", "anchor"):
            self.assertNotIn(secret, output)

    def test_state_limit_exposes_unvisited_frontier(self):
        page = self.browser.new_page()
        try:
            page.goto(FIXTURE.as_uri())
            private = capture(page, max_states=1, max_depth=3)
            public = summarize(private)
            self.assertEqual(public["observed_state_count"], 1)
            self.assertGreater(public["pending_state_count"], 0)
            self.assertTrue(public["capture_bounded"])
            self.assertFalse(public["real_site_completeness_verified"])
        finally:
            page.close()

    def test_bare_question_without_tooltip_attributes_has_stable_path(self):
        from engine.live_dom_capture import OBSERVE, _hover
        page = self.browser.new_page()
        try:
            page.goto(FIXTURE.as_uri())
            page.locator("#heroB").click()
            observed = page.evaluate(OBSERVE)
            candidates = [t for t in observed["tooltip_triggers"] if t["bare_question"]]
            self.assertEqual(len(candidates), 1)
            self.assertFalse(candidates[0]["id"])
            self.assertTrue(candidates[0]["css_path"].startswith("html > "))
            hovered = _hover(page, 20)
            self.assertTrue(any(
                "Synthetic tooltip only available from a bare question mark." in
                " ".join(item["dynamic_tooltips"]) for item in hovered
            ))
        finally:
            page.close()

    def test_stable_id_replay_ignores_stale_position(self):
        from engine.live_dom_capture import _perform
        page = self.browser.new_page()
        try:
            page.goto(FIXTURE.as_uri())
            page.locator("#heroB").click()
            _perform(page, {"index": 999, "kind": "select",
                            "dom_id": "betaMode", "value": "alternate"})
            self.assertTrue(page.locator("#beta-extra").is_visible())
        finally:
            page.close()

    def test_tooltip_limit_is_visible_as_unvisited_and_not_approved(self):
        page = self.browser.new_page()
        try:
            page.goto(FIXTURE.as_uri())
            data = capture(page, max_states=12, max_depth=3,
                           max_tooltips_per_state=0)
            report = summarize(data)
            self.assertTrue(report["known_capture_gaps"])
            self.assertTrue(any(s["unhovered_tooltip_triggers"] > 0
                                for s in report["states"]))
            self.assertFalse(report["real_site_completeness_verified"])
        finally:
            page.close()

    def test_depth_limit_reveals_unvisited_child_states(self):
        page = self.browser.new_page()
        try:
            page.goto(FIXTURE.as_uri())
            report = summarize(capture(page, max_states=24, max_depth=0))
            self.assertEqual(report["observed_state_count"], 1)
            self.assertGreater(report["depth_limited_state_count"], 0)
            self.assertTrue(report["known_capture_gaps"])
        finally:
            page.close()

    def test_bounded_state_count_and_no_assumed_real_completeness(self):
        page = self.browser.new_page()
        try:
            page.goto(FIXTURE.as_uri())
            data = capture(page, max_states=2, max_depth=2)
            audit = summarize(data)
            self.assertEqual(audit["observed_state_count"], 2)
            self.assertFalse(audit["real_site_completeness_verified"])
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
