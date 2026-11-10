#!/usr/bin/env python3
"""One-time, lossless conversion of V11 HTML into declarative JSON chapter files."""
from pathlib import Path
import hashlib
import json
import re
import sys
from bs4 import BeautifulSoup
from .html_spans import SpanParser, find_class

ROOT = Path(__file__).resolve().parents[2]

def digest(data): return hashlib.sha256(data.encode('utf-8')).hexdigest()

def dump(path:Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def bootstrap(source_path:Path, source_md:Path|None=None, *, destination_root:Path|None=None):
    """Import trusted V11 content into a chosen workspace (default: legacy ROOT)."""
    workspace = Path(destination_root) if destination_root is not None else ROOT
    (workspace/'templates').mkdir(parents=True, exist_ok=True)
    (workspace/'reference').mkdir(parents=True, exist_ok=True)
    source = source_path.read_text(encoding='utf8')
    spans = SpanParser(source).spans
    guides = find_class(spans,'div','manual-view')
    assert len(guides) in (7, 8), f'Expected 7 original or 8 extended V11 guides, got {len(guides)}'
    soup = BeautifulSoup(source,'html.parser')
    nav_titles={}
    nav_map={}
    for tocn in soup.select('.reader-toc'):
        guide=tocn.get('data-nav-guide')
        nav_map[guide]=[(a.get('data-target'),a.get_text(' ',strip=True)) for a in tocn.select('a[data-target]')]
    class_map = {
        'fire': ('마법사','MAGE','화염','FIRE',[('sunfury','성난태양')]),
        'arcane': ('마법사','MAGE','비전','ARCANE',[('sunfury','성난태양'),('spellslinger','주문술사')]),
        'frost': ('마법사','MAGE','냉기','FROST',[('spellslinger','주문술사'),('frostfire','서리불꽃')]),
        'dk': ('죽음의 기사','DEATH KNIGHT','냉기','FROST',[('deathbringer','죽음의 인도자')]),
        'hunter': ('사냥꾼','HUNTER','사격','MARKSMANSHIP',[('sentinel','파수꾼')]),
        'bm': ('사냥꾼','HUNTER','야수','BEAST MASTERY',[('packleader','무리의 지도자')]),
        'rogue': ('도적','ROGUE','잠행','SUBTLETY',[('trickster','기만자')]),
        'assassination': ('도적','ROGUE','암살','ASSASSINATION',[('fatebound','운명결속자'),('deathstalker','죽음추적자')]),
    }
    out=[]
    all_skills={}
    for guide in guides:
        gid=guide.attrs['data-guide']
        _,_,_,_,heroes=class_map[gid]
        sections=[x for x in spans if x.tag=='section' and x.start>=guide.inner_start and x.end<=guide.inner_end]
        sections.sort(key=lambda x:x.start)
        assert sections, f'No sections for {gid}'
        soupguide=soup.select_one(f'#guide-{gid}')
        assert soupguide is not None
        nav_labels=dict(nav_map[gid])
        parts=[]
        for i,sec in enumerate(sections):
            sec_node=soupguide.select_one(f'section[id="{sec.attrs["id"]}"]')
            assert sec_node is not None
            header=sec_node.select_one('h2')
            label=header.get_text(' ',strip=True) if header else sec.attrs['id']
            # html is preserved verbatim, including icon tooltips, conditional
            # hero switches, note references and priority tables.
            after_html=source[sec.end:sections[i+1].start] if i+1<len(sections) else ''
            parts.append({
                'after_html':after_html,
                'id':sec.attrs['id'],
                'title_ko':label,
                'kind':'overview' if 'overview' in sec.attrs.get('class','').split() else 'chapter',
                'nav_label':nav_labels.get(sec.attrs['id'],label),
                'html':sec.full(source),
                'source_sha256':digest(sec.full(source)),
            })
        rows=[]
        for row in soupguide.select('.glossary-row'):
            spell=row.select_one('[data-spell]')
            en=row.select_one('.en')
            spellid=row.select_one('.spell-id')
            if not spell or not en or not spellid: continue
            namespell=spell.select_one('.spell-icon + span')
            if namespell: ko=namespell.get_text(' ',strip=True)
            else: ko=spell.get_text(' ',strip=True)
            en_name=en.get_text(' ',strip=True)
            en_name=en_name.replace(spellid.get_text(' ',strip=True),'').strip().strip('·').strip()
            m=re.search(r'\d+',spellid.get_text(' ',strip=True))
            if not m: continue
            rowobj={'spell_id':int(m.group()),'name_ko':ko,'name_en':en_name,
                    'glossary_source_guide':gid,'status':'inherited_v11_not_independently_verified'}
            rows.append(rowobj)
            all_skills.setdefault(str(rowobj['spell_id']),[]).append(rowobj)
        start=source[guide.inner_start:sections[0].start]
        end=source[sections[-1].end:guide.inner_end]
        datum={
            'schema_version':1,
            'id':gid,
            'class_ko':class_map[gid][0], 'class_en':class_map[gid][1],
            'spec_ko':class_map[gid][2], 'spec_en':class_map[gid][3],
            'hero_options':[{'id':id,'name_ko':n} for id,n in heroes],
            'initial_hero':guide.attrs.get('data-hero') or heroes[0][0],
            'wrapper_open':guide.opener(source),
            'intro_html':start,
            'sections':parts,
            'ending_html':end,
            'wrapper_close':guide.closer(source),
            'glossary_index':rows,
            'original_guide_sha256':digest(guide.full(source)),
        }
        dump(workspace/'content'/'guides'/f'{gid}.json',datum)
        out.append({'id':gid,'file':f'guides/{gid}.json','class_ko':class_map[gid][0],
                    'spec_ko':class_map[gid][2],'hero_options':datum['hero_options']})
    marker='<!-- ENGINE_GUIDES_INSERT -->'
    assert marker not in source
    template=source[:guides[0].start]+marker+source[guides[-1].end:]
    (workspace/'templates'/'shell.html').write_text(template,encoding='utf8')
    dump(workspace/'content'/'registry.json',{
        'schema_version':1,'engine_version':'1.0.0',
        'title':'WoW 딜사이클 데이터 엔진',
        'baseline':'V11',
        'scope':'Midnight Season 2 / user-provided guide interpretations',
        'import_source_sha256':digest(source),
        'guides':out,
    })
    conflicts={k: v for k,v in all_skills.items() if len({x['name_ko'] for x in v})>1}
    dump(workspace/'content'/'spell_index_from_v11.json',{
        'note':'Imported from V11 display text, NOT independently validated against official WoW Korean localization.',
        'spell_ids':all_skills,'name_conflicts':conflicts,
    })
    (workspace/'reference'/'v11.html').write_text(source,encoding='utf8')
    if source_md:
        (workspace/'reference'/'v11_source.md').write_bytes(source_md.read_bytes())
    print('Imported',len(guides),'guides',sum(len(json.loads((workspace/'content'/'guides'/f'{g["id"]}.json').read_text(encoding='utf8'))['sections']) for g in out),'sections')
    print('Content spell IDs',len(all_skills),'conflicting localized names',len(conflicts))

if __name__=='__main__':
    if len(sys.argv)<2: raise SystemExit('Usage: python -m engine.import_v11 SOURCE_V11_HTML [SOURCE_V11_MARKDOWN]')
    bootstrap(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv)>2 else None)
