"""Synthetic tests for exact-span private V11 edits; no real guide content."""
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from engine.v2.patch_v11 import apply_patch, write_private_patch
from engine.v2.detail_bridge import digest


SOURCE = (
    '<!doctype html><html><head><style>.a{color:red}</style></head><body>'
    '<div class="manual-view" data-guide="rogue">'
    '<section id="rogue-rotation"><table class="priority">'
    '<thead><tr><th>순위</th><th>기술</th><th>조건</th></tr></thead>'
    '<tbody><tr><td>1</td><td>합성 기술</td>'
    '<td><b>합성 조건</b> 테스트 설명</td></tr></tbody></table></section>'
    '<section id="rogue-advanced"><h3>시험 주제</h3>'
    '<p>합성 심화 설명입니다.</p></section>'
    '</div><script>const currentUI = true;</script></body></html>'
)
RULE = "rogue:rogue-rotation:table-1:row-1"
TIP = "rogue:rogue-advanced:tip-1"
RULE_HASH = digest("1 | 합성 기술 | 합성 조건 테스트 설명")
TIP_HASH = digest("합성 심화 설명입니다.")


def baseline_details():
    return {"guides": [{
        "guide_id": "rogue",
        "rotation_groups": [{"rules": [{
            "id": RULE, "source_fragment_sha256": RULE_HASH,
        }]}],
        "advanced_guidance": [{
            "id": TIP, "source_fragment_sha256": TIP_HASH,
        }],
    }]}


def proposal(kind, item, sha, html):
    return {
        "kind": kind,
        "id": item,
        "expected_source_sha256": sha,
        "new_inner_html": html,
    }


class PrivateV11PatchTests(unittest.TestCase):
    def setUp(self):
        self.source_sha = hashlib.sha256(SOURCE.encode("utf-8")).hexdigest()

    def patch_doc(self, updates, baseline=None):
        return {
            "schema_version": "v11-private-patch-v1",
            "baseline_v11_sha256": baseline or self.source_sha,
            "updates": updates,
        }

    def execute(self, updates):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "v11.html"
            source.write_text(SOURCE, encoding="utf-8")
            with patch("engine.v2.patch_v11.extract_details", return_value=baseline_details()):
                return apply_patch(source, self.patch_doc(updates)).decode("utf-8")

    def test_zero_changes_remain_byte_identical(self):
        self.assertEqual(self.execute([]), SOURCE)

    def test_one_condition_changes_no_other_html_byte(self):
        result = self.execute([proposal("rule", RULE, RULE_HASH, "<b>변경 조건</b> 테스트 설명")])
        expected = SOURCE.replace("<b>합성 조건</b> 테스트 설명",
                                  "<b>변경 조건</b> 테스트 설명")
        self.assertEqual(result, expected)
        self.assertIn("<script>const currentUI = true;</script>", result)
        self.assertIn("<style>.a{color:red}</style>", result)

    def test_tip_change_preserves_original_tag_and_other_content(self):
        result = self.execute([proposal("tip", TIP, TIP_HASH,
                                        "수정된 <strong>합성 설명</strong>입니다.")])
        self.assertEqual(
            result,
            SOURCE.replace("<p>합성 심화 설명입니다.</p>",
                           "<p>수정된 <strong>합성 설명</strong>입니다.</p>")
        )

    def test_two_changes_are_applied_in_source_order(self):
        result = self.execute([
            proposal("tip", TIP, TIP_HASH, "수정된 심화 설명"),
            proposal("rule", RULE, RULE_HASH, "수정된 조건"),
        ])
        self.assertIn("<td>수정된 조건</td>", result)
        self.assertIn("<p>수정된 심화 설명</p>", result)

    def test_wrong_source_provenance_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "source evidence mismatch"):
            self.execute([proposal("rule", RULE, "0" * 64, "수정된 조건")])

    def test_duplicate_item_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate patch ID"):
            self.execute([
                proposal("rule", RULE, RULE_HASH, "조건A"),
                proposal("rule", RULE, RULE_HASH, "조건B"),
            ])

    def test_unsafe_markup_rejected(self):
        for payload in ('<script>alert(1)</script>', '<a href="javascript:alert(1)">링크</a>',
                        '<b onclick="alert(1)">클릭</b>'):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                self.execute([proposal("tip", TIP, TIP_HASH, payload)])

    def test_baseline_mismatch_rejected(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "v11.html"
            source.write_text(SOURCE, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "baseline SHA-256 mismatch"):
                apply_patch(source, self.patch_doc([], baseline="f" * 64))

    def test_private_output_cannot_be_under_repository(self):
        with self.assertRaisesRegex(ValueError, "GitHub repository"):
            write_private_patch(
                Path("/private/v11.html"), Path("/private/edits.json"),
                Path(__file__).resolve().parents[1] / "dist" / "updated-v11.html",
            )

    def test_original_cannot_be_overwritten(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "v11.html"
            source.write_text(SOURCE, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "overwrite the original"):
                write_private_patch(source, Path(tmp) / "patch.json", source)


    def test_inherited_v11_image_handler_and_spell_icon_are_preserved(self):
        icon = (
            '<span data-spell="synthetic-spell">'
            '<img onerror="this.hidden=true" src="https://example.org/icon.jpg"/></span>'
        )
        old_html = SOURCE.replace(
            "<b>합성 조건</b> 테스트 설명", f"<b>합성 조건</b>{icon} 테스트 설명"
        )
        new_content = f"<b>수정 조건</b>{icon} 테스트 설명"
        with TemporaryDirectory() as tmp:
            file = Path(tmp) / "v11.html"
            file.write_text(old_html, encoding="utf-8")
            document = {
                "schema_version": "v11-private-patch-v1",
                "baseline_v11_sha256": hashlib.sha256(
                    old_html.encode("utf-8")
                ).hexdigest(),
                "updates": [proposal("rule", RULE, RULE_HASH, new_content)],
            }
            with patch("engine.v2.patch_v11.extract_details",
                       return_value=baseline_details()):
                actual = apply_patch(file, document).decode("utf-8")
                self.assertEqual(
                    actual,
                    old_html.replace(
                        f"<b>합성 조건</b>{icon} 테스트 설명", new_content,
                    ),
                )
                missing_icon = dict(document, updates=[
                    proposal("rule", RULE, RULE_HASH, "<b>수정 조건</b> 테스트 설명")
                ])
                with self.assertRaisesRegex(ValueError, "spell icons"):
                    apply_patch(file, missing_icon)
                altered_event = dict(document, updates=[
                    proposal(
                        "rule", RULE, RULE_HASH,
                        new_content.replace("this.hidden=true", "alert(1)")
                    )
                ])
                with self.assertRaisesRegex(ValueError, "event handler"):
                    apply_patch(file, altered_event)


if __name__ == "__main__":
    unittest.main()
