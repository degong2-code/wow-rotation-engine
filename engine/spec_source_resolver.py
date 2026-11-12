"""Resolve exact Korean/English WoW specialization names to canonical guide URLs.

No arbitrary URLs from model text, no fuzzy guesses, and no fixed hero/opening
branches. The returned URL is a candidate; the downloaded HTML title and
revision still require independent checks before an editorial workflow.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

WOWHEAD_ROOT = "https://www.wowhead.com/guide/classes"
ROTATION_SUFFIX = "rotation-cooldowns-pve-dps"


class SpecializationResolutionError(ValueError):
    pass


class AmbiguousSpecialization(SpecializationResolutionError):
    pass


class UnknownSpecialization(SpecializationResolutionError):
    pass


@dataclass(frozen=True)
class Specialization:
    class_slug: str
    class_en: str
    class_ko: str
    spec_slug: str
    spec_en: str
    spec_ko: str

    @property
    def guide_url(self) -> str:
        return f"{WOWHEAD_ROOT}/{self.class_slug}/{self.spec_slug}/{ROTATION_SUFFIX}"

    @property
    def key(self) -> str:
        return f"{self.class_slug}/{self.spec_slug}"

    @property
    def english_name(self) -> str:
        return f"{self.spec_en} {self.class_en}"

    @property
    def korean_name(self) -> str:
        return f"{self.spec_ko} {self.class_ko}"


# Class/category taxonomy is not a rotation guide or talent build. Talent,
# potion and additional guide UI switches are discovered from live source.
# Each entry (URL slug, official-ish English name, Korean specialization).
_DATA = (
    ("warrior", "Warrior", "전사", (
        ("arms", "Arms", "무기"), ("fury", "Fury", "분노"), ("protection", "Protection", "방어"))),
    ("paladin", "Paladin", "성기사", (
        ("holy", "Holy", "신성"), ("protection", "Protection", "보호"),
        ("retribution", "Retribution", "징벌"))),
    ("hunter", "Hunter", "사냥꾼", (
        ("beast-mastery", "Beast Mastery", "야수"), ("marksmanship", "Marksmanship", "사격"),
        ("survival", "Survival", "생존"))),
    ("rogue", "Rogue", "도적", (
        ("assassination", "Assassination", "암살"), ("outlaw", "Outlaw", "무법"),
        ("subtlety", "Subtlety", "잠행"))),
    ("priest", "Priest", "사제", (
        ("discipline", "Discipline", "수양"), ("holy", "Holy", "신성"),
        ("shadow", "Shadow", "암흑"))),
    ("shaman", "Shaman", "주술사", (
        ("elemental", "Elemental", "정기"), ("enhancement", "Enhancement", "고양"),
        ("restoration", "Restoration", "복원"))),
    ("mage", "Mage", "마법사", (
        ("arcane", "Arcane", "비전"), ("fire", "Fire", "화염"),
        ("frost", "Frost", "냉기"))),
    ("warlock", "Warlock", "흑마법사", (
        ("affliction", "Affliction", "고통"), ("demonology", "Demonology", "악마"),
        ("destruction", "Destruction", "파괴"))),
    ("monk", "Monk", "수도사", (
        ("brewmaster", "Brewmaster", "양조"), ("mistweaver", "Mistweaver", "운무"),
        ("windwalker", "Windwalker", "풍운"))),
    ("druid", "Druid", "드루이드", (
        ("balance", "Balance", "조화"), ("feral", "Feral", "야성"),
        ("guardian", "Guardian", "수호"), ("restoration", "Restoration", "회복"))),
    ("demon-hunter", "Demon Hunter", "악마사냥꾼", (
        ("havoc", "Havoc", "파멸"), ("vengeance", "Vengeance", "복수"),
        ("devourer", "Devourer", "포식"))),
    ("death-knight", "Death Knight", "죽음의 기사", (
        ("blood", "Blood", "혈기"), ("frost", "Frost", "냉기"),
        ("unholy", "Unholy", "부정"))),
    ("evoker", "Evoker", "기원사", (
        ("devastation", "Devastation", "황폐"), ("preservation", "Preservation", "보존"),
        ("augmentation", "Augmentation", "증강"))),
)

SPECIALIZATIONS: tuple[Specialization, ...] = tuple(
    Specialization(cls, en, ko, slug, sen, sko)
    for cls, en, ko, specs in _DATA for slug, sen, sko in specs
)

CLASS_ALIASES = {
    "warrior": ("전사",), "paladin": ("성기사", "기사"),
    "hunter": ("사냥꾼", "냥꾼"), "rogue": ("도적",),
    "priest": ("사제",), "shaman": ("주술사", "술사"),
    "mage": ("마법사", "법사"), "warlock": ("흑마법사", "흑마"),
    "monk": ("수도사",), "druid": ("드루이드", "드루"),
    "demon-hunter": ("악마사냥꾼", "악사"),
    "death-knight": ("죽음의 기사", "죽기"),
    "evoker": ("기원사",),
}

SHORT_NAMES = {
    "death-knight/frost": ("냉죽",), "mage/frost": ("냉법",),
    "mage/fire": ("화법",), "mage/arcane": ("비법",),
    "hunter/beast-mastery": ("야냥",), "hunter/marksmanship": ("격냥",),
    "hunter/survival": ("생냥",), "warrior/arms": ("무전",),
    "warrior/fury": ("분전",), "shaman/enhancement": ("고술",),
    "shaman/elemental": ("정술",),
}


def _normalize(value: str) -> str:
    return re.sub(r"[\s\u00b7\-_/()]+", "", value.casefold())


def _keys(spec: Specialization) -> set[str]:
    aliases = {spec.spec_ko, spec.spec_en, spec.spec_slug,
               f"{spec.spec_en} {spec.class_en}",
               f"{spec.class_en} {spec.spec_en}"}
    for cls in CLASS_ALIASES[spec.class_slug]:
        aliases.add(f"{spec.spec_ko} {cls}")
        aliases.add(f"{cls} {spec.spec_ko}")
    aliases.update(SHORT_NAMES.get(spec.key, ()))
    return {_normalize(x) for x in aliases}


ALIASES: dict[str, tuple[Specialization, ...]] = {}
for _item in SPECIALIZATIONS:
    for _alias in _keys(_item):
        ALIASES[_alias] = (*ALIASES.get(_alias, ()), _item)


def resolve_specialization(query: str) -> Specialization:
    """Resolve exact class/spec or unambiguous spec alone; never guess."""
    if not isinstance(query, str) or not query.strip() or len(query) > 100:
        raise UnknownSpecialization("유효한 전문화 이름을 입력해야 합니다.")
    choices = ALIASES.get(_normalize(query), ())
    if not choices:
        raise UnknownSpecialization("알 수 없는 전문화입니다. '고양 주술사'처럼 입력하세요.")
    if len(choices) > 1:
        names = " / ".join(sorted(s.korean_name for s in choices))
        raise AmbiguousSpecialization(
            f"'{query}'은(는) 여러 전문화에 해당합니다: {names}. 직업까지 명시하세요."
        )
    return choices[0]
