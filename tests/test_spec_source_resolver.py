"""Generic Korean-English specialization resolution, without network or game logic."""
import unittest
from engine.spec_source_resolver import (
    SPECIALIZATIONS, AmbiguousSpecialization, UnknownSpecialization,
    resolve_specialization,
)


class SpecSourceResolverTests(unittest.TestCase):
    def test_all_current_class_spec_entries_have_unique_urls(self):
        self.assertEqual(len(SPECIALIZATIONS), 40)
        self.assertEqual(len({s.guide_url for s in SPECIALIZATIONS}), 40)
        for spec in SPECIALIZATIONS:
            self.assertEqual(resolve_specialization(spec.korean_name), spec)
            self.assertEqual(resolve_specialization(spec.english_name), spec)
            self.assertEqual(resolve_specialization(
                f"{spec.class_en} {spec.spec_en}"), spec)
            self.assertTrue(spec.guide_url.endswith("/rotation-cooldowns-pve-dps"))
            self.assertTrue(spec.guide_url.startswith("https://www.wowhead.com/guide/classes/"))

    def test_user_typical_korean_input(self):
        cases = {
            "고양 주술사": "shaman/enhancement",
            "고양": "shaman/enhancement",
            "비전 마법사": "mage/arcane",
            "비전": "mage/arcane",
            "사격 사냥꾼": "hunter/marksmanship",
            "냉기 죽음의 기사": "death-knight/frost",
            "냉죽": "death-knight/frost",
            "냉법": "mage/frost",
            "생냥": "hunter/survival",
            "포식 악마사냥꾼": "demon-hunter/devourer",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(resolve_specialization(value).key, expected)

    def test_identical_specialization_names_fail_without_class(self):
        for label in ("냉기", "신성", "Restoration", "Frost", "protection"):
            with self.subTest(label=label), self.assertRaises(AmbiguousSpecialization):
                resolve_specialization(label)

    def test_english_case_spacing(self):
        spec = resolve_specialization("  ENHANCEMENT    SHAMAN  ")
        self.assertEqual(spec.guide_url,
                         "https://www.wowhead.com/guide/classes/shaman/enhancement/rotation-cooldowns-pve-dps")

    def test_urls_not_derived_from_unsafe_user_strings(self):
        for text in ("", "../admin", "https://example.com", "shaman/enhancement",
                     "unknown mage", "고양 주술사?"):
            with self.subTest(query=text), self.assertRaises(UnknownSpecialization):
                resolve_specialization(text)

    def test_alias_collision_free_for_full_spec_name(self):
        for spec in SPECIALIZATIONS:
            self.assertEqual(resolve_specialization(spec.korean_name).key, spec.key)


if __name__ == "__main__":
    unittest.main()
