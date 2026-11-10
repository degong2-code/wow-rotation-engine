"""Conservative, tri-state rule evaluation for manually curated V11-derived examples.

It is NOT a rotation solver: result only says which *example contract* applies.
Unknown or missing context never silently becomes false or true.
"""
from __future__ import annotations
from pathlib import Path
from .build import ROOT, read_json, sha
from bs4 import BeautifulSoup

MISSING=object()
ALLOWED_FIELDS={'hero','target_count','phase','combo_points','combo_point_cap','combat_mode'}


def scalar(node:dict,context:dict):
    if 'field' in node:
        name=node['field']
        if name not in ALLOWED_FIELDS and not name.startswith('buff:') and not name.startswith('ready:') and not name.startswith('talent:'):
            raise ValueError(f'Unknown condition field: {name}')
        if name.startswith('buff:'):
            return context.get('buffs',{}).get(name[5:],MISSING)
        if name.startswith('ready:'):
            return context.get('ready',{}).get(name[6:],MISSING)
        if name.startswith('talent:'):
            return context.get('talents',{}).get(name[7:],MISSING)
        return context.get(name,MISSING)
    return node.get('value',MISSING)


def evaluate(node:dict,context:dict)->bool | None:
    if 'all' in node:
        vals=[evaluate(x,context) for x in node['all']]
        return False if False in vals else None if None in vals else True
    if 'any' in node:
        vals=[evaluate(x,context) for x in node['any']]
        return True if True in vals else None if None in vals else False
    if 'not' in node:
        v=evaluate(node['not'],context)
        return None if v is None else not v
    op=node.get('op')
    if op not in ('eq','gte','lte','ne'):
        raise ValueError(f'Unsupported conditional operator: {op}')
    left=scalar({'field':node['field']},context)
    right=scalar({'field':node['rhs_field']},context) if 'rhs_field' in node else scalar({'value':node.get('value',MISSING)},context)
    if left is MISSING or right is MISSING or left is None or right is None:
        return None
    if op in ('gte','lte') and (type(left) not in (int,float) or type(right) not in (int,float)):
        raise ValueError(f'Numeric comparison requires numeric values: {node}')
    return {'eq':lambda:left==right,'ne':lambda:left!=right,'gte':lambda:left>=right,'lte':lambda:left<=right}[op]()


def validate_catalog(root:Path=ROOT)->list[str]:
    errors=[]
    docs=read_json(root/'content'/'semantic_contracts.json')
    registry=read_json(root/'content'/'registry.json')
    gids={r['id'] for r in registry['guides']}
    seen=set()
    for rule in docs['contracts']:
        cid=rule['id']
        if cid in seen:errors.append(f'duplicate contract: {cid}')
        seen.add(cid)
        if rule['guide_id'] not in gids:
            errors.append(f'{cid}: undeclared guide')
            continue
        guide=read_json(root/'content'/next(r['file'] for r in registry['guides'] if r['id']==rule['guide_id']))
        sect=next((s for s in guide['sections'] if s['id']==rule['source']['chapter_id']),None)
        if sect is None:
            errors.append(f'{cid}: missing cited chapter')
            continue
        if sha(sect['html'])!=rule['source']['chapter_sha256']:
            errors.append(f'{cid}: source chapter checksum does not match')
        source=BeautifulSoup(sect['html'],'html.parser').get_text(' ',strip=True)
        quote=rule['source']['quote_ko']
        if quote not in source:
            errors.append(f'{cid}: claimed evidence quote absent from V11 chapter: {quote[:60]}')
        if rule['review_state']!='pending_external_source_validation':
            errors.append(f'{cid}: cannot use automatic approval for curated, unverified contract')
        spell_id=rule['recommendation'].get('spell_id')
        if spell_id is not None and not any(e['spell_id']==spell_id for e in guide['glossary_index']):
            errors.append(f'{cid}: spell ID is not mapped in current guide glossary')
        try:
            # Must parse and evaluate without missing-information coercion.
            evaluate(rule['when'],{})
        except (TypeError,ValueError) as exc:
            errors.append(f'{cid}: malformed condition {exc}')
    return errors


def applicable(context:dict,root:Path=ROOT)->dict:
    data=read_json(root/'content'/'semantic_contracts.json')
    result={'applicable':[],'inapplicable':[],'unknown':[],
            'caveat':'Examples only, not sufficient to determine a full optimal rotation.'}
    for c in data['contracts']:
        gid=context.get('guide_id',MISSING)
        if gid is MISSING or gid!=c['guide_id']:
            continue
        res=evaluate(c['when'],context)
        dest='unknown' if res is None else 'applicable' if res else 'inapplicable'
        result[dest].append({'id':c['id'],'recommendation':c['recommendation']})
    return result

if __name__=='__main__':
    errors=validate_catalog()
    print('Semantic sample contracts:',len(read_json(ROOT/'content'/'semantic_contracts.json')['contracts']))
    print('Validation:','PASS' if not errors else 'FAIL')
    for e in errors:print('ERROR',e)
    if errors:raise SystemExit(1)
