"""Fail-closed, provenance-aware rule changes. Report only; NEVER auto-edit the HTML.

python -m engine.diff_rules --before content/rules --after /path/to/proposed/rules --output dist/diff.json
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .build import ROOT, read_json


def items(doc):
    rows={}
    for g in doc['rotation_groups']:
        rows[g['id']]={'kind':'group','value':g['scenario']}
        for r in g['rules']:
            rows[r['id']]={'kind':'rotation','value':{
                'order':r['order'], 'priority_number':r['priority_number'],
                'action':r['action'], 'condition':r['condition'],
                'evidence':r['evidence']}}
    for a in doc['advanced_guidance']:
        rows[a['id']]={'kind':'advanced','value':{'text_ko':a['text_ko'],
            'evidence':a['evidence'],'kind':a['kind']}}
    return rows


def diff_documents(before,after):
    changes=[]
    if before['guide_id']!=after['guide_id']:
        raise ValueError('Refusing to compare different guide IDs')
    b,a=items(before),items(after)
    for key in sorted(set(b)|set(a)):
        old,new=b.get(key),a.get(key)
        if old==new: continue
        kind=(new or old)['kind']
        severity='critical' if old is None or new is None else 'high' if kind in ('rotation','group') else 'medium'
        changes.append({'id':key,'type':'added' if old is None else 'removed' if new is None else 'modified',
                        'kind':kind,'severity':severity, 'previous':old,'proposed':new,
                        'automatic_publish_allowed':False})
    return changes


def diff_dirs(before:Path,after:Path)->dict:
    found=[]
    names={p.name for p in before.glob('*.json')}|{p.name for p in after.glob('*.json')}
    for name in sorted(names):
        bp=before/name; ap=after/name
        if not bp.exists() or not ap.exists():
            found.append({'id':name, 'type':'file_missing_or_added', 'severity':'critical',
                          'automatic_publish_allowed':False});continue
        found += diff_documents(read_json(bp),read_json(ap))
    risks={'critical':0,'high':0,'medium':0}
    for e in found:
        risks[e['severity']]+=1
    return {'status':'no_changes' if not found else 'review_required',
            'change_count':len(found), 'risk_counts':risks,
            'auto_publish_allowed':False,'changes':found}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--before',type=Path,default=ROOT/'content'/'rules')
    parser.add_argument('--after',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'dist'/'rule_change_report.json')
    args=parser.parse_args()
    report=diff_dirs(args.before,args.after)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'status':report['status'],'change_count':report['change_count'],
                      'risk_counts':report['risk_counts'],'auto_publish_allowed':False},ensure_ascii=False,indent=2))
    print('Saved:',args.output)

if __name__=='__main__':main()
