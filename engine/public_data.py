"""Public compact-rule data validator and HTML index generator.

It intentionally does not claim to interpret all rotation predicates or to ship
full translated guides. Run: python -m engine.public_data validate|build
"""
from __future__ import annotations

import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path
import re

BASE = Path(__file__).resolve().parents[1] / 'content' / 'public'
HEX = re.compile(r'^[0-9a-f]{64}$')


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def load(base: Path = BASE):
    manifest = read(base / 'manifest.json')
    spell_doc = read(base / 'spells.json')
    guides = [read(base / spec['file']) for spec in manifest['guides']]
    return manifest, spell_doc, guides


def validate(base: Path = BASE):
    problems = []
    try:
        manifest, spell_doc, guides = load(base)
    except (OSError, ValueError) as exc:
        return {'ok': False, 'errors': [str(exc)]}

    def require(ok, msg):
        if not ok:
            problems.append(msg)

    require(manifest.get('schema_version') == 'public-v1', 'wrong manifest version')
    require(spell_doc.get('schema_version') == 'public-v1', 'wrong spell map version')
    spellnames = {}
    spell_ids = set()
    records = 0
    for item in spell_doc.get('spells', []):
        sid = item.get('spell_id')
        name = item.get('name_ko')
        if type(sid) is not int or sid <= 0 or not isinstance(name, str) or not name:
            problems.append('invalid spell entry')
            continue
        spell_ids.add(sid)
        spellnames.setdefault(sid, set()).add(name)
        require(item.get('review') == 'unverified_inherited_from_v11', f'spell {sid} review state')
        records += 1
    observed = Counter(specs=len(guides), spell_records=records, spell_ids=len(spell_ids))
    seen_guides = set()
    for summary, guide in zip(manifest.get('guides', []), guides):
        sid = guide.get('guide_id')
        require(sid == summary.get('id') and sid not in seen_guides, f'invalid guide key: {sid}')
        seen_guides.add(sid)
        require(guide.get('schema_version') == 'public-v1', f'{sid}: schema')
        require(guide.get('publication') == {'status': 'review_required', 'automatic_publish_allowed': False}, f'{sid}: publication state')
        require(guide.get('source_url', '').startswith('https://www.wowhead.com/'), f'{sid}: source URL')
        require(HEX.fullmatch(guide.get('baseline_v11_sha256', '')) is not None, f'{sid}: baseline hash')
        known_heroes = set(guide.get('hero_options', []))
        observed['tables'] += len(guide.get('rotation_groups', []))
        observed['advanced_tips'] += len(guide.get('advanced_guidance_index', []))
        require(len(guide['rotation_groups']) == summary.get('rotation_group_count'), f'{sid}: group count')
        require(sum(len(g['rules']) for g in guide['rotation_groups']) == summary.get('priority_row_count'), f'{sid}: row count')
        require(len(guide['advanced_guidance_index']) == summary.get('advanced_item_count'), f'{sid}: advanced count')
        seen_rules = set()
        for group in guide['rotation_groups']:
            require(group['scenario'].get('hero') in known_heroes, f'{sid}: unknown hero')
            for ordinal, rule in enumerate(group['rules'], 1):
                rid = rule['id']
                require(rid not in seen_rules, f'{sid}: duplicate rule: {rid}')
                seen_rules.add(rid)
                require(rule['order'] == ordinal, f'{rid}: row order')
                action = rule.get('action', {})
                spell_id = action.get('spell_id')
                if spell_id is None:
                    observed['unresolved_spell_ids'] += 1
                else:
                    require(spell_id in spellnames and action.get('name_ko') in spellnames.get(spell_id, set()), f'{rid}: spell lookup mismatch')
                cond = rule.get('condition', {})
                require(cond.get('state') == 'needs_manual_interpretation', f'{rid}: unexpected condition approval')
                require(rule.get('review') == 'pending', f'{rid}: unexpected review approval')
                for p in cond.get('machine_predicates', []):
                    require(p.get('op') in {'eq', 'ne', 'gte', 'lte'} and isinstance(p.get('field'), str), f'{rid}: invalid predicate')
                evidence = rule.get('provenance', {})
                require(HEX.fullmatch(evidence.get('v11_fragment_sha256','')) is not None and evidence.get('external_source_verified') is False, f'{rid}: invalid evidence')
                observed['rows'] += 1
        seen_tips = set()
        for tip in guide['advanced_guidance_index']:
            require(tip['id'] not in seen_tips, f'{sid}: duplicate advanced id')
            seen_tips.add(tip['id'])
            require(tip.get('full_text_in_public_dataset') is False and tip.get('review') == 'pending', f'{sid}: tip review')
            evidence=tip.get('provenance',{})
            require(HEX.fullmatch(evidence.get('v11_fragment_sha256','')) is not None and evidence.get('external_source_verified') is False, f'{sid}: tip evidence')
    require(dict(observed) == manifest.get('counts'), f'count drift: {dict(observed)} != {manifest.get("counts")}')
    return {'ok': not problems, 'counts': dict(observed), 'errors': problems}


def render(base: Path = BASE):
    report = validate(base)
    if not report['ok']:
        raise ValueError('; '.join(report['errors']))
    manifest, _, guides = load(base)
    h = escape
    parts = [
        '<!doctype html><html lang="ko"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<title>WoW Rotation Engine — 공개 규칙 데이터 색인</title>',
        '<style>:root{color-scheme:dark;--gold:#e8b34b;--bg:#1d1f24;--fg:#f4f1eb;--line:#47443e}',
        '*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.7 system-ui,\'Malgun Gothic\',sans-serif}',
        'header{background:#0c0d0f;padding:1.5rem 1rem}main{max-width:980px;margin:auto;padding:1rem}',
        'h1,h2,h3{color:var(--gold)}.note{border:1px solid var(--gold);padding:12px;border-radius:8px}',
        'nav{display:flex;flex-wrap:wrap;gap:6px;margin:18px 0}button{background:#292b30;color:#faf5e9;border:1px solid #62605a;padding:8px 11px;border-radius:7px;cursor:pointer}',
        'button[aria-selected="true"]{border-color:var(--gold);color:var(--gold)}section[data-guide]{display:none}section[data-guide].active{display:block}',
        '.sheet{background:#24262b;border:1px solid var(--line);border-radius:8px;padding:14px;margin:14px 0}',
        'table{width:100%;border-collapse:collapse}td,th{padding:9px 7px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}',
        'th{color:#d4c2a1}small,.muted{color:#b4b2b5}a{color:#e8b34b}code{overflow-wrap:anywhere}',
        '@media(max-width:600px){body{font-size:14px}td,th{padding:7px 4px}main{padding:12px}}',
        '</style></head><body>',
        '<header><main><h1>WoW 딜사이클 규칙 데이터 색인</h1>',
        '<p>V11에서 이관한 구조화 규칙을 탐색하는 데이터 품질 점검용 뷰어</p></main></header>',
        '<main><p class="note"><strong>주의:</strong> 이 페이지는 실전 딜사이클 공략이 아닙니다. '
        '우선순위의 조건은 불완전하고, 한국어 스킬명과 원문 의미도 외부 대조 전입니다. '
        '실제 전투에서는 검증된 원문 공략을 확인하세요.</p>',
        '<nav aria-label="전문화 선택">'
    ]
    for i,guide in enumerate(guides):
        label=h(guide['class_ko']+' · '+guide['spec_ko'])
        parts.append(f'<button type="button" data-target="spec-{h(guide["guide_id"])}" '
                     f'aria-selected="{"true" if i==0 else "false"}">{label}</button>')
    parts.append('</nav>')
    for i,guide in enumerate(guides):
        parts.append(f'<section data-guide id="spec-{h(guide["guide_id"])}" class="{"active" if i==0 else ""}">')
        parts.append(f'<h2>{h(guide["class_ko"])} · {h(guide["spec_ko"])}'
                     f' <small>({h(" / ".join(guide["hero_options"]))})</small></h2>')
        parts.append(f'<p><a href="{h(guide["source_url"])}" target="_blank" rel="noopener noreferrer">출처 페이지</a>'
                     ' · 모든 규칙 검토 대기</p>')
        for g in guide['rotation_groups']:
            s=g['scenario']; desc=f"{s.get('hero')} · {s.get('mode')} · 대상 {s.get('target_min')}~{s.get('target_max') or '∞'}"
            if s.get('phase'): desc+=f" · {s['phase']}"
            parts.append(f'<article class="sheet"><h3>{h(desc)}</h3><table><thead><tr><th>순위</th><th>기술(미검증)</th><th>조건 상태</th></tr></thead><tbody>')
            for r in g['rules']:
                a=r['action']; name=a['name_ko'] or '(복합 행동: 기술 미확정)'; spell=a['spell_id']
                tags=', '.join(r['condition']['semantic_tags']) or '미분류'
                parts.append(f'<tr><td>{r["order"]}</td><td>{h(name)} <small>#{spell if spell is not None else "?"}</small></td>'
                             f'<td><small>해석 대기 · {h(tags)}</small></td></tr>')
            parts.append('</tbody></table></article>')
        parts.append('<article class="sheet"><h3>Advanced Tips — 주제 색인</h3><p class="muted">원문 설명은 포함하지 않았습니다. 제목·분류만 표시합니다.</p><ul>')
        for a in guide['advanced_guidance_index']:
            parts.append(f'<li>{h(a["topic"])} <small>({h(", ".join(a["semantic_tags"]) or "미분류")})</small></li>')
        parts.append('</ul></article></section>')
    parts.append('</main><script>document.querySelectorAll("nav [data-target]").forEach(b=>b.addEventListener("click",()=>{'
                 'document.querySelectorAll("nav [data-target]").forEach(x=>x.setAttribute("aria-selected",x===b?"true":"false"));'
                 'document.querySelectorAll("section[data-guide]").forEach(s=>s.classList.toggle("active",s.id===b.dataset.target));'
                 '}));</script></body></html>\n')
    return ''.join(parts)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('command', choices=['validate','build'])
    p.add_argument('--output', default='dist/public-index.html')
    args=p.parse_args()
    if args.command=='validate':
        result=validate()
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0 if result['ok'] else 1
    page=render()
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(page,encoding='utf8')
    print('Built',out,'bytes',out.stat().st_size)
    return 0

if __name__=='__main__':
    raise SystemExit(main())