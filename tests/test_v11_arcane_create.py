"""Synthetic-only contract tests for Arcane CREATE and V11 byte preservation."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from engine.v2.build import ROOT, read_json, render, validate
from engine.v2.create_guide import (
    JS_PATCHES, OLD_IDS, create_arcane, create_private_preview,
    validate_draft, _original_guides,
)
from engine.v2.import_v11 import bootstrap


ARCANE_JSON = ROOT / "content" / "new_guides" / "arcane.json"
FIRE_BUTTON = (
    '<button class="guide-select active" data-guide-button="fire" '
    'data-hero-button="sunfury" type="button">성난태양</button>'
)
FROST_VIEW = (
    '<div class="manual-view" data-guide="frost" data-hero="spellslinger" '
    'id="guide-frost">'
)


def synthetic_original():
    toc = "".join(
        '<div class="reader-toc" data-nav-guide="' + gid + '"'
        + (' hidden=""' if gid != "fire" else "")
        + '><a href="#' + ("overview" if gid == "fire" else gid + "-overview")
        + '" data-target="' + ("overview" if gid == "fire" else gid + "-overview")
        + '">개요</a></div>'
        for gid in OLD_IDS
    )
    buttons = (
        FIRE_BUTTON
        + '<div class="tree-spec">냉기 <small>FROST</small></div>'
        + '<button data-guide-button="frost" data-hero-button="spellslinger">주문술사</button>'
    )
    old_views = []
    for gid in OLD_IDS:
        start = (
            '<div class="manual-view'
            + (' active' if gid == "fire" else "")
            + '" data-guide="' + gid + '"'
            + (' data-hero="spellslinger"' if gid == "frost" else "")
            + ' id="guide-' + gid + '">'
        )
        overview = "overview" if gid == "fire" else gid + "-overview"
        old_views.append(
            start
            + '<div class="intro"><h1>' + gid + ' 원본</h1></div>'
            + '<section class="overview" id="' + overview
            + '"><h2>' + gid + ' 개요</h2></section></div>'
        )
    # Every exact JS rewriting anchor is represented by synthetic code tokens
    # only: the user's original V11 script and text are NOT checked into CI.
    original_js_anchors = "\n".join(old for old, new in JS_PATCHES)
    return (
        '<!doctype html><html lang="ko"><head><style>'
        'body{font-family:system-ui}</style></head><body>'
        '<nav class="toc"><div class="tree">' + buttons + '</div>' + toc + '</nav>'
        '<main class="reader">' + "".join(old_views) + '</main>'
        '<script>' + original_js_anchors + '</script></body></html>'
    )


class ArcaneCreateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.draft = json.loads(ARCANE_JSON.read_text(encoding="utf-8"))
        cls.original = synthetic_original()
        cls.baseline_hash = hashlib.sha256(cls.original.encode("utf-8")).hexdigest()

    def create(self, document=None):
        with patch("engine.v2.create_guide.BASELINE_SHA", self.baseline_hash):
            return create_arcane(
                self.original.encode("utf-8"),
                self.draft if document is None else document,
            )

    def test_private_create_defaults_to_no_rejected_legacy_baseline(self):
        # The previous tool accepted an unapproved pre-canonical Arcane draft
        # as its implicit default. Refuse it before touching private V11 bytes.
        with TemporaryDirectory() as temp:
            root = Path(temp)
            private = root / "original-private.html"
            private.write_text(self.original, encoding="utf-8")
            bad = root / "historical-arcane-draft.json"
            bad.write_text(json.dumps(self.draft), encoding="utf-8")
            output = root / "result.html"
            with self.assertRaisesRegex(ValueError, "Legacy handwritten"):
                create_private_preview(private, bad, output)
            self.assertFalse(output.exists())

    def test_old_draft_can_only_be_replayed_as_explicit_review_comparison(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            private = root / "original-private.html"
            private.write_text(self.original, encoding="utf-8")
            old = root / "historical-arcane-draft.json"
            old.write_text(json.dumps(self.draft), encoding="utf-8")
            output = root / "historical-comparison.html"
            with patch("engine.v2.create_guide.BASELINE_SHA", self.baseline_hash):
                report = create_private_preview(
                    private, old, output, allow_legacy_review=True
                )
            self.assertTrue(output.exists())
            self.assertEqual(
                report["content_basis"], "historical_legacy_comparison_only"
            )
            self.assertFalse(report["gameplay_accuracy_verified"])
            self.assertFalse(report["approved_visual_baseline_verified"])

    def test_canonical_draft_is_normal_private_create_path(self):
        draft = deepcopy(self.draft)
        rules = []
        for hero in ("sunfury", "spellslinger"):
            for rank in range(1, 10):
                rules.append({
                    "id": f"source-{hero}-{rank}",
                    "kind": "priority", "rank": rank, "step": None,
                    "context": {"hero": hero}, "action": "비전 탄막",
                    "when": (
                        [{"field": "target_count", "op": "gte", "value": 5}]
                        if rank == 9 else
                        [{"field": "arcane_charges", "op": "lt", "value": 3}]
                        if rank == 1 else []
                    ),
                    "condition_text": (
                        "비전 충전물 3개 미만" if rank == 1
                        else "합성 출처의 선택 조건"
                    ),
                    "reason": "합성 근거에만 기초한 검토 설명",
                    "exceptions": [],
                })
        draft["canonical_priority_rules"] = rules
        with TemporaryDirectory() as temp:
            root = Path(temp)
            private = root / "original-private.html"
            private.write_text(self.original, encoding="utf-8")
            source = root / "source-first.json"
            source.write_text(json.dumps(draft), encoding="utf-8")
            output = root / "canonical-private.html"
            with patch("engine.v2.create_guide.BASELINE_SHA", self.baseline_hash):
                report = create_private_preview(private, source, output)
            self.assertTrue(output.exists())
            self.assertEqual(report["arcane_priority_rows"], 34)
            self.assertEqual(
                report["content_basis"], "canonical_source_rules_review_required"
            )
            self.assertFalse(report["gameplay_accuracy_verified"])
            self.assertFalse(report["approved_visual_baseline_verified"])
            self.assertIn(
                'data-canonical-id="source-sunfury-1"',
                output.read_text(encoding="utf-8")
            )

    def test_real_draft_is_review_gated_with_two_heroes_and_four_scenarios(self):
        counts = validate_draft(self.draft)
        self.assertEqual(counts["row_count"], 34)
        self.assertEqual(counts["tip_count"], 10)
        self.assertEqual(counts["group_count"], 4)
        self.assertEqual(len(self.draft["spells"]), 12)
        self.assertFalse(self.draft["publication"]["automatic_publish_allowed"])

    def test_one_patch_aligned_baseline_source_suffices(self):
        draft = deepcopy(self.draft)
        draft["sources"] = draft["sources"][:1]
        counts = validate_draft(draft)
        self.assertEqual(counts["row_count"], 34)

    def test_no_baseline_source_is_rejected(self):
        draft = deepcopy(self.draft)
        draft["sources"] = []
        with self.assertRaisesRegex(ValueError, "baseline source"):
            validate_draft(draft)

    def test_canonical_source_rows_override_legacy_handwritten_tables(self):
        from engine.v2.create_guide import project_canonical_arcane_draft
        draft = deepcopy(self.draft)
        original_legacy_condition = draft["rotation_groups"][0]["rows"][0]["condition"]
        draft["rotation_groups"][0]["rows"][0]["condition"] = "INVALID LEGACY TEXT"
        canon = []
        for hero in ("sunfury", "spellslinger"):
            for rank in range(1, 10):
                rule = {
                    "id": f"synthetic-{hero}-{rank}",
                    "kind": "priority", "rank": rank, "step": None,
                    "context": {"hero": hero}, "action": "비전 탄막",
                    "when": (
                        [{"field": "target_count", "op": "gte", "value": 5}]
                        if rank == 9 else
                        [{"field": "arcane_charges", "op": "lt", "value": 3}]
                        if rank == 1 else []
                    ),
                    "condition_text": (
                        "비전 충전물 3개 미만" if rank == 1
                        else "합성 출처의 선택 조건"
                    ),
                    "reason": "원문 기반 합성 설명",
                    "exceptions": [],
                }
                canon.append(rule)
        draft["canonical_priority_rules"] = canon
        projected = project_canonical_arcane_draft(draft)
        self.assertTrue(all("priority_shadow_audit" in g
                            for g in projected["rotation_groups"]))
        self.assertTrue(all(not g["priority_shadow_audit"]["source_meaning_verified"]
                            for g in projected["rotation_groups"]))
        self.assertEqual(
            [len(g["rows"]) for g in projected["rotation_groups"]],
            [8, 9, 8, 9]
        )
        self.assertEqual(
            projected["rotation_groups"][0]["rows"][0]["source_rule_id"],
            "synthetic-sunfury-1"
        )
        self.assertEqual(
            projected["rotation_groups"][0]["rows"][0]["condition"],
            "비전 충전물 3개 미만"
        )
        self.assertNotEqual(
            projected["rotation_groups"][0]["rows"][0]["condition"],
            original_legacy_condition
        )
        data, report = self.create(draft)
        result = data.decode("utf-8")
        self.assertEqual(report["arcane_priority_rows"], 34)
        self.assertEqual(report["priority_shadow_audit"]["views_checked"], 4)
        self.assertFalse(report["priority_shadow_audit"]["gameplay_meaning_verified"])
        self.assertIn('data-canonical-id="synthetic-sunfury-1"', result)
        self.assertIn('<strong>이유</strong> 원문 기반 합성 설명', result)
        self.assertNotIn("INVALID LEGACY TEXT", result)
        self.assertTrue(report["old_seven_byte_identical"])

    def test_adds_eighth_guide_and_preserves_seven_original_views_exactly(self):
        data, report = self.create()
        updated = data.decode("utf-8")
        old = _original_guides(self.original)
        new = _original_guides(updated)
        self.assertEqual(set(new), {*OLD_IDS, "arcane"})
        self.assertTrue(all(old[gid] == new[gid] for gid in OLD_IDS))
        self.assertTrue(report["old_seven_byte_identical"])
        self.assertEqual(report["guide_count"], 8)
        self.assertEqual(report["arcane_priority_rows"], 34)
        self.assertEqual(report["arcane_advanced_tips"], 10)
        self.assertEqual(updated.count('data-guide-button="arcane"'), 2)
        self.assertIn("arcaneHero='sunfury'", updated)
        self.assertIn("arcane:'arcane-overview'", updated)
        self.assertIn("arcane:'arcane-rotation'", updated)
        self.assertIn("if(id.startsWith('arcane-'))", updated)
        self.assertIn('data-nav-guide="arcane"', updated)
        self.assertIn('data-hero="spellslinger"', updated)
        self.assertIn('data-hero="sunfury"', updated)
        self.assertIn('id="arcane-rotation"', updated)

    def test_full_v2_reimport_and_rebuild_are_byte_identical_with_eight(self):
        generated, _ = self.create()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "private-arcane.html"
            src.write_bytes(generated)
            workspace = root / "workspace"
            bootstrap(src, destination_root=workspace)
            registry = read_json(workspace / "content" / "registry.json")
            html, guides = render(registry, root=workspace)
            self.assertEqual(html.encode("utf-8"), generated)
            self.assertEqual(registry["guides"][1]["id"], "arcane")
            self.assertEqual(len(guides), 8)
            self.assertEqual(validate(registry, guides, html), [])

    def test_spellslinger_bolt_logic_is_grouped_and_spell_ids_have_evidence(self):
        groups = {group["id"]: group for group in self.draft["rotation_groups"]}
        barrage = groups["arcane:rotation:spellslinger-st"]["rows"][1]
        self.assertEqual(barrage["spell"], "비전 탄막")
        self.assertIn("비전 충전물 4개", barrage["comment"])
        self.assertIn("오프너에서는 예외", barrage["comment"])
        opening = groups["arcane:rotation:spellslinger-st"]["rows"][0]
        self.assertEqual(opening["spell"], "오색 화살")
        self.assertIn("비전 연사가 13중첩 초과이며, (", opening["condition"])
        self.assertIn("축적된 힘 6중첩 이상 또는 번뜩임 없음 또는 4세트 미보유", opening["condition"])
        spells = {spell["key"]: spell for spell in self.draft["spells"]}
        self.assertEqual(spells["prismatic-bolt"]["id"], 1295924)
        self.assertEqual(spells["cumulative-power"]["id"], 1296930)
        self.assertIsNone(spells["prismatic-bolt"]["icon"])
        self.assertFalse(self.draft["publication"]["automatic_publish_allowed"])
        evidence = self.draft["source_verification"]["verified"]
        self.assertTrue(any(i.get("spell_id") == 1295924 for i in evidence))
        self.assertTrue(any(i.get("spell_id") == 1296930 for i in evidence))

    def test_rejects_unreviewed_publication(self):
        draft = deepcopy(self.draft)
        draft["publication"]["automatic_publish_allowed"] = True
        with self.assertRaisesRegex(ValueError, "blocked pending review"):
            self.create(draft)

    def test_rejects_missing_spellslinger_scenario(self):
        draft = deepcopy(self.draft)
        draft["rotation_groups"] = draft["rotation_groups"][:-1]
        with self.assertRaisesRegex(ValueError, "four|both heroes"):
            self.create(draft)

    def test_rejects_untrusted_icon_path(self):
        draft = deepcopy(self.draft)
        draft["spells"][0]["icon"] = "../malicious.js"
        with self.assertRaisesRegex(ValueError, "icon"):
            self.create(draft)

    def test_refuses_unrecognized_original_html_source(self):
        with self.assertRaisesRegex(ValueError, "exact unmodified V11"):
            create_arcane(b"<html></html>", self.draft)

    def test_refuses_missing_original_script_anchor(self):
        source = self.original.replace(
            "const views={fire:document.getElementById('guide-fire'),frost:",
            "const views={fire:null,frost:",
        )
        with patch(
            "engine.v2.create_guide.BASELINE_SHA",
            hashlib.sha256(source.encode("utf-8")).hexdigest(),
        ):
            with self.assertRaisesRegex(ValueError, "script extension"):
                create_arcane(source.encode("utf-8"), self.draft)

    def test_created_arcane_contains_no_unreviewed_spell_id_for_unknown_spells(self):
        generated, _ = self.create()
        self.assertIn("오색 화살", generated.decode("utf-8"))
        self.assertIn("spell ID 미확인", generated.decode("utf-8"))
        self.assertNotIn('automatic_publish_allowed="true"', generated.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
