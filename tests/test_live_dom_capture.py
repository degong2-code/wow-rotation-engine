"""True browser interaction regression for generic nested UI acquisition."""
from pathlib import Path
import unittest

from engine.live_dom_capture import capture, summarize

HERE = Path(__file__).resolve().parents[1]
FIXTURE = HERE / "examples" / "synthetic-live-dom.html"


class LiveDOMTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
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
            self.assertFalse(data["errors"], data["errors"])
            public = summarize(data)
            self.assertGreaterEqual(public["observed_state_count"], 5)
            self.assertNotIn("Beta Special", str(public))
            self.assertNotIn("Synthetic separate referenced", str(public))
            self.assertFalse(public["real_site_completeness_verified"])
            self.assertFalse(public["automatic_publish_allowed"])
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
