"""Synthetic-only tests of the private V11-to-public-ID detail bridge."""
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from engine.v2.detail_bridge import digest, extract_details, export_private


SOURCE = (
    '<html><body><div class="manual-view" data-guide="rogue">'
    '<section id="rogue-rotation"><table class="priority">'
    '<thead><tr><th>순위</th><th>기술</th><th>조건</th></tr></thead>'
    '<tbody><tr><td>1</td><td>합성 기술</td>'
    '<td><b>합성 조건</b> 테스트 설명</td></tr></tbody></table></section>'
    '<section id="rogue-advanced"><div class="chapter-heading"><h2>고급</h2></div>'
    '<h3>시험 주제</h3><p>합성 심화 설명입니다.</p></section>'
    '</div></body></html>'
)


def public_fixture(baseline):
    rule_id = "rogue:rogue-rotation:table-1:row-1"
    tip_id = "rogue:rogue-advanced:tip-1"
    guide = {
        "guide_id": "rogue",
        "baseline_v11_sha256": baseline,
        "rotation_groups": [
            {
                "id": "rogue:rogue-rotation:table-1",
                "source_section": "rogue-rotation",
                "rules": [{
                    "id": rule_id, "order": 1,
                    "provenance": {
                        "v11_fragment_sha256": digest("1 | 합성 기술 | 합성 조건 테스트 설명"),
                        "locator": "section#rogue-rotation table.priority[1] tbody tr:nth-child(1)",
                    },
                }],
            },
        ],
        "advanced_guidance_index": [{
            "id": tip_id, "topic": "시험 주제",
            "provenance": {
                "v11_fragment_sha256": digest("합성 심화 설명입니다."),
                "locator": "section#rogue-advanced advanced-item[1]",
            },
        }],
    }
    return {"guides": [{"id": "rogue"}]}, {}, [guide]


class PrivateDetailBridgeTests(unittest.TestCase):
    def setUp(self):
        self.baseline = hashlib.sha256(SOURCE.encode("utf-8")).hexdigest()

    def _patch_data(self, guide=None):
        manifest, spells, guides = public_fixture(self.baseline)
        if guide is not None:
            guides[0] = guide
        return patch("engine.v2.detail_bridge.load",
                     return_value=(manifest, spells, guides))

    def test_full_text_is_matched_by_source_hash_and_not_published(self):
        with TemporaryDirectory() as tmp:
            src = Path(tmp) / "source.html"
            src.write_text(SOURCE, encoding="utf-8")
            with self._patch_data(), patch(
                "engine.v2.detail_bridge.validate", return_value={"ok": True}
            ):
                result = extract_details(src, expected_sha256=self.baseline)
                self.assertEqual(result["counts"], {
                    "specs": 1, "groups": 1, "rows": 1, "tips": 1,
                })
                guide = result["guides"][0]
                row = guide["rotation_groups"][0]["rules"][0]
                tip = guide["advanced_guidance"][0]
                self.assertEqual(row["condition_text_ko"], "합성 조건 테스트 설명")
                self.assertIn("<b>합성 조건</b>", row["condition_html"])
                self.assertEqual(tip["text_ko"], "합성 심화 설명입니다.")
                self.assertFalse(guide["public_storage_allowed"])

    def test_mutated_evidence_cannot_attach_to_wrong_rule(self):
        with TemporaryDirectory() as tmp:
            src = Path(tmp) / "source.html"
            src.write_text(SOURCE, encoding="utf-8")
            _, _, guides = public_fixture(self.baseline)
            guides[0]["rotation_groups"][0]["rules"][0]["provenance"][
                "v11_fragment_sha256"] = "0" * 64
            with self._patch_data(guides[0]), patch(
                "engine.v2.detail_bridge.validate", return_value={"ok": True}
            ):
                with self.assertRaisesRegex(ValueError, "V11 rule hash mismatch"):
                    extract_details(src)

    def test_refuses_to_write_private_text_under_public_repository(self):
        with self.assertRaisesRegex(ValueError, "GitHub repository"):
            export_private(Path("/not/used.html"),
                           Path(__file__).resolve().parents[1] / "dist" / "details")

    def test_baseline_mismatch_before_extraction(self):
        with TemporaryDirectory() as tmp:
            src = Path(tmp) / "source.html"
            src.write_text(SOURCE, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "V11 baseline mismatch"):
                extract_details(src, expected_sha256="f" * 64)


if __name__ == "__main__":
    unittest.main()
