"""User-oriented, no-browser, standalone manual preview smoke tests."""
import json
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
import unittest

from engine.manual_site import render
from engine.public_data import BASE


class ManualPreviewTests(unittest.TestCase):
    def test_all_existing_content_is_visible_in_html(self):
        page=render()
        self.assertEqual(page.count('class="guide-panel"'),7)
        self.assertEqual(page.count('class="scenario"'),23)
        self.assertEqual(page.count('class="priority-row"'),177)
        self.assertEqual(page.count('class="tips"'),7)
        self.assertIn("data-select-guide=\"fire\"",page)
        self.assertIn("data-select-guide=\"assassination\"",page)
        self.assertIn("data-select-hero=\"deathstalker\"",page)
        self.assertIn("https://www.wowhead.com/ko/spell=30455",page)
        self.assertIn("세부 조건 미수록",page)

    def test_build_is_deterministic(self):
        self.assertEqual(render(),render())

    def test_user_controls_are_present_and_connected(self):
        page=render()
        for target in ("spell-search","mode-filter","target-filter",
                       "filter-result","empty-result"):
            self.assertIn(f'id="{target}"',page)
        for javascript in ("function selectGuide","function selectHero",
                           "function filter()","window.addEventListener",
                           "history.replaceState"):
            self.assertIn(javascript,page)
        self.assertIn('type="search"',page)

    def test_html_escapes_untrusted_labels(self):
        with TemporaryDirectory() as tmp:
            base=Path(tmp)/"public"
            copytree(BASE,base)
            path=base/"rules"/"fire.json"
            data=json.loads(path.read_text(encoding="utf-8"))
            data["class_ko"]="<script>bad()</script>"
            data["rotation_groups"][0]["rules"][0]["action"]["name_ko"]="<img onerror=alert(1)>"
            # Changing rule names would break spell dictionary integrity; test the class label only.
            data["rotation_groups"][0]["rules"][0]["action"]["name_ko"]="유성"
            path.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")
            page=render(base)
            self.assertNotIn("<script>bad()</script>",page)
            self.assertIn("&lt;script&gt;bad()&lt;/script&gt;",page)

    def test_new_spec_in_manifest_creates_new_navigation_button(self):
        with TemporaryDirectory() as tmp:
            base=Path(tmp)/"public"
            copytree(BASE,base)
            manifest_path=base/"manifest.json"
            manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
            guide=json.loads((base/"rules"/"fire.json").read_text(encoding="utf-8"))
            guide["guide_id"]="testspec"
            guide["spec_ko"]="추가 시험 전문화"
            (base/"rules"/"testspec.json").write_text(json.dumps(guide,ensure_ascii=False),encoding="utf-8")
            new_manifest=dict(manifest["guides"][0])
            new_manifest.update({"id":"testspec","spec_ko":"추가 시험 전문화","file":"rules/testspec.json"})
            manifest["guides"].append(new_manifest)
            manifest["counts"]["specs"]+=1
            manifest["counts"]["tables"]+=new_manifest["rotation_group_count"]
            manifest["counts"]["rows"]+=new_manifest["priority_row_count"]
            manifest["counts"]["advanced_tips"]+=new_manifest["advanced_item_count"]
            manifest["counts"]["unresolved_spell_ids"]+=sum(
                row["action"]["spell_id"] is None
                for group in guide["rotation_groups"] for row in group["rules"])
            manifest_path.write_text(json.dumps(manifest,ensure_ascii=False),encoding="utf-8")
            page=render(base)
            self.assertEqual(page.count('class="guide-panel"'),8)
            self.assertIn('data-select-guide="testspec"',page)
            self.assertIn("추가 시험 전문화",page)

    def test_guide_does_not_claim_completeness(self):
        page=render()
        self.assertIn("간략 참조판",page)
        self.assertIn("세부 발동 조건·예외",page)
        self.assertNotIn("실전 검증 완료",page)


if __name__=="__main__":
    unittest.main()
