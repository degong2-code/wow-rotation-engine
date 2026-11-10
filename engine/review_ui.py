"""Accessible dynamic UI for review-only public rotation metadata.

Not a gameplay guide. Never implies unverified conditions are executable.
Run: python -m engine.review_ui --output dist/review/index.html
"""
from __future__ import annotations

import argparse
from collections import Counter
from html import escape
from pathlib import Path
import re

from .public_data import BASE, load, validate

IDENT = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
HERO_NAMES = {
    "sunfury": "성난태양", "spellslinger": "주문술사", "frostfire": "서리불꽃",
    "deathbringer": "죽음의 인도자", "sentinel": "파수꾼",
    "packleader": "무리의 지도자", "trickster": "기만자",
    "fatebound": "운명결속자", "deathstalker": "죽음추적자",
}
PHASE_NAMES = {
    "unspecified": "구간 미지정", "combustion_active": "발화 중",
    "combustion_inactive": "발화 외",
    "shadow_dance_active": "어둠의 춤 중",
    "shadow_dance_inactive": "어둠의 춤 외",
}
MODE_NAMES = {"single_target": "단일", "aoe": "광역"}


def safe_id(value: str) -> str:
    if not isinstance(value, str) or not IDENT.fullmatch(value):
        raise ValueError("Unsafe guide/hero identifier")
    return value


def target_label(scenario: dict) -> str:
    low, high = scenario.get("target_min"), scenario.get("target_max")
    if low is None:
        return "대상 수 미지정"
    if high is None:
        return f"{low}명 이상"
    if low == high:
        return f"{low}명"
    return f"{low}~{high}명"


def render(base: Path = BASE) -> str:
    report = validate(base)
    if not report["ok"]:
        raise ValueError("Invalid public data: " + "; ".join(report["errors"]))
    manifest, _, guides = load(base)
    h = lambda s: escape(str(s), quote=True)
    parts = [
        '<!doctype html><html lang="ko"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        '<meta name="color-scheme" content="dark">',
        '<title>WoW Rotation Engine · 데이터 검토</title>',
        '<style>',
        ':root{color-scheme:dark;--bg:#1d1f24;--surface:#24262b;--ink:#f4f1eb;--muted:#b4b2b5;'
        '--gold:#e8b34b;--line:#49443d;--soft:#34363b}*{box-sizing:border-box}',
        'body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.72 system-ui,'
        '"Noto Sans KR","Malgun Gothic",sans-serif}a{color:var(--gold)}',
        'button{font:inherit;cursor:pointer;color:var(--ink)}',
        'button:focus-visible,a:focus-visible,summary:focus-visible{outline:2px solid var(--gold);outline-offset:3px}',
        'header{background:#0b0c0e;border-bottom:1px solid var(--line);padding:15px max(16px,calc((100vw - 1170px)/2))}',
        '.brand{font-weight:750;letter-spacing:-.02em}.brand small{color:var(--muted);font-size:12px;margin-left:12px}',
        '.frame{display:grid;grid-template-columns:205px minmax(0,1fr);gap:36px;max-width:1170px;margin:auto;padding:30px 18px 80px}',
        '.sidebar{position:sticky;top:12px;align-self:start;max-height:calc(100vh - 24px);overflow:auto}',
        '.sidebar h2{font-size:12px;color:var(--muted);font-weight:650;letter-spacing:.09em;margin:0 0 10px}',
        '.select-btn{display:block;width:100%;text-align:left;border:0;border-left:2px solid transparent;'
        'background:transparent;padding:9px 10px;margin:2px 0;border-radius:0 6px 6px 0}',
        '.select-btn[aria-selected=true]{background:#302b23;color:var(--gold);border-left-color:var(--gold);font-weight:700}',
        'main{min-width:0}h1{font-size:28px;margin:0 0 10px;line-height:1.3;letter-spacing:-.035em}',
        'h2{font-size:21px;line-height:1.35}h3{font-size:16px}p{margin:8px 0 14px}',
        '.subtitle,.muted,.metadata{color:var(--muted)}.metadata{font-size:12px}',
        '.notice{border:1px solid var(--gold);border-radius:8px;padding:14px 16px;margin:0 0 26px;background:#282720}',
        '.notice strong{color:var(--gold)}.guide-panel[hidden],.rotation-group[hidden]{display:none!important}',
        '.hero-controls{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0}',
        '.hero-btn{border:1px solid #625e55;border-radius:7px;padding:7px 13px;background:var(--surface)}',
        '.hero-btn[aria-pressed=true]{border-color:var(--gold);color:var(--gold);background:#302b23}',
        '.statbar{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0}',
        '.stat{border:1px solid var(--line);border-radius:7px;padding:8px 12px;font-size:12px}',
        '.stat b{font-size:16px;color:var(--gold);margin-right:5px}',
        '.card{border:1px solid var(--line);background:var(--surface);border-radius:10px;padding:18px;margin:16px 0}',
        '.card h3{margin-top:0}.over{overflow-x:auto;max-width:100%}',
        'table{width:100%;border-collapse:collapse;min-width:480px}',
        'th,td{text-align:left;padding:10px 8px;vertical-align:top;border-bottom:1px solid var(--soft)}',
        'th{font-size:12px;color:#dfc998}td:first-child{white-space:nowrap}',
        '.pending{font-size:12px;color:#e4bd7e}.pill{display:inline-block;border:1px solid #686052;'
        'border-radius:20px;padding:2px 8px;font-size:11px;margin-right:5px}',
        'details{margin:8px 0}summary{cursor:pointer;color:#d9c7a7;font-size:13px}',
        'details .metadata{padding:8px 0 0 14px;overflow-wrap:anywhere}',
        '.advanced-list{padding-left:22px}.advanced-list li{margin:12px 0}',
        '.footer{border-top:1px solid var(--line);margin-top:28px;padding:18px 0;font-size:12px;color:var(--muted)}',
        '[hidden]{display:none!important}',
        '@media(max-width:790px){.frame{display:block;padding:18px 14px 50px}',
        '.sidebar{position:static;max-height:none;border-bottom:1px solid var(--line);margin-bottom:22px}',
        '.navgroup{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:12px}',
        '.select-btn{width:auto;border:1px solid var(--line);border-radius:7px;padding:6px 10px;font-size:12px}',
        '.select-btn[aria-selected=true]{border-color:var(--gold)}',
        'h1{font-size:23px}.card{padding:13px}header{padding:12px 14px}}',
        '</style></head><body>',
        '<header><div class="brand">WOW ROTATION ENGINE <small>RULE REVIEW · V11 BASELINE</small></div></header>',
        '<div class="frame"><aside class="sidebar" aria-label="전문화 선택"><h2>전문화</h2><div class="navgroup" role="group" aria-label="전문화 목록">'
    ]
    for i, guide in enumerate(guides):
        gid = safe_id(guide["guide_id"])
        label = h(f'{guide["class_ko"]} · {guide["spec_ko"]}')
        parts.append(f'<button type="button" class="select-btn" data-select-guide="{gid}" '
                     f'aria-controls="guide-{gid}" aria-selected="{str(i == 0).lower()}">{label}</button>')
    parts.extend([
        '</div><p class="metadata">등록된 전문화는 JSON 목록을 기준으로 자동 구성됩니다.</p></aside><main>',
        '<h1>딜사이클 데이터 검토</h1>',
        '<p class="subtitle">규칙·기술명·원문 근거를 대조하기 위한 개발 화면</p>',
        '<div class="notice" role="status"><strong>실전용 공략이 아닙니다.</strong> '
        '현재 177개 우선순위의 조건은 미완성이고 한국어 기술명도 독립적으로 검증되지 않았습니다. '
        '표의 행 순서만 보고 게임에서 기술을 사용하지 마세요.</div>',
    ])
    for i, guide in enumerate(guides):
        gid = safe_id(guide["guide_id"])
        hero_options = [safe_id(x) for x in guide["hero_options"]]
        parts.append(f'<section class="guide-panel" id="guide-{gid}" data-guide="{gid}" '
                     + ('' if i == 0 else 'hidden ') + '>')
        parts.append(f'<h2>{h(guide["class_ko"])} · {h(guide["spec_ko"])}</h2>')
        parts.append(f'<p class="metadata"><a href="{h(guide["source_url"])}" rel="noopener noreferrer" '
                     f'target="_blank">원문 위치</a> · 외부 내용 대조 대기 · V11 기반 메타데이터</p>')
        groups = guide["rotation_groups"]
        tips = guide["advanced_guidance_index"]
        parts.append('<div class="statbar">'
                     f'<span class="stat"><b>{len(groups)}</b>우선순위 표</span>'
                     f'<span class="stat"><b>{sum(len(g["rules"]) for g in groups)}</b>행</span>'
                     f'<span class="stat"><b>{len(tips)}</b>심화 항목</span>'
                     '</div>')
        parts.append(f'<div class="hero-controls" role="group" aria-label="{h(guide["spec_ko"])} 영웅 특성">')
        for j, hero in enumerate(hero_options):
            parts.append(f'<button type="button" class="hero-btn" data-select-hero="{hero}" '
                         f'aria-pressed="{str(j == 0).lower()}">{h(HERO_NAMES.get(hero, hero))}</button>')
        parts.append('</div>')
        for group in groups:
            scenario = group["scenario"]
            hero = safe_id(scenario["hero"])
            mode = MODE_NAMES.get(scenario.get("mode"), scenario.get("mode", "미지정"))
            phase = PHASE_NAMES.get(scenario.get("phase"), scenario.get("phase", "미지정"))
            subject = f"{mode} · {target_label(scenario)} · {phase}"
            parts.append(f'<article class="card rotation-group" data-hero="{hero}" '
                         + ('' if hero == hero_options[0] else 'hidden ') + '>')
            parts.append(f'<h3>{h(subject)}</h3>')
            parts.append('<p class="pending">이 표는 행 제목과 순위만 복원된 검토 자료입니다. '
                         '전체 실행 조건이 누락되어 있습니다.</p>')
            parts.append('<div class="over"><table><thead><tr>'
                         '<th>순위</th><th>기술 · 주문 ID</th><th>해석 상태 / 근거</th>'
                         '</tr></thead><tbody>')
            for rule in group["rules"]:
                action, cond, provenance = rule["action"], rule["condition"], rule["provenance"]
                title = action.get("name_ko") or "복합 행동 · 미해결"
                spell = f'#{action["spell_id"]}' if action["spell_id"] is not None else 'ID 미해결'
                tags = ", ".join(cond.get("semantic_tags", [])) or "분류 없음"
                rank = rule["priority"] if rule["priority"] is not None else "선행"
                locator = provenance.get("locator", "")
                fingerprint = provenance.get("v11_fragment_sha256", "")
                parts.append('<tr>'
                             f'<td>{h(rank)}</td><td><b>{h(title)}</b><div class="metadata">{h(spell)}</div></td>'
                             '<td><span class="pending">조건 미해석 · 검토 대기</span>'
                             f'<div class="metadata">{h(tags)}</div>'
                             '<details><summary>원본 근거 식별자</summary>'
                             f'<div class="metadata">{h(locator)} · SHA-256 {h(fingerprint)}</div>'
                             '</details></td></tr>')
            parts.append('</tbody></table></div></article>')
        counts = Counter(tip["topic"] for tip in tips)
        parts.append('<article class="card"><h3>Advanced Tips · 주제 색인</h3>'
                     '<p class="pending">이름·분류만 보존했으며 구체적인 운용 설명은 포함하지 않습니다.</p>'
                     '<ol class="advanced-list">')
        for topic, count in counts.items():
            parts.append(f'<li>{h(topic)} <span class="pill">{count}개 항목 · 검토 대기</span></li>')
        parts.append('</ol></article></section>')
    parts.extend([
        '<footer class="footer">이 화면은 공개 가능한 데이터 검토 인터페이스입니다. '
        '미검증 규칙의 자동 게시를 지원하지 않습니다.</footer></main></div>',
        '<script>',
        '(function(){',
        'const buttons=[...document.querySelectorAll("[data-select-guide]")];',
        'const panels=[...document.querySelectorAll(".guide-panel")];',
        'function chooseGuide(id){',
        'buttons.forEach(b=>b.setAttribute("aria-selected",String(b.dataset.selectGuide===id)));',
        'panels.forEach(p=>p.hidden=p.dataset.guide!==id);',
        '}',
        'buttons.forEach(b=>b.addEventListener("click",()=>chooseGuide(b.dataset.selectGuide)));',
        'panels.forEach(panel=>{',
        'const heroes=[...panel.querySelectorAll("[data-select-hero]")];',
        'const groups=[...panel.querySelectorAll(".rotation-group[data-hero]")];',
        'function chooseHero(id){',
        'heroes.forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.selectHero===id)));',
        'groups.forEach(g=>g.hidden=g.dataset.hero!==id);',
        '}',
        'heroes.forEach(b=>b.addEventListener("click",()=>chooseHero(b.dataset.selectHero)));',
        '});',
        '})();',
        '</script></body></html>\n'
    ])
    return "".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Dynamic review-only guide browser")
    parser.add_argument("--output", default="dist/review/index.html")
    args = parser.parse_args()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(), encoding="utf-8")
    print(f"Built review viewer: {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
