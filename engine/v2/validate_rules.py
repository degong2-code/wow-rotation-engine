"""Offline rule-store gate: schema + structural source evidence, *not* gameplay correctness.

python -m engine.validate_rules
"""
from __future__ import annotations
import json
from pathlib import Path
from collections import Counter
import jsonschema
from .build import ROOT, read_json, sha
from .rules import extract_guide, digest


def validate_directory(root: Path = ROOT) -> dict:
    registry=read_json(root/'content'/'registry.json')
    schema=read_json(root/'schemas'/'rotation-rules.schema.json')
    errors=[];warnings=[]
    stats={'guide_count':0,'priority_table_count':0,'priority_row_count':0,
           'advanced_item_count':0,'unresolved_spell_id_count':0,
           'no_explicit_target_threshold_count':0}
    for record in registry['guides']:
        guide=read_json(root/'content'/record['file'])
        path=root/'content'/'rules'/f'{guide["id"]}.json'
        if not path.is_file():
            errors.append(f'Missing candidate rule file {path.name}')
            continue
        doc=read_json(path)
        stats['guide_count']+=1
        validator=jsonschema.Draft202012Validator(schema)
        for e in validator.iter_errors(doc):
            errors.append(f'{guide["id"]} schema {"/".join(map(str,e.absolute_path))}: {e.message}')
        if doc.get('guide_id')!=guide['id']: errors.append(f'{guide["id"]}: mismatched guide ID')
        if doc.get('baseline_html_sha256')!=registry['import_source_sha256']:
            errors.append(f'{guide["id"]}: baseline V11 hash changed')
        if set(doc.get('hero_options',[]))!={h['id'] for h in guide['hero_options']}:
            errors.append(f'{guide["id"]}: mismatched hero options')
        expected=extract_guide(guide,registry['import_source_sha256'])
        # The V11 migration is read-only; stage future AI proposals separately.
        if doc.get('rotation_groups')!=expected['rotation_groups']:
            errors.append(f'{guide["id"]}: rotation candidate differs from source HTML. Do not edit imported rules directly.')
        if doc.get('advanced_guidance')!=expected['advanced_guidance']:
            errors.append(f'{guide["id"]}: Advanced Tips candidate differs from source HTML. Do not edit imported tips directly.')
        if doc.get('publication',{}).get('status')!='blocked_pending_review':
            errors.append(f'{guide["id"]}: cannot publish source-unverified imported candidates')
        groups=doc.get('rotation_groups',[])
        advice=doc.get('advanced_guidance',[])
        stats['priority_table_count']+=len(groups)
        stats['advanced_item_count']+=len(advice)
        all_ids=[]
        glossary={(e['spell_id'],e['name_ko']) for e in guide['glossary_index']}
        section_map={s['id']:s for s in guide['sections']}
        for group in groups:
            all_ids.append(group['id'])
            sc=group['scenario'];hero=sc['hero']
            if hero not in doc['hero_options']:
                errors.append(f'{guide["id"]} unknown hero: {hero}')
            lo,hi=sc['target_min'],sc['target_max']
            if lo is not None and hi is not None and lo>hi:
                errors.append(f'{group["id"]}: invalid target range')
            if sc['mode']=='aoe' and lo is None:
                stats['no_explicit_target_threshold_count']+=1
                warnings.append(f'{group["id"]}: AoE target threshold is not explicit in the heading')
            chapter=section_map.get(group['source_chapter'])
            if chapter is None:errors.append(f'{group["id"]}: source section missing')
            ranks=[]
            for i,rule in enumerate(group['rules'],start=1):
                stats['priority_row_count']+=1
                all_ids.append(rule['id'])
                if rule['order']!=i:
                    errors.append(f'{rule["id"]}: wrong row order')
                if rule['priority_number'] is not None:
                    ranks.append(rule['priority_number'])
                action=rule['action']
                if action['spell_id'] is None:
                    stats['unresolved_spell_id_count']+=1
                elif (action['spell_id'],action['spell_name_ko']) not in glossary:
                    errors.append(f'{rule["id"]}: spell ID/name pair not present in V11 glossary')
                if rule['review']['state']!='pending':
                    errors.append(f'{rule["id"]}: cannot auto-approve without external source audit')
                if rule['evidence']['original_wowhead_passage_verified']:
                    errors.append(f'{rule["id"]}: V11 internal evidence cannot prove external Wowhead source')
                if digest(rule['evidence']['evidence_ko'])!=rule['evidence']['evidence_sha256']:
                    errors.append(f'{rule["id"]}: evidence checksum mismatch')
            if ranks!=sorted(ranks) or len(ranks)!=len(set(ranks)):
                errors.append(f'{group["id"]}: invalid priority ordering/duplicates')
        for item in advice:
            all_ids.append(item['id'])
            if item['review']['state']!='pending':
                errors.append(f'{item["id"]}: cannot auto-approve unsupported advice')
            if digest(item['evidence']['evidence_ko'])!=item['evidence']['evidence_sha256']:
                errors.append(f'{item["id"]}: evidence checksum mismatch')
        dup=[k for k,n in Counter(all_ids).items() if n>1]
        if dup:errors.append(f'{guide["id"]}: duplicate logical IDs {dup}')
        for section in guide['sections']:
            if sha(section['html'])!=section['source_sha256']:
                errors.append(f'{guide["id"]}/{section["id"]}: source chapter HTML checksum mismatch')
    result={'status':'PASS' if not errors else 'FAIL', 'stats':stats,
            'errors':errors,'warnings':warnings,
            'caveat':'Only schema, provenance, and coherence verified; game semantics and official Korean spell names are NOT certified.'}
    return result


def main():
    report=validate_directory()
    out=ROOT/'dist'/'rule_validation_report.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='warnings'},ensure_ascii=False,indent=2))
    print('Non-blocking warnings:',len(report['warnings']))
    print('Full report:',out)
    if report['errors']: raise SystemExit(1)

if __name__=='__main__':main()
