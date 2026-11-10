"""Standalone, quick-reference HTML generated directly from existing V11 metadata.

This is intentionally a *reference index*, not an invented complete rotation.
It supports practical navigation while openly distinguishing missing conditions.
Run: python -m engine.manual_site --output dist/manual/index.html
"""
from __future__ import annotations

import argparse
from collections import Counter
from html import escape
from pathlib import Path

from .public_data import BASE, load, validate
from .review_ui import HERO_NAMES, MODE_NAMES, PHASE_NAMES, safe_id, target_label

TITLE = "WoW 딜사이클 빠른 참조"


def render(base: Path = BASE) -> str:
    checked = validate(base)
    if not checked["ok"]:
        raise ValueError("Invalid public guide data: " + "; ".join(checked["errors"]))
    manifest, _, guides = load(base)
    h = lambda value: escape(str(value), quote=True)
    parts = [
        '<!doctype html><html lang="ko"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        '<meta name="color-scheme" content="dark">',
        f'<title>{h(TITLE)}</title>',
        '<style>',
        ':root{color-scheme:dark;--bg:#181a1e;--panel:#25272b;--border:#48443c;'
        '--text:#f3efe6;--sub:#b5b1a9;--gold:#e4b75e;--accent:#323026}',
        '*{box-sizing:border-box}body{background:var(--bg);color:var(--text);margin:0;'
        'font:15px/1.65 system-ui,"Malgun Gothic",sans-serif}',
        'a{color:var(--gold);text-decoration:none}a:hover{text-decoration:underline}',
        'button,input,select{font:inherit}button{cursor:pointer}button:focus-visible,'
        'input:focus-visible,select:focus-visible,a:focus-visible,summary:focus-visible{'
        'outline:2px solid var(--gold);outline-offset:3px}',
        'header{background:#101114;border-bottom:1px solid var(--border);'
        'padding:18px max(18px,calc((100vw - 1150px)/2))}',
        '.brand{font-weight:800;font-size:16px;letter-spacing:.02em}',
        '.brand small{display:block;color:var(--sub);font-weight:400;font-size:12px}',
        '.layout{max-width:1150px;margin:auto;display:grid;grid-template-columns:200px minmax(0,1fr);'
        'gap:30px;padding:24px 18px 70px}',
        '.side{position:sticky;top:16px;align-self:start}.side h2{font-size:12px;'
        'color:var(--sub);text-transform:uppercase;margin:0 0 8px}',
        '.spec-buttons{display:grid;gap:4px}.spec-btn{text-align:left;padding:10px 12px;'
        'background:transparent;border:1px solid transparent;border-radius:7px;color:var(--text)}',
        '.spec-btn[aria-selected=true]{background:var(--accent);border-color:#706044;'
        'color:var(--gold);font-weight:700}',
        '.overline{font-size:12px;color:var(--gold);font-weight:700;letter-spacing:.08em}',
        'h1{font-size:28px;line-height:1.2;margin:5px 0 12px}h2{font-size:22px;margin:0 0 10px}',
        'h3{font-size:17px;margin:0 0 8px}p{margin:6px 0 12px}.muted{color:var(--sub)}',
        '.caveat{border-left:3px solid var(--gold);background:#2a2823;'
        'padding:12px 15px;border-radius:0 7px 7px 0;margin:16px 0 20px}',
        '.filters{display:flex;flex-wrap:wrap;gap:10px;align-items:end;padding:15px;'
        'border:1px solid var(--border);border-radius:10px;background:#202126;margin:17px 0 22px}',
        '.filter-label{display:grid;gap:5px;color:var(--sub);font-size:12px}',
        '.filter-label.search{flex:1;min-width:190px}input,select{background:#101114;'
        'color:var(--text);border:1px solid #5a5751;border-radius:6px;padding:9px 10px;'
        'min-height:40px;width:100%}',
        '.group-head{display:flex;gap:12px;justify-content:space-between;align-items:baseline;'
        'flex-wrap:wrap}.hero-buttons{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0 22px}',
        '.hero-btn{background:var(--panel);border:1px solid var(--border);border-radius:7px;'
        'padding:8px 14px;color:var(--text)}',
        '.hero-btn[aria-pressed=true]{color:var(--gold);border-color:var(--gold);'
        'background:var(--accent)}',
        '.stats{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0}',
        '.stat{border:1px solid var(--border);border-radius:6px;padding:6px 10px;'
        'color:var(--sub);font-size:12px}.stat b{color:var(--gold);margin-right:5px}',
        '.scenario{border:1px solid var(--border);border-radius:11px;background:var(--panel);'
        'padding:18px;margin:16px 0}.scenario h3{color:var(--text)}',
        '.scenario-meta{color:var(--sub);font-size:12px}',
        '.priority-list{padding-left:30px;margin:14px 0 0}.priority-row{'
        'padding:10px 6px 11px 6px;border-top:1px solid #393b3f}',
        '.priority-row::marker{color:var(--gold);font-weight:700}',
        '.spell-name{font-size:16px;font-weight:700}.spell-id{font-size:12px;'
        'color:var(--sub);margin-left:8px}.spell-id a{font-weight:500}',
        '.row-sub{font-size:12px;color:var(--sub)}details{margin:6px 0 0}',
        'summary{cursor:pointer;font-size:12px;color:#d5bd91}',
        '.source-detail{font-size:11px;overflow-wrap:anywhere;color:var(--sub);padding:5px 0 0}',
        '.tips{margin-top:25px;border-top:1px solid var(--border);padding-top:20px}',
        '.tips ul{padding-left:20px}.tips li{padding:6px 0}',
        '.empty{padding:16px;border:1px dashed #756953;border-radius:7px;color:var(--sub)}',
        '.guide-panel[hidden],.scenario[hidden],.priority-row[hidden]{display:none!important}',
        '.footer{margin-top:25px;padding-top:15px;border-top:1px solid var(--border);'
        'color:var(--sub);font-size:12px}',
        '@media(max-width:780px){.layout{display:block;padding:18px 13px 55px}',
        '.side{position:static}.spec-buttons{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 20px}',
        '.spec-btn{padding:7px 10px;border:1px solid var(--border);font-size:13px}',
        'h1{font-size:23px}.scenario{padding:12px}.filter-label.search{min-width:100%}',
        'header{padding:13px}.priority-list{padding-left:27px}}',
        '</style></head><body>',
        '<header><div class="brand">WoW ROTATION ENGINE'
        '<small>구조화된 기술 순서 · 전문화별 빠른 참조</small></div></header>',
        '<div class="layout"><aside class="side" aria-label="전문화 탐색"><h2>전문화 선택</h2>',
        '<div class="spec-buttons" role="group" aria-label="전문화">'
    ]
    for i, g in enumerate(guides):
        gid = safe_id(g["guide_id"])
        parts.append(
            f'<button type="button" class="spec-btn" data-select-guide="{gid}" '
            f'aria-controls="guide-{gid}" aria-selected="{str(i == 0).lower()}">'
            f'{h(g["class_ko"])} · {h(g["spec_ko"])}</button>'
        )
    parts.extend([
        '</div><p class="muted" style="font-size:12px">전문화 목록은 JSON에서 자동 생성됩니다.</p>'
        '</aside><main>',
        '<div class="overline">QUICK REFERENCE · V11 데이터</div>',
        f'<h1>{h(TITLE)}</h1>',
        '<div class="caveat"><b>간략 참조판</b> — 기술의 순서와 상황 분류를 빠르게'
        ' 확인할 수 있습니다. 세부 발동 조건·예외·Advanced Tips 본문은'
        ' 아직 이 데이터에 포함되지 않았습니다. 순서만으로 시전 여부를 결정하지 마세요.</div>',
        '<div class="filters" role="group" aria-label="기술·상황 필터">',
        '<label class="filter-label search" for="spell-search">기술명 또는 주문 ID 검색',
        '<input id="spell-search" type="search" placeholder="예: 얼음창, 30455" autocomplete="off"></label>',
        '<label class="filter-label" for="mode-filter">전투 상황',
        '<select id="mode-filter"><option value="all">전체</option>'
        '<option value="single_target">단일</option><option value="aoe">광역</option></select></label>',
        '<label class="filter-label" for="target-filter">대상 수',
        '<select id="target-filter"><option value="all">전체</option>'
        '<option value="1">1명</option><option value="2">2명</option>'
        '<option value="3">3명</option><option value="5">5명</option>'
        '<option value="8">8명</option></select></label>',
        '</div>',
        '<p id="filter-result" class="muted" role="status" aria-live="polite"></p>',
    ])
    for i, g in enumerate(guides):
        gid = safe_id(g["guide_id"])
        heroes = [safe_id(x) for x in g["hero_options"]]
        parts.append(f'<section class="guide-panel" id="guide-{gid}" data-guide="{gid}" '
                     + ('' if i == 0 else 'hidden ') + '>')
        parts.append(f'<div class="group-head"><h2>{h(g["class_ko"])} · {h(g["spec_ko"])}</h2>'
                     f'<a href="{h(g["source_url"])}" rel="noopener noreferrer" '
                     'target="_blank">원문 공략 보기</a></div>')
        groups = g["rotation_groups"]
        tips = g["advanced_guidance_index"]
        parts.append(f'<div class="stats"><span class="stat"><b>{len(groups)}</b>상황별 표</span>'
                     f'<span class="stat"><b>{sum(len(x["rules"]) for x in groups)}</b>기술 행</span>'
                     f'<span class="stat"><b>{len(tips)}</b>심화 주제</span></div>')
        parts.append('<div class="hero-buttons" role="group" aria-label="영웅 특성">')
        for j, hero in enumerate(heroes):
            parts.append(f'<button type="button" class="hero-btn" data-select-hero="{hero}" '
                         f'aria-pressed="{str(j == 0).lower()}">'
                         f'{h(HERO_NAMES.get(hero, hero))}</button>')
        parts.append('</div>')
        for group in groups:
            s = group["scenario"]
            hero = safe_id(s["hero"])
            mode = s.get("mode", "")
            if mode not in {"single_target", "aoe", "both"}:
                raise ValueError("Unsupported scenario mode: " + str(mode))
            low, high = s.get("target_min"), s.get("target_max")
            low_attr = "" if low is None else str(int(low))
            high_attr = "" if high is None else str(int(high))
            phase = PHASE_NAMES.get(s.get("phase"), s.get("phase", "구간 미지정"))
            label = f'{MODE_NAMES.get(mode, "단일·광역 공통" if mode == "both" else mode)} · {target_label(s)} · {phase}'
            parts.append(f'<article class="scenario" data-hero="{hero}" data-mode="{mode}" '
                         f'data-low="{low_attr}" data-high="{high_attr}" '
                         + ('' if hero == heroes[0] else 'hidden ') + '>')
            parts.append(f'<h3>{h(label)}</h3>'
                         '<p class="scenario-meta">표의 순번은 V11 원본 기준이며, 사용 조건은 별도 확인이 필요합니다.</p>')
            parts.append('<ol class="priority-list">')
            for rule in group["rules"]:
                action = rule["action"]
                name = action.get("name_ko") or "복합 행동 · 기술명 미확정"
                spell_id = action.get("spell_id")
                spell_markup = (f'<a href="https://www.wowhead.com/ko/spell={spell_id}" '
                                f'target="_blank" rel="noopener noreferrer">#{spell_id}</a>'
                                if type(spell_id) is int and spell_id > 0 else "ID 미해결")
                source = rule["provenance"]
                parts.append(f'<li class="priority-row" data-search="{h(name)} {spell_id or ""}">'
                             f'<span class="spell-name">{h(name)}</span> '
                             f'<span class="spell-id">{spell_markup}</span>'
                             '<div class="row-sub">세부 조건 미수록 · 원본 순서 참고</div>'
                             '<details><summary>분류·출처 정보</summary>'
                             f'<div class="source-detail">분류: {h(", ".join(rule["condition"].get("semantic_tags", [])) or "미분류")}'
                             f' · 위치: {h(source.get("locator", ""))}'
                             f' · SHA-256: {h(source.get("v11_fragment_sha256", ""))}</div>'
                             '</details></li>')
            parts.append('</ol></article>')
        parts.append('<div class="tips"><h3>Advanced Tips · 주제 목록</h3>'
                     '<p class="muted">현재 주제 이름만 보관하고 있습니다. 설명 본문은 후속 업데이트 대상입니다.</p><ul>')
        topic_counts = Counter(t["topic"] for t in tips)
        for topic, count in topic_counts.items():
            parts.append(f'<li>{h(topic)} <span class="muted">({count}건)</span></li>')
        parts.append('</ul></div></section>')
    parts.extend([
        '<p class="empty" id="empty-result" hidden>해당 조건에 맞는 기술 행이 없습니다. 검색어 또는 필터를 바꿔 보세요.</p>',
        '<footer class="footer">이 참조판은 사용자 편집 V11의 추출 데이터로 생성됩니다. '
        '실제 최적화 여부·완전한 시전 조건은 원문 공략에서 확인하세요.</footer>',
        '</main></div>',
        '<script>',
        '(function(){',
        'const specs=[...document.querySelectorAll("[data-select-guide]")];',
        'const panels=[...document.querySelectorAll(".guide-panel")];',
        'const search=document.getElementById("spell-search");',
        'const mode=document.getElementById("mode-filter");',
        'const target=document.getElementById("target-filter");',
        'const result=document.getElementById("filter-result");',
        'const empty=document.getElementById("empty-result");',
        'let guide=panels[0]?.dataset.guide;',
        'let hero=panels[0]?.querySelector("[data-select-hero]")?.dataset.selectHero;',
        'function panel(){return panels.find(p=>p.dataset.guide===guide);}',
        'function updateHash(){',
        'const hash="#"+encodeURIComponent(guide)+"/"+encodeURIComponent(hero);',
        'if(location.hash!==hash)history.replaceState(null,"",hash);',
        '}',
        'function filter(){',
        'const active=panel();if(!active)return;',
        'const text=search.value.trim().toLocaleLowerCase();',
        'const count=target.value==="all"?null:Number(target.value);',
        'let visibleRows=0;let visibleGroups=0;',
        'active.querySelectorAll(".scenario").forEach(card=>{',
        'const isHero=card.dataset.hero===hero;',
        'const isMode=mode.value==="all"||card.dataset.mode===mode.value||card.dataset.mode==="both";',
        'const min=card.dataset.low===""?null:Number(card.dataset.low);',
        'const max=card.dataset.high===""?null:Number(card.dataset.high);',
        'const targetsMatch=count===null||card.dataset.mode==="both"&&min===null||(min!==null&&count>=min&&(max===null||count<=max));',
        'let rows=0;',
        'card.querySelectorAll(".priority-row").forEach(row=>{',
        'const match=!text||row.dataset.search.toLocaleLowerCase().includes(text);',
        'row.hidden=!match; if(match)rows++;',
        '});',
        'card.hidden=!(isHero&&isMode&&targetsMatch&&rows>0);',
        'if(!card.hidden){visibleGroups++;visibleRows+=rows;}',
        '});',
        'result.textContent=visibleGroups+"개 상황 · "+visibleRows+"개 기술 행";',
        'empty.hidden=visibleRows!==0;',
        '}',
        'function selectGuide(id,hash=true){',
        'const active=panels.find(p=>p.dataset.guide===id);if(!active)return;',
        'guide=id;specs.forEach(b=>b.setAttribute("aria-selected",String(b.dataset.selectGuide===guide)));',
        'panels.forEach(p=>p.hidden=p!==active);',
        'hero=active.querySelector("[data-select-hero]")?.dataset.selectHero;',
        'active.querySelectorAll("[data-select-hero]").forEach(b=>',
        'b.setAttribute("aria-pressed",String(b.dataset.selectHero===hero)));',
        'if(hash)updateHash();filter();',
        '}',
        'function selectHero(id,hash=true){',
        'const active=panel();if(!active||!active.querySelector(\'[data-select-hero="\'+id+\'"]\'))return;',
        'hero=id;active.querySelectorAll("[data-select-hero]").forEach(b=>',
        'b.setAttribute("aria-pressed",String(b.dataset.selectHero===hero)));',
        'if(hash)updateHash();filter();',
        '}',
        'function restoreHash(){',
        'const parts=location.hash.slice(1).split("/").map(decodeURIComponent);',
        'if(parts[0]&&panels.some(p=>p.dataset.guide===parts[0])){',
        'selectGuide(parts[0],false);if(parts[1])selectHero(parts[1],false);',
        '}else{filter();}',
        '}',
        'specs.forEach(b=>b.addEventListener("click",()=>selectGuide(b.dataset.selectGuide)));',
        'panels.forEach(p=>p.querySelectorAll("[data-select-hero]").forEach(b=>',
        'b.addEventListener("click",()=>selectHero(b.dataset.selectHero))));',
        '[search,mode,target].forEach(el=>el.addEventListener("input",filter));',
        'window.addEventListener("hashchange",restoreHash);restoreHash();',
        '})();',
        '</script></body></html>\n'
    ])
    return "".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a standalone reference HTML from guide JSON")
    parser.add_argument("--output", default="dist/manual/index.html")
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(), encoding="utf-8")
    print(f"Manual reference generated: {output} ({output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
