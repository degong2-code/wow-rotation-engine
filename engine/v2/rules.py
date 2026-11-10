"""Phase 2: provenance-first, conservative structured extraction from *trusted* V11 chapters.

Not an AI and not a gameplay optimizer. Every extracted rule remains UNREVIEWED.
The original chapter HTML is still the rendering source of truth in Phase 2.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from bs4 import BeautifulSoup, Tag
from .build import ROOT, read_json, sha

RULES = ROOT / 'content' / 'rules'
SCHEMA = ROOT / 'schemas' / 'rotation-rules.schema.json'


def digest(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def text(tag: Tag) -> str:
    return tag.get_text(' ', strip=True)


def source_ref(guide: dict, section: dict, selector: str, evidence: str) -> dict:
    return {
        'kind': 'trusted_v11_html',
        'guide_id': guide['id'],
        'chapter_id': section['id'],
        'chapter_sha256': section['source_sha256'],
        'locator': selector,
        'evidence_sha256': digest(evidence),
        'evidence_ko': evidence,
        'original_wowhead_passage_verified': False,
    }


def scenario_from_heading(heading: str, hero: str) -> dict:
    single = ('단일' in heading)
    aoe = ('광역' in heading)
    min_targets: int | None = None
    max_targets: int | None = None
    if '단일/광역' in heading or '단일·광역' in heading:
        single = False
        aoe = False
    if single:
        min_targets = 1
        max_targets = 2 if any(p in heading for p in ('1~2', '1～2', '1-2')) else 1
    elif aoe:
        if re.search(r'(?:3\s*명\s*이상|3\s*명\s*\+|3\+)', heading):
            min_targets = 3
        elif re.search(r'(?:2\s*명\s*이상|2\s*명\s*\+|2\+)', heading):
            min_targets = 2
    phase = 'unspecified'
    if '발화 중' in heading: phase = 'combustion_active'
    elif '발화 외' in heading: phase = 'combustion_inactive'
    elif '춤 중' in heading: phase = 'shadow_dance_active'
    elif '춤 외' in heading: phase = 'shadow_dance_inactive'
    elif '쿨기 조건' in heading: phase = 'cooldown_condition'
    return {
        'hero': hero,
        'target_min': min_targets,
        'target_max': max_targets,
        'mode': 'both' if '단일/광역' in heading or '단일·광역' in heading else 'single_target' if single else 'aoe' if aoe else 'unspecified',
        'phase': phase,
        'heading_ko': heading,
        'interpretation': 'inferred_from_heading_not_game_verified',
    }


def find_hero(node: Tag, initial_hero: str) -> str:
    for par in node.parents:
        if isinstance(par, Tag) and par.get('data-hero'):
            return par['data-hero']
    return initial_hero


def spell_candidates(guide: dict, action_cell: Tag) -> dict:
    raw = text(action_cell)
    glossary = guide['glossary_index']
    # Action-only resolution. Never read condition tooltips as the action spell.
    matches = []
    for e in glossary:
        name = e['name_ko']
        if not name or not isinstance(e['spell_id'], int):
            continue
        if raw == name or raw.startswith(name + ' ') or raw.startswith(name + '·') or raw.startswith(name + '('):
            matches.append(e)
    # Choose the longest valid prefix; the action may also contain a role/qualifier.
    if matches:
        longest = max(len(e['name_ko']) for e in matches)
        match = [e for e in matches if len(e['name_ko']) == longest]
        ids = sorted(set(e['spell_id'] for e in match))
        if len(ids) == 1:
            return {'raw_ko':raw,'spell_id':ids[0],'spell_name_ko':match[0]['name_ko'],
                    'match_state':'v11_glossary_prefix_unverified'}
        return {'raw_ko':raw,'spell_id':None,'spell_name_ko':None,
                'match_state':'ambiguous_same_name_multiple_ids'}
    # Compound rows contain multiple abilities or a descriptive role label. Do not guess.
    return {'raw_ko':raw,'spell_id':None,'spell_name_ko':None,'match_state':'unresolved_or_composite'}


def predicates_from_condition(raw: str) -> list[dict]:
    """Extract ONLY syntactically explicit numerical predicates; never claim completeness."""
    out=[]
    # Arbitrary Korean prose can reverse polarity. Do not infer buffs or broader logic.
    for match in re.finditer(r'연계\s*점수\s*(?:≥|>=|이?\s*)\s*(\d+)\s*(?:점\s*이상|점\s*|이상)', raw):
        out.append({'field':'combo_points','operator':'gte','value':int(match.group(1)),
                    'matched_text':match.group(0), 'verification':'syntax_only'})
    return out


def extract_guide(guide: dict, baseline: str) -> dict:
    groups=[]
    advanced=[]
    for section in guide['sections']:
        dom=BeautifulSoup(section['html'],'html.parser')
        root=dom.find('section')
        if not root:
            continue
        tables=[t for t in root.find_all('table') if (t.select_one('thead th') and text(t.select_one('thead th'))=='순위')]
        for table_idx,table in enumerate(tables, start=1):
            heading = table.find_previous(['h3','h4'])
            if heading is None or root not in list(heading.parents):
                heading = root.select_one('h2')
            heading_txt=text(heading) if heading else section['title_ko']
            hero=find_hero(table,guide['initial_hero'])
            group_id=f'{guide["id"]}:{section["id"]}:table-{table_idx}'
            header=[text(th) for th in table.select('thead th')]
            records=[]
            for row_idx,row in enumerate(table.select('tbody tr'),start=1):
                cells=row.find_all(['td','th'],recursive=False)
                if len(cells)<3:
                    raise ValueError(f'{group_id} row {row_idx}: expected 3 columns, saw {len(cells)}')
                columns=[text(cell) for cell in cells]
                label,action_raw,condition_raw=columns[0],columns[1],columns[2]
                # No destructive normalization of original priority label.
                rank=int(label) if label.isdigit() else None
                evidence=' | '.join(columns)
                rules={
                    'id':f'{group_id}:row-{row_idx}',
                    'order':row_idx,
                    'priority_label':label,
                    'priority_number':rank,
                    'kind':'ability' if rank is not None else 'preparation_or_other',
                    'action':spell_candidates(guide,cells[1]),
                    'condition':{
                        'raw_ko':condition_raw,
                        'predicates':predicates_from_condition(condition_raw),
                        'formalization':'partial_syntax_only_not_executable',
                    },
                    'evidence':source_ref(guide,section, f'section#{section["id"]} table.priority[{table_idx}] tbody tr:nth-child({row_idx})', evidence),
                    'review':{'state':'pending','reason':'V11 text imported; source-meaning and spell IDs not independently verified'},
                }
                records.append(rules)
            groups.append({
                'id':group_id,
                'source_chapter':section['id'],
                'column_headers':header,
                'scenario':scenario_from_heading(heading_txt,hero),
                'source_heading':heading_txt,
                'evidence':source_ref(guide,section,f'section#{section["id"]} table.priority[{table_idx}]',heading_txt),
                'rules':records,
            })
        if 'advanced' not in section['id']:
            continue
        current_heading=section['title_ko']
        block_idx=0
        for child in root.find_all(recursive=False):
            if child.name in ('h3','h4'):
                current_heading=text(child)
                continue
            if child.name in ('header','div') and ('chapter-heading' in (child.get('class') or [])):
                continue
            # Use meaningful direct paragraphs, each li, and warning boxes. Skip the same
            # li content when a container is summarized; no nested double count.
            chunks=[]
            if child.name in ('p','aside'):
                chunks=[child]
            elif child.name in ('ul','ol'):
                chunks=child.find_all('li',recursive=False)
            elif child.name=='div' and child.find('table'):
                # structured table: each data row becomes a separate advanced item
                chunks=child.select('tbody tr')
            else:
                continue
            for item in chunks:
                body=text(item)
                if not body:
                    continue
                block_idx+=1
                kind='warning' if child.name=='aside' and 'warn' in child.get('class',[]) else 'tip'
                if child.name=='div':kind='comparison_row'
                advanced.append({
                    'id':f'{guide["id"]}:{section["id"]}:tip-{block_idx}',
                    'title_ko':current_heading,
                    'kind':kind,
                    'text_ko':body,
                    'semantic_status':'unstructured_tip_requires_review',
                    'evidence':source_ref(guide,section,f'section#{section["id"]} advanced-item[{block_idx}]',body),
                    'review':{'state':'pending','reason':'Guidance extracted from V11; no automated semantic validation'},
                })
    return {
        'schema_version':'2.0',
        'guide_id':guide['id'],
        'class_ko':guide['class_ko'],
        'spec_ko':guide['spec_ko'],
        'baseline_document':'V11',
        'baseline_html_sha256':baseline,
        'hero_options':[h['id'] for h in guide['hero_options']],
        'rotation_groups':groups,
        'advanced_guidance':advanced,
        'publication':{'status':'blocked_pending_review',
            'reason':'Structured import is a review candidate, not a validated replacement for human-reviewed V11 HTML.'},
    }


def extract_all(root:Path=ROOT) -> list[dict]:
    registry=read_json(root/'content'/'registry.json')
    return [extract_guide(read_json(root/'content'/r['file']),registry['import_source_sha256']) for r in registry['guides']]


def write_all(root:Path=ROOT, overwrite:bool=False) -> dict:
    dst=root/'content'/'rules'
    dst.mkdir(parents=True,exist_ok=True)
    docs=extract_all(root)
    for doc in docs:
        path=dst/f'{doc["guide_id"]}.json'
        if path.exists() and json.loads(path.read_text(encoding='utf8')) != doc and not overwrite:
            raise ValueError(f'Refusing to overwrite modified rule candidate: {path.name}. Review/diff first, or explicitly use --force.')
    for doc in docs:
        (dst/f'{doc["guide_id"]}.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    stats={
        'guide_count':len(docs),
        'priority_table_count':sum(len(d['rotation_groups']) for d in docs),
        'priority_row_count':sum(len(g['rules']) for d in docs for g in d['rotation_groups']),
        'advanced_item_count':sum(len(d['advanced_guidance']) for d in docs),
        'spell_id_matched_count':sum(r['action']['spell_id'] is not None for d in docs for g in d['rotation_groups'] for r in g['rules']),
        'spell_id_unresolved_count':sum(r['action']['spell_id'] is None for d in docs for g in d['rotation_groups'] for r in g['rules']),
        'publication_status':'blocked_pending_review',
    }
    dest=root/'dist'/'rule_import_stats.json'
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return stats

if __name__=='__main__':
    print(json.dumps(write_all(),ensure_ascii=False,indent=2))
