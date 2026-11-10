#!/usr/bin/env python3
"""Deterministic, offline V11-guide JSON -> standalone HTML builder.

This stage deliberately DOES NOT scrape, translate, reason about rotations,
call AI, or publish. It requires trusted, already-reviewed chapter HTML.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[2]
MARKER='<!-- ENGINE_GUIDES_INSERT -->'

def sha(data:str)->str:
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def read_json(path:Path):
    return json.loads(path.read_text(encoding='utf8'))

def validate(registry:dict, guides:list[dict], page:str):
    errors=[]
    guide_ids=[g['id'] for g in guides]
    if len(set(guide_ids))!=len(guide_ids): errors.append('Duplicate guide IDs')
    if len(guides)!=len(registry['guides']): errors.append('Missing guide documents')
    for g in guides:
        if g['schema_version']!=1: errors.append(f'Unsupported schema version: {g["id"]}')
        if g['wrapper_open'].count('data-guide="'+g['id']+'"')!=1:
            errors.append(f'Guide wrapper mismatch: {g["id"]}')
        if len(g['sections'])<1: errors.append(f'No chapters: {g["id"]}')
        sid=[s['id'] for s in g['sections']]
        if len(set(sid))!=len(sid): errors.append(f'Duplicate section IDs in {g["id"]}')
        if not any(s['kind']=='overview' for s in g['sections']):
            errors.append(f'No overview: {g["id"]}')
        for s in g['sections']:
            node=BeautifulSoup(s['html'],'html.parser').find('section')
            if node is None or node.get('id')!=s['id']:
                errors.append(f'Section HTML or ID mismatch: {g["id"]}/{s["id"]}')
                continue
            h=node.select_one('h2')
            if h and h.get_text(' ',strip=True)!=s['title_ko']:
                errors.append(f'Section heading mismatch: {g["id"]}/{s["id"]}')
            if node.find('script'):
                errors.append(f'Inline scripts forbidden in guide section: {g["id"]}/{s["id"]}')
        if not any(h['id']==g['initial_hero'] for h in g['hero_options']):
            errors.append(f'Initial hero not declared: {g["id"]}')
    page_doc=BeautifulSoup(page,'html.parser')
    ids=[e.get('id') for e in page_doc.select('[id]')]
    repeats={k:v for k,v in Counter(ids).items() if v>1}
    if repeats: errors.append(f'Duplicate HTML IDs: {repeats}')
    actual_guide_ids=[e.get('data-guide') for e in page_doc.select('.manual-view')]
    if actual_guide_ids!=guide_ids:
        errors.append(f'Wrong guide order: {actual_guide_ids} != {guide_ids}')
    controls=page_doc.select('[data-guide-button]')
    for b in controls:
        gid=b.get('data-guide-button')
        hero=b.get('data-hero-button')
        if gid not in guide_ids:
            errors.append(f'Navigation targets unknown guide: {gid}')
        else:
            guide=guides[guide_ids.index(gid)]
            if hero not in {h['id'] for h in guide['hero_options']}:
                errors.append(f'Navigation targets undeclared hero: {gid}/{hero}')
    if not controls: errors.append('Navigation missing')
    all_ids=set(ids)
    for a in page_doc.select('a[href^="#"]'):
        dest=a.get('href','')[1:]
        if dest and dest not in all_ids:
            errors.append(f'Broken section href: #{dest}')
    for a in page_doc.select('.reader-toc a[data-target]'):
        dest=a['data-target']
        if dest not in all_ids:
            errors.append(f'Invalid TOC data-target: {dest}')
    for ng in page_doc.select('.reader-toc'):
        if ng.get('data-nav-guide') not in guide_ids:
            errors.append(f'Invalid nav guide: {ng.get("data-nav-guide")}')
    if len(page_doc.select('.manual-view'))!=len(guides):
        errors.append('Unexpected number of guides')
    return errors

def render(registry, root=ROOT):
    guides=[read_json(root/'content'/e['file']) for e in registry['guides']]
    template=(root/'templates'/'shell.html').read_text(encoding='utf8')
    if template.count(MARKER)!=1: raise ValueError('Template must contain exactly one insertion marker')
    def html(g):
        return g['wrapper_open']+g['intro_html']+''.join(s['html']+s.get('after_html','') for s in g['sections'])+g['ending_html']+g['wrapper_close']
    full=template.replace(MARKER,''.join(html(g) for g in guides))
    return full,guides

def main():
    p=argparse.ArgumentParser(description='Build standalone offline HTML from content/guides/*.json')
    p.add_argument('--output',type=Path,default=ROOT/'dist'/'wow_rotation_manual_engine_v2.html')
    p.add_argument('--manifest',type=Path,default=ROOT/'dist'/'build_manifest.json')
    p.add_argument('--require-identical-v11',action='store_true')
    args=p.parse_args()
    registry=read_json(ROOT/'content'/'registry.json')
    page,guides=render(registry)
    errors=validate(registry,guides,page)
    if errors: raise SystemExit('Build validation FAIL:\n- '+'\n- '.join(errors))
    output_sha=sha(page)
    baseline_sha=registry['import_source_sha256']
    identical=output_sha==baseline_sha
    if args.require_identical_v11 and not identical:
        raise SystemExit(f'Baseline mismatch: generated={output_sha} expected={baseline_sha}')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(page,encoding='utf8')
    status={
        'engine_version':registry['engine_version'],
        'guide_count':len(guides),
        'chapter_count':sum(len(g['sections']) for g in guides),
        'glossary_entries':sum(len(g['glossary_index']) for g in guides),
        'baseline_v11_sha256':baseline_sha,
        'output_sha256':output_sha,
        'byte_identical_to_v11':identical,
        'status':'PASS',
        'known_limits':[
            'V11 candidate extraction is implemented; external source collection, AI translation and semantic verification are not.',
            'Structured rule candidates are not yet used for HTML rendering; the original V11 chapter HTML remains canonical.',
            'Ability names were imported from V11 and not reverified by this build.'
        ]
    }
    args.manifest.parent.mkdir(parents=True,exist_ok=True)
    args.manifest.write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(f'PASS {status["guide_count"]} guides, {status["chapter_count"]} chapters, {status["glossary_entries"]} spell glossary entries')
    print(f'Generated HTML size {len(page.encode("utf8")):,} bytes')
    print(f'Byte-identical to V11: {identical}')
    print(f'Output: {args.output}')

if __name__=='__main__':main()
