"""Synthetic-only tests for building a minimal private V11 edit patch."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from engine.v2.private_changes import make_patch, create_private_patch


ICON = (
    '<span data-spell="test"><img src="https://example.org/icon.png" '
    'onerror="this.hidden=true"/></span>'
)


def fixture():
    return {
        "schema_version": "v11-private-detail-v1",
        "guide_id": "rogue",
        "baseline_v11_sha256": "a" * 64,
        "public_storage_allowed": False,
        "rotation_groups": [{
            "id": "rogue:rogue-rotation:table-1",
            "rules": [{
                "id": "rogue:rogue-rotation:table-1:row-1",
                "condition_html": "<b>기존 조건</b>" + ICON,
                "condition_text_ko": "기존 조건",
                "action_text_ko": "합성 기술",
                "source_fragment_sha256": "b" * 64,
            }],
        }],
        "advanced_guidance": [{
            "id": "rogue:rogue-advanced:tip-1",
            "topic": "합성 심화 주제",
            "html": "<p class=\"sample\">기존 심화 설명입니다.</p>",
            "text_ko": "기존 심화 설명입니다.",
            "source_fragment_sha256": "c" * 64,
        }],
    }


class MinimalPrivateChangesTests(unittest.TestCase):
    def test_unchanged_detail_has_no_updates(self):
        doc = fixture()
        result = make_patch(doc, deepcopy(doc))
        self.assertEqual(result["updates"], [])

    def test_only_edited_rule_is_selected_and_original_icon_remains(self):
        old = fixture()
        proposed = deepcopy(old)
        proposed["rotation_groups"][0]["rules"][0]["condition_html"] = (
            "<b>검토된 새 조건</b>" + ICON
        )
        proposed["rotation_groups"][0]["rules"][0]["condition_text_ko"] = "검토된 새 조건"
        result = make_patch(old, proposed)
        self.assertEqual(len(result["updates"]), 1)
        self.assertEqual(result["updates"][0]["kind"], "rule")
        self.assertEqual(result["updates"][0]["id"],
                         "rogue:rogue-rotation:table-1:row-1")
        self.assertEqual(result["updates"][0]["expected_source_sha256"], "b" * 64)
        self.assertIn(ICON, result["updates"][0]["new_inner_html"])

    def test_one_advanced_tip_edit_changes_only_tip_inner(self):
        old = fixture()
        proposed = deepcopy(old)
        proposed["advanced_guidance"][0]["html"] = (
            '<p class="sample">개선된 <strong>합성 설명</strong>입니다.</p>'
        )
        proposed["advanced_guidance"][0]["text_ko"] = "개선된 합성 설명 입니다."
        result = make_patch(old, proposed)
        self.assertEqual(len(result["updates"]), 1)
        self.assertEqual(result["updates"][0]["kind"], "tip")
        self.assertEqual(result["updates"][0]["id"],
                         "rogue:rogue-advanced:tip-1")
        self.assertEqual(result["updates"][0]["new_inner_html"],
                         "개선된 <strong>합성 설명</strong>입니다.")

    def test_cannot_silently_change_original_evidence(self):
        old = fixture()
        proposed = deepcopy(old)
        proposed["rotation_groups"][0]["rules"][0]["source_fragment_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "provenance changed"):
            make_patch(old, proposed)

    def test_cannot_remove_original_spell_icon(self):
        old = fixture()
        proposed = deepcopy(old)
        proposed["rotation_groups"][0]["rules"][0]["condition_html"] = "아이콘 누락"
        proposed["rotation_groups"][0]["rules"][0]["condition_text_ko"] = "아이콘 누락"
        with self.assertRaisesRegex(ValueError, "spell icons"):
            make_patch(old, proposed)

    def test_cannot_create_executable_handler_or_script(self):
        old = fixture()
        for replacement in ('<script>alert(1)</script>' + ICON,
                            '<img src="https://example.org/icon.png" onerror="alert(1)">' + ICON):
            proposed = deepcopy(old)
            proposed["rotation_groups"][0]["rules"][0]["condition_html"] = replacement
            proposed["rotation_groups"][0]["rules"][0]["condition_text_ko"] = ""
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                make_patch(old, proposed)

    def test_condition_text_must_match_html(self):
        old = fixture()
        proposed = deepcopy(old)
        proposed["rotation_groups"][0]["rules"][0]["condition_text_ko"] = "다른 내용"
        with self.assertRaisesRegex(ValueError, "text and HTML disagree"):
            make_patch(old, proposed)

    def test_tip_must_keep_same_outer_html_tag(self):
        old = fixture()
        proposed = deepcopy(old)
        proposed["advanced_guidance"][0]["html"] = "<div>새 설명</div>"
        proposed["advanced_guidance"][0]["text_ko"] = "새 설명"
        with self.assertRaisesRegex(ValueError, "outer tag changed"):
            make_patch(old, proposed)

    def test_private_patch_file_is_created_outside_repository(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = root / "baseline.json"
            proposed = root / "proposed.json"
            out = root / "patch.json"
            doc = fixture()
            original.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
            changed = deepcopy(doc)
            changed["advanced_guidance"][0]["html"] = '<p class="sample">새 설명</p>'
            changed["advanced_guidance"][0]["text_ko"] = "새 설명"
            proposed.write_text(json.dumps(changed, ensure_ascii=False), encoding="utf-8")
            report = create_private_patch(original, proposed, out)
            self.assertEqual(report["updated_count"], 1)
            self.assertEqual(report["updated_ids"], [
                "rogue:rogue-advanced:tip-1"
            ])
            self.assertEqual(len(json.loads(out.read_text())["updates"]), 1)
            with self.assertRaises(FileExistsError):
                create_private_patch(original, proposed, out)

    def test_reject_private_content_inside_public_repo(self):
        with self.assertRaisesRegex(ValueError, "cannot be stored in GitHub"):
            create_private_patch(
                Path(__file__).resolve(), Path("/private/candidate.json"),
                Path("/private/result.json"),
            )


if __name__ == "__main__":
    unittest.main()
