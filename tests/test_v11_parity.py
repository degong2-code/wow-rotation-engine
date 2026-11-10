"""Offline round-trip tests with synthetic HTML only; never check in real V11 text."""
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from engine.v2.parity import verify_v11
from engine.v2.patch_v11 import rebuild_v2


HEROES = (
    ("fire", "sunfury"),
    ("frost", "spellslinger"),
    ("dk", "deathbringer"),
    ("hunter", "sentinel"),
    ("bm", "packleader"),
    ("rogue", "trickster"),
    ("assassination", "fatebound"),
)


def synthetic_v11() -> str:
    controls = "".join(
        f'<button data-guide-button="{gid}" data-hero-button="{hero}">{gid}</button>'
        for gid, hero in HEROES
    )
    navigation = "".join(
        f'<nav class="reader-toc" data-nav-guide="{gid}">'
        f'<a data-target="{gid}-overview" href="#{gid}-overview">Overview</a></nav>'
        for gid, _ in HEROES
    )
    guides = "".join(
        f'<div class="manual-view" data-guide="{gid}" data-hero="{hero}" id="guide-{gid}">'
        f'<div class="intro"><h1>{gid} 합성 시험</h1></div>'
        f'<section class="overview" id="{gid}-overview">'
        f'<h2>{gid} 합성 개요</h2><p>실제 WoW 공략이 아닌 시험 자료.</p></section>'
        f'<footer>합성 종료 {gid}</footer></div>'
        for gid, hero in HEROES
    )
    return (
        '<!doctype html><html lang="ko"><head><meta charset="utf-8">'
        '<title>합성 V11 시험</title></head><body>'
        f'<header><nav>{controls}</nav></header>{navigation}'
        f'<main>{guides}</main><script>const synthetic=true;</script></body></html>'
    )


class V11ParityTests(unittest.TestCase):
    def test_roundtrip_preserves_all_bytes_in_private_workspace(self):
        with TemporaryDirectory() as tmp:
            original = Path(tmp) / "private-v11.html"
            payload = synthetic_v11().encode("utf-8")
            original.write_bytes(payload)
            report = verify_v11(
                original,
                expected_sha256=hashlib.sha256(payload).hexdigest(),
                expected_size_bytes=len(payload),
            )
            self.assertTrue(report["byte_identical"])
            self.assertEqual(report["guide_count"], 7)
            self.assertEqual(report["chapter_count"], 7)
            self.assertEqual(report["size_bytes"], len(payload))
            self.assertFalse(report["source_content_published"])
            self.assertEqual({p.name for p in Path(tmp).iterdir()}, {"private-v11.html"})

    def test_wrong_baseline_hash_is_rejected_before_import(self):
        with TemporaryDirectory() as tmp:
            original = Path(tmp) / "v11.html"
            original.write_text(synthetic_v11(), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                verify_v11(original, expected_sha256="0" * 64)
            self.assertEqual({p.name for p in Path(tmp).iterdir()}, {"v11.html"})

    def test_wrong_baseline_size_is_rejected(self):
        with TemporaryDirectory() as tmp:
            original = Path(tmp) / "v11.html"
            payload = synthetic_v11().encode("utf-8")
            original.write_bytes(payload)
            with self.assertRaisesRegex(ValueError, "source size mismatch"):
                verify_v11(
                    original,
                    expected_sha256=hashlib.sha256(payload).hexdigest(),
                    expected_size_bytes=len(payload) + 1,
                )


    def test_v2_builder_retains_original_ui_after_one_synthetic_detail_edit(self):
        original = synthetic_v11()
        updated = original.replace(
            "<p>실제 WoW 공략이 아닌 시험 자료.</p>",
            "<p>수정된 합성 장 설명입니다.</p>",
            1,
        )
        self.assertNotEqual(original, updated)
        self.assertEqual(rebuild_v2(updated.encode("utf-8")), updated.encode("utf-8"))
        self.assertIn("<title>합성 V11 시험</title>", updated)
        self.assertEqual(updated.count('class="manual-view"'), 7)

if __name__ == "__main__":
    unittest.main()
