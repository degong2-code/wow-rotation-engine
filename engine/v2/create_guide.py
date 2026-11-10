"""Add an original authored, review-pending Arcane guide to PRIVATE V11 HTML.

The input V11 HTML is never committed to this public repository. Existing seven
guide DOM subtrees are preserved byte-for-byte. The original CSS, icon/tooltip
logic and navigation design are reused, with a targeted extension to support
the eighth guide and its two hero talents.

Usage:
  python -m engine.v2.create_guide /private/v11.html \
    --draft content/new_guides/arcane.json --output /private/v11-with-arcane.html
"""
from __future__ import annotations

import argparse
from collections import Counter
from html import escape
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from .build import ROOT
from .html_spans import SpanParser, find_class
from .fidelity import audit_create_fragment
from .annotations import validate_notes, render_note, render_legend
from .mechanics import validate as validate_mechanics, render_flows, render_comparisons, rich

BASELINE_SHA = "5d70279c4dd073eccef1f3b13565a8f555cd81c9f0a5b7eda7e3485e410742be"
OLD_IDS = ("fire", "frost", "dk", "hunter", "bm", "rogue", "assassination")
HERO_IDS = ("sunfury", "spellslinger")
ICON_RE = re.compile(r"^[a-z0-9_]+$")
SOURCE_HOSTS = ("www.wowhead.com", "www.icy-veins.com", "www.method.gg",
                "worldofwarcraft.blizzard.com")


def _e(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Guide text fields must be strings")
    return escape(value, quote=True)


def _hash(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _replace_once(text: str, old: str, new: str, description: str) -> str:
    number = text.count(old)
    if number != 1:
        raise ValueError(f"{description}: expected one V11 anchor, got {number}")
    return text.replace(old, new, 1)


def validate_draft(doc: dict) -> dict:
    if not isinstance(doc, dict) or doc.get("schema_version") != "new-v11-guide-v1":
        raise ValueError("Unsupported new-guide schema")
    if doc.get("id") != "arcane" or doc.get("spec_ko") != "비전":
        raise ValueError("Arcane pilot only; cannot silently replace existing guides")
    if doc.get("publication") != {
        "status": "draft_review_required",
        "automatic_publish_allowed": False,
        "source_translations_copied": False,
    }:
        raise ValueError("New guide publication must remain blocked pending review")
    if [x.get("id") for x in doc["heroes"]] != list(HERO_IDS):
        raise ValueError("Arcane must support Sunfury and Spellslinger")
    if doc.get("default_hero") not in HERO_IDS:
        raise ValueError("Arcane default hero must be declared")

    sources = doc["sources"]
    if len(sources) < 2:
        raise ValueError("Require at least two source references")
    for src in sources:
        parsed = urlsplit(src["url"])
        if parsed.scheme != "https" or parsed.hostname not in SOURCE_HOSTS:
            raise ValueError("Guide source must be from an approved HTTPS guide site")
        if not src.get("checked_on") or not src.get("role"):
            raise ValueError("Incomplete guide source provenance")

    editorial = doc.get("editorial")
    if not isinstance(editorial, dict) or editorial.get("version") != "v11-editorial-v1":
        raise ValueError("V11 CREATE editorial contract is required")
    overview = editorial.get("overview", {})
    if not overview.get("lead") or len(overview.get("decision_order", [])) < 3 or not overview.get("caution"):
        raise ValueError("Missing V11 decision-first overview explanations")
    mandatory = {"pre", "basics", "opener", "rotation", "advanced", "glossary"}
    chapters = editorial.get("chapters", {})
    if not mandatory.issubset(chapters) or any(
        not chapters[name].get("lead") or not chapters[name].get("caution")
        for name in mandatory
    ):
        raise ValueError("Each V11 CREATE chapter requires context and exception")
    if len(editorial.get("cooldowns", [])) < 2 or len(editorial.get("practice", [])) < 2:
        raise ValueError("Missing cooldown explanations or decision examples")
    for item in editorial["cooldowns"]:
        if not all(item.get(key) for key in ("title", "principle", "decision", "exception")):
            raise ValueError("Incomplete cooldown explanation")
        if item.get("review") != "needs_manual_gameplay_review":
            raise ValueError("Cannot approve unreviewed cooldown")
    for item in editorial["practice"]:
        if not all(item.get(key) for key in ("question", "reasoning", "caution")):
            raise ValueError("Incomplete decision exercise")
    if editorial.get("review_policy", {}).get("publication_blocked") is not True:
        raise ValueError("Review gate cannot be bypassed")

    spells = {}
    for spell in doc["spells"]:
        if not re.fullmatch("[a-z0-9-]+", spell["key"]):
            raise ValueError("Invalid spell key")
        if not spell.get("hint") or len(spell["hint"]) < 15:
            raise ValueError("CREATE spell tooltips require meaningful explanations")
        if spell["ko"] in spells:
            raise ValueError("Duplicate Arcane spell")
        if spell["icon"] is not None and not ICON_RE.fullmatch(spell["icon"]):
            raise ValueError("Untrusted icon filename")
        if spell["id"] is not None and (
            type(spell["id"]) is not int or spell["id"] <= 0
        ):
            raise ValueError("Invalid spell ID")
        spells[spell["ko"]] = spell

    groups = doc["rotation_groups"]
    if len(groups) != 4:
        raise ValueError("Arcane pilot requires both heroes and target modes")
    pairs = []
    row_ids = set()
    for group in groups:
        pairs.append((group["hero"], group["mode"]))
        if group["hero"] not in HERO_IDS or group["mode"] not in ("single", "aoe"):
            raise ValueError("Invalid Arcane rotation scenario")
        if not group.get("intro") or not group.get("caution"):
            raise ValueError("CREATE rotation tables require explanatory context")
        if not group["rows"]:
            raise ValueError("Empty Arcane rotation group")
        for index, row in enumerate(group["rows"], 1):
            if row["id"] != f'{group["id"]}:row-{index}' or row["order"] != index:
                raise ValueError("Arcane rule identity/order mismatch")
            if row["id"] in row_ids:
                raise ValueError("Duplicate Arcane row ID")
            row_ids.add(row["id"])
            if row["spell"] not in spells:
                raise ValueError(f'Unrecognized Arcane spell: {row["spell"]}')
            if row["review"] != "needs_manual_gameplay_review":
                raise ValueError("Cannot declare unreviewed mechanics approved")
            if not row["condition"] or not row["comment"]:
                raise ValueError("Missing Arcane condition or explanation")
    if set(pairs) != set((h, m) for h in HERO_IDS for m in ("single", "aoe")):
        raise ValueError("Missing Arcane hero/target variant")

    tip_ids = set()
    for tip in doc["advanced_guidance"]:
        if tip["id"] in tip_ids or not re.fullmatch(r"arcane:advanced:tip-[1-9]\d*", tip["id"]):
            raise ValueError("Duplicate/invalid Arcane advanced tip")
        tip_ids.add(tip["id"])
        if tip["hero"] not in (*HERO_IDS, "both"):
            raise ValueError("Unknown advanced tip hero")
        if tip["review"] != "needs_manual_gameplay_review":
            raise ValueError("Unreviewed tip cannot be approved")
        if not tip["text"] or not tip["topic"]:
            raise ValueError("Missing advanced tip body")
    validate_mechanics(editorial["mechanics"], doc)
    validate_notes(doc)
    return {
        "spells": spells,
        "row_count": len(row_ids),
        "tip_count": len(tip_ids),
        "group_count": len(groups),
    }


def _spell(spell: dict) -> str:
    ko, en, key = _e(spell["ko"]), _e(spell["en"]), _e(spell["key"])
    title = _e(spell["ko"] + " · " + spell["en"])
    label = _e("전문화 기술 " + spell["ko"] + " 설명")
    # Unverified icon IDs render a neutral text glyph, not an invented image.
    icon = (
        '<span class="spell-icon"><img alt="" loading="lazy" '
        'onerror="this.hidden=true;this.parentElement.classList.add(\'is-missing\')" '
        'src="https://wow.zamimg.com/images/wow/icons/medium/'
        + spell["icon"] + '.jpg"/></span>'
        if spell["icon"] else
        '<span class="spell-icon" aria-hidden="true">✦</span>'
    )
    return (
        '<span class="spell tip-trigger" data-spell="' + key + '" role="button" '
        'tabindex="0" aria-label="' + label + '" data-hint-title="' + title
        + '" data-hint-body="' + _e(spell["hint"]) + '">'
        + icon + '<span>' + ko + '</span></span>'
    )


def _hero_switch(default: str) -> str:
    buttons = "".join(
        f'<button class="hero-choice" type="button" data-select-hero="{key}" '
        f'aria-pressed="{str(key == default).lower()}">{name}</button>'
        for key, name in (("sunfury", "성난태양"), ("spellslinger", "주문술사"))
    )
    return '<div class="hero-switch" role="group" aria-label="비전 영웅 특성 선택"><span>영웅 특성</span>' + buttons + '</div>'


def _aside(title: str, body: str, *, caution: bool = False) -> str:
    modifier = "warn" if caution else "plain"
    return (
        '<aside class="aside ' + modifier + '"><strong>' + _e(title)
        + '</strong><div>' + _e(body) + '</div></aside>'
    )


def _priority(group: dict, spells: dict, number: str, note_for=None) -> str:
    rows = []
    for row in group["rows"]:
        rows.append(
            '<tr data-rule-id="' + _e(row["id"]) + '"><td>' + str(row["order"])
            + '</td><td>' + _spell(spells[row["spell"]])
            + '</td><td><b>' + _e(row["condition"])
            + '</b> ' + (note_for("rule", row["id"]) if note_for else "") + '<div class="muted">' + _e(row["comment"])
            + '</div></td></tr>'
        )
    return (
        '<h3>' + _e(number + " " + group["target_label"]) + '</h3>'
        '<p>' + _e(group["intro"]) + '</p>'
        '<div class="table-scroll"><table class="priority"><thead><tr>'
        '<th>순위</th><th>기술 / 역할</th><th>조건 및 행동</th></tr></thead><tbody>'
        + "".join(rows) + '</tbody></table></div>'
        '<p class="tiny-rule">' + _e(group["caution"]) + '</p>'
    )


def _section(section_id: str, heading: str, body: str, *, number: int = 0,
             kicker: str = "", overview: bool = False) -> str:
    section = "overview" if overview else "chapter"
    if overview:
        title = ('<div class="quick-head"><h2>' + _e(heading)
                 + '</h2><span>QUICK REFERENCE · ARCANE</span></div>')
    else:
        title = (
            '<div class="chapter-heading"><span class="chapter-no">'
            + f'{number:02d}' + '</span><div><h2>' + _e(heading)
            + '</h2><p class="kicker">' + _e(kicker) + '</p></div></div>'
        )
    return ('<section class="' + section + '" id="arcane-' + section_id
            + '">' + title + body + '</section>')



def render_arcane(doc: dict) -> dict:
    meta = validate_draft(doc)
    spellmap = meta["spells"]
    spells_by_key = {spell["key"]: spell for spell in doc["spells"]}
    def link(t): return rich(t, spells_by_key, _spell)
    notes = validate_notes(doc)
    def note_for(kind, identifier):
        note = notes.get((kind, identifier))
        return render_note(note) if note is not None else ""
    hero_labels = {"sunfury": "성난태양", "spellslinger": "주문술사"}
    switch = _hero_switch(doc["default_hero"])
    editorial = doc["editorial"]
    chapters = editorial["chapters"]
    intro = (
        '<div class="intro"><span class="eyebrow">MAGE / ARCANE / SUNFURY · SPELLSLINGER</span>'
        '<h1>비전 마법사 딜사이클 교본</h1>'
        '<p>' + _e(doc["introduction"]) + '</p>'
        '<p class="scope">' + _e(doc["season"] + " · " + doc["patch"] + " · " + doc["scope"]) + '</p>'
        '<p class="route">읽는 순서: 요약 → 준비 → 원리 → 오프너 → 우선순위 → 쿨다운 → 고급 운용 → 판단 연습 → 기술명·출처</p>'
        '</div>'
    )
    overview_variants = []
    for hero in HERO_IDS:
        groups = [g for g in doc["rotation_groups"] if g["hero"] == hero]
        items = [
            '<tr><td>' + _e(g["target_label"]) + '</td><td>'
            + _spell(spellmap[g["rows"][0]["spell"]]) + " — "
            + _e(g["rows"][0]["condition"])
            + '<div class="muted">' + _e(g["rows"][0]["comment"]) + '</div>'
            + '</td></tr>' for g in groups
        ]
        overview_variants.append(
            '<div class="variant" data-hero="' + hero + '"><h3>'
            + hero_labels[hero] + ' · 핵심 판단</h3>'
            '<div class="table-scroll"><table class="overview-table"><thead><tr>'
            '<th>전투 상황</th><th>우선 확인할 기술</th></tr></thead><tbody>'
            + "".join(items) + '</tbody></table></div></div>'
        )

    overview = (
        '<p>' + _e(editorial["overview"]["lead"]) + '</p>' + switch + render_legend()
        + "".join(overview_variants)
        + '<h3>읽는 순서</h3><ol class="principles">'
        + "".join('<li>' + _e(value) + '</li>' for value in editorial["overview"]["decision_order"])
        + '</ol>' + _aside('영웅 특성 구분', editorial["overview"]["caution"])
    )
    pre = (
        '<p>' + link(chapters["pre"]["lead"]) + '</p>'
        + '<ul class="simple-list">' + "".join(
            '<li>' + _e(value) + '</li>' for value in doc["preparation"]
        ) + '</ul>' + _aside('사전 준비 예외', chapters["pre"]["caution"])
    )
    principles = (
        '<p>' + _e(chapters["basics"]["lead"]) + '</p>'
        + "".join(
            '<h3>' + _e(item["heading"]) + '</h3><p>' + _e(item["body"]) + '</p>'
            for item in doc["principles"]
        )
        + render_flows(editorial["mechanics"], "basics", spells_by_key, _spell, note_for)
        + render_comparisons(editorial["mechanics"], spells_by_key, _spell, note_for)
        + _aside('조건을 읽을 때', chapters["basics"]["caution"])
    )
    opener = (
        '<p>' + _e(chapters["opener"]["lead"]) + '</p>'
        + '<h3>기본 시전 연결 예시</h3><ol class="steps compact">' + "".join(
            '<li>' + _spell(spellmap[step["action"]]) + ' — '
            + _e(step["condition"]) + ' <span class="muted">'
            + _e(step["note"]) + '</span></li>' for step in doc["opener"]
        ) + '</ol>'
        + render_flows(editorial["mechanics"], "opener", spells_by_key, _spell, note_for)
        + _aside('오프너를 고정 시퀀스로 사용하지 마세요', chapters["opener"]["caution"], caution=True)
    )
    rotations = (
        '<p class="rule">' + _e(chapters["rotation"]["lead"]) + '</p>'
        + "".join(
            '<div class="variant" data-hero="' + hero + '"><h3>'
            + hero_labels[hero] + ' · 시전 우선순위</h3>'
            + "".join(
                _priority(group, spellmap, f"5.{index}", note_for)
                for index, group in enumerate(
                    (g for g in doc["rotation_groups"] if g["hero"] == hero), 1
                )
            ) + '</div>' for hero in HERO_IDS
        )
        + _aside('기본 원칙과 예외', chapters["rotation"]["caution"])
    )
    cooldowns = (
        '<p>핵심 쿨다운은 단순히 사용 가능 여부가 아니라 강화 구간, 대상 유지 시간, '
        '다음 사용 기회를 고려합니다. 아래 설명은 검토 중인 판단 기준입니다.</p>'
        + "".join(
            '<h3>' + _spell(spells_by_key[item["spell_key"]]) + ' · ' + _e(item["title"]) + '</h3>'
            + '<p>' + _e(item["principle"]) + '</p>'
            + '<p><b>사용 판단:</b> ' + link(item["decision"]) + '</p>'
            + '<p><b>예외 및 주의:</b> ' + _e(item["exception"]) + '</p>'
            for item in editorial["cooldowns"]
        )
    )

    shared = []
    only = {h: [] for h in HERO_IDS}
    for tip in doc["advanced_guidance"]:
        item = (
            '<div class="advanced-item" data-tip-id="' + _e(tip["id"]) + '">'
            '<h3>' + _e(tip["topic"]) + '</h3><p>' + link(tip["text"])
            + '</p></div>'
        )
        if tip["hero"] == "both":
            shared.append(item)
        else:
            only[tip["hero"]].append(item)
    advanced = (
        '<p>' + link(chapters["advanced"]["lead"]) + '</p>'
        + "".join(shared) + "".join(
            '<div class="variant" data-hero="' + hero + '">'
            '<h3>' + hero_labels[hero] + ' 전용 판단</h3>'
            + "".join(only[hero]) + '</div>'
            for hero in HERO_IDS
        )
        + _aside('검토 범위', chapters["advanced"]["caution"], caution=True)
    )
    practice = (
        '<p>조건을 암기하는 대신 어떤 판단 요소를 먼저 확인하는지 연습합니다. '
        '아래의 사례는 설명을 위한 가상 상황이지 확정 시전 지시는 아닙니다.</p>'
        + "".join(
            '<h3>' + _e(item["question"]) + '</h3>'
            + '<p>' + link(item["reasoning"]) + '</p>'
            + '<p class="tiny-rule">' + _e(item["caution"]) + '</p>'
            for item in editorial["practice"]
        )
    )
    glossary = (
        '<p>' + _e(chapters["glossary"]["lead"]) + '</p>'
        + '<div class="glossary-list">' + "".join(
            '<div class="glossary-row"><div>' + _spell(spell)
            + '</div><div class="en">' + _e(spell["en"])
            + '<span class="spell-id"> · spell ID '
            + str(spell["id"] or "미확인") + '</span>'
            + '<p>' + _e(spell["hint"]) + '</p></div></div>'
            for spell in doc["spells"]
        ) + '</div>'
        + _aside('기술 식별 검증', chapters["glossary"]["caution"])
    )
    citations = '<h3>공략 근거 및 재검토 링크</h3><ul class="simple-list">' + "".join(
        '<li><a href="' + _e(src["url"]) + '" target="_blank" rel="noopener noreferrer">'
        + _e(urlsplit(src["url"]).hostname or "reference")
        + '</a> · ' + _e(src["role"]) + '</li>' for src in doc["sources"]
    ) + '</ul>'
    notice = _aside(
        '검토 전 초안',
        '현재 비전의 34개 우선순위 행과 10개 고급 팁은 게임플레이 검토 중입니다. '
        '최종 승인 전에는 세부 수치를 확정 가이드로 취급하지 마세요.',
        caution=True,
    )
    sections = [
        ("overview", "한눈에 보는 딜사이클", "QUICK REFERENCE", notice + overview),
        ("pre", "전투 전 준비", "BUILD · SET BONUS · COOLDOWNS", pre),
        ("basics", "핵심 원리", "ARCANE CHARGES · SALVO · CLEARCASTING", principles),
        ("opener", "오프너", "OPENER · COOLDOWN ENTRY", opener),
        ("rotation", "단일·광역 시전 우선순위", "SINGLE TARGET · AOE · HERO TALENTS", rotations),
        ("cooldowns", "주요 쿨다운과 연계", "ARCANE SURGE · TOUCH OF THE MAGI", cooldowns),
        ("advanced", "고급 운용과 예외", "BUFF WINDOWS · RESOURCE MANAGEMENT", advanced),
        ("practice", "상황별 판단 연습", "DECISION PRACTICE · EXCEPTIONS", practice),
        ("glossary", "기술명·출처", "SPELL GLOSSARY · SOURCES & SCOPE", glossary + citations),
    ]
    guide = (
        '<div class="manual-view" data-guide="arcane" data-hero="'
        + _e(doc["default_hero"]) + '" id="guide-arcane">'
        + intro
        + "".join(_section(key, title, body, number=i, kicker=kicker,
                           overview=(key == "overview"))
                  for i, (key, title, kicker, body) in enumerate(sections))
        + '</div>'
    )
    toc = (
        '<div class="reader-toc" data-nav-guide="arcane" hidden="">'
        + "".join(
            f'<a data-target="arcane-{key}" href="#arcane-{key}">'
            f'{i:02d} {_e(title)}</a>'
            for i, (key, title, _, _) in enumerate(sections)
        ) + '</div>'
    )
    buttons = (
        '<div class="tree-spec">비전 <small>ARCANE</small></div>'
        + "".join(
            '<button class="guide-select" type="button" data-guide-button="arcane" '
            'data-hero-button="' + hero + '">' + hero_labels[hero] + '</button>'
            for hero in HERO_IDS
        )
    )
    audit = audit_create_fragment(guide, doc)
    if audit["status"] != "PASS":
        raise ValueError("V11 CREATE fidelity FAIL: " + "; ".join(audit["failures"]))
    return {
        "html": guide, "toc": toc, "buttons": buttons,
        "sections": len(sections),
        "rows": meta["row_count"],
        "tips": meta["tip_count"],
        "fidelity": audit,
    }


JS_PATCHES = (
    ("const views={fire:document.getElementById('guide-fire'),frost:",
     "const views={fire:document.getElementById('guide-fire'),arcane:document.getElementById('guide-arcane'),frost:"),
    ("let current='fire',hero='spellslinger',assassinationHero='fatebound';",
     "let current='fire',hero='spellslinger',assassinationHero='fatebound',arcaneHero='sunfury';"),
    ("current=g;if(g==='frost'&&h)hero=h;",
     "current=g;if(g==='arcane'&&h)arcaneHero=h;if(g==='frost'&&h)hero=h;"),
    ("views.frost.dataset.hero=hero;",
     "views.arcane.dataset.hero=arcaneHero;\n  views.frost.dataset.hero=hero;"),
    ("g==='frost'?b.dataset.heroButton===hero:g==='assassination'?",
     "g==='arcane'?b.dataset.heroButton===arcaneHero:g==='frost'?b.dataset.heroButton===hero:g==='assassination'?"),
    ("const isAssassination=!!c.closest('#guide-assassination');c.setAttribute('aria-pressed',String(c.dataset.selectHero===(isAssassination?assassinationHero:hero)))",
     "const isArcane=!!c.closest('#guide-arcane');const isAssassination=!!c.closest('#guide-assassination');c.setAttribute('aria-pressed',String(c.dataset.selectHero===(isArcane?arcaneHero:isAssassination?assassinationHero:hero)))"),
    ("const ids={fire:'rotation',frost:'frost-rotation'",
     "const ids={fire:'rotation',arcane:'arcane-rotation',frost:'frost-rotation'"),
    ("const overviews={fire:'overview',frost:'frost-overview'",
     "const overviews={fire:'overview',arcane:'arcane-overview',frost:'frost-overview'"),
    ("const title=g==='fire'?'화염 · 성난태양':g==='frost'?",
     "const title=g==='fire'?'화염 · 성난태양':g==='arcane'?'비전 마법사 · '+(arcaneHero==='sunfury'?'성난태양':'주문술사'):g==='frost'?"),
    ("else apply('frost',c.dataset.selectHero,false);",
     "else if(c.closest('#guide-arcane'))apply('arcane',c.dataset.selectHero,false);else apply('frost',c.dataset.selectHero,false);"),
    ("if(id.startsWith('assassination-'))",
     "if(id.startsWith('arcane-'))apply('arcane',null,false);\n  else if(id.startsWith('assassination-'))"),
)

ARCANE_STYLE = """
/* New Arcane guide: reuse V11 styles, select only the active hero variant. */
.manual-view[data-guide="arcane"][data-hero="sunfury"] .variant[data-hero="spellslinger"],
.manual-view[data-guide="arcane"][data-hero="spellslinger"] .variant[data-hero="sunfury"]{display:none!important}
#guide-arcane .priority td{vertical-align:top}
#guide-arcane .priority th:first-child,#guide-arcane .priority td:first-child{width:48px}
#guide-arcane .priority th:nth-child(2),#guide-arcane .priority td:nth-child(2){width:29%}
#guide-arcane .advanced-item{margin:18px 0}
#guide-arcane .advanced-item h3{margin-bottom:6px}
"""


def _original_guides(text: str) -> dict[str, str]:
    parser = SpanParser(text)
    guides = find_class(parser.spans, "div", "manual-view")
    return {sp.attrs["data-guide"]: sp.full(text) for sp in guides}


def create_arcane(source: bytes, draft: dict) -> tuple[bytes, dict]:
    baseline = _hash(source)
    if baseline != BASELINE_SHA:
        raise ValueError(f"Source must be exact unmodified V11 baseline, got {baseline}")
    text = source.decode("utf-8")
    originals = _original_guides(text)
    if set(originals) != set(OLD_IDS):
        raise ValueError("V11 source does not have the canonical seven guides")

    view = render_arcane(draft)
    fire_button = (
        '<button class="guide-select active" data-guide-button="fire" '
        'data-hero-button="sunfury" type="button">성난태양</button>'
    )
    text = _replace_once(text, fire_button,
                         fire_button + view["buttons"], "Arcane sidebar menu")
    text = _replace_once(
        text,
        '<div class="reader-toc" data-nav-guide="frost" hidden="">',
        view["toc"] + '<div class="reader-toc" data-nav-guide="frost" hidden="">',
        "Arcane reader toc",
    )
    text = _replace_once(
        text,
        '<div class="manual-view" data-guide="frost" data-hero="spellslinger" id="guide-frost">',
        view["html"]
        + '<div class="manual-view" data-guide="frost" data-hero="spellslinger" id="guide-frost">',
        "Arcane document insertion",
    )
    text = _replace_once(text, "</style>", ARCANE_STYLE + "\n</style>",
                         "Arcane hero styling")
    for number, (previous, expanded) in enumerate(JS_PATCHES, 1):
        text = _replace_once(text, previous, expanded, f"V11 script extension {number}")

    updated_guides = _original_guides(text)
    if set(updated_guides) != {*OLD_IDS, "arcane"}:
        raise ValueError("Generated guide identities wrong")
    if any(updated_guides[guide_id] != originals[guide_id] for guide_id in OLD_IDS):
        raise ValueError("One of the original seven V11 guides changed")
    soup = BeautifulSoup(text, "html.parser")
    doc_ids = [tag["id"] for tag in soup.select("[id]")]
    if len(doc_ids) != len(set(doc_ids)):
        raise ValueError("Duplicate IDs after Arcane insertion")
    document_ids = set(doc_ids)
    for link in soup.select('a[href^="#"]'):
        dest = link.get("href", "")[1:]
        if dest and dest not in document_ids:
            raise ValueError(f"Broken in-document link: {dest}")
    if len(soup.select('button[data-guide-button="arcane"]')) != 2:
        raise ValueError("Arcane hero sidebar buttons missing")
    if len(soup.select('#guide-arcane .variant[data-hero="sunfury"]')) < 2 or (
        len(soup.select('#guide-arcane .variant[data-hero="spellslinger"]')) < 2
    ):
        raise ValueError("Arcane hero content missing")
    if len(soup.select('#arcane-rotation tbody tr')) != view["rows"]:
        raise ValueError("Wrong Arcane rule table rows")
    if len(soup.select('#arcane-advanced .advanced-item')) != view["tips"]:
        raise ValueError("Wrong Arcane advanced tips")
    report = {
        "status": "PASS",
        "review_required": True,
        "source_v11_sha256": baseline,
        "generated_sha256": _hash(text.encode("utf-8")),
        "guide_count": len(updated_guides),
        "new_guide": "arcane",
        "old_seven_byte_identical": True,
        "arcane_sections": view["sections"],
        "arcane_priority_rows": view["rows"],
        "arcane_advanced_tips": view["tips"],
        "fidelity_components_reused": len(view["fidelity"]["reused_v11_components"]),
        "item_evidence_coverage": view["fidelity"]["evidence_coverage"],
        "gameplay_accuracy_verified": False,
    }
    return text.encode("utf-8"), report


def create_private_preview(source_path: Path, draft_path: Path,
                           output_path: Path) -> dict:
    target = Path(output_path).resolve()
    root = ROOT.resolve()
    if target == root or target.is_relative_to(root):
        raise ValueError("Cannot publish private V11 HTML to the GitHub repository")
    if target == Path(source_path).resolve():
        raise ValueError("Cannot overwrite original V11")
    if target.exists():
        raise FileExistsError("Refusing to overwrite existing Arcane preview")
    draft = json.loads(Path(draft_path).read_text(encoding="utf-8"))
    full, report = create_arcane(Path(source_path).read_bytes(), draft)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(full)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Add review-pending Arcane to private V11")
    parser.add_argument("source", type=Path)
    parser.add_argument("--draft", type=Path, default=ROOT / "content" / "new_guides" / "arcane.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = create_private_preview(args.source, args.draft, args.output)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
