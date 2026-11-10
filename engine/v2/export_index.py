"""Read-only index over provenance-first v2 rule candidate store."""
from __future__ import annotations
from pathlib import Path
import json
from .build import ROOT,read_json


def index_all():
    registry=read_json(ROOT/'content'/'registry.json')
    out={'schema_version':2,
         'source':'V11 HTML imported as review-pending structured rule candidates',
         'warning':'Not a verified optimizer; snippets and spell IDs imported from V11, not independently checked against Wowhead.',
         'guides':{}}
    for rec in registry['guides']:
        doc=read_json(ROOT/'content'/'rules'/f'{rec["id"]}.json')
        out['guides'][rec['id']]={
            'priority_tables':[{ 'id':g['id'], 'heading':g['source_heading'],
                                'hero':g['scenario']['hero'],
                                'rows':[{'id':r['id'],'priority':r['priority_label'],
                                         'action':r['action']['raw_ko'],
                                         'condition':r['condition']['raw_ko'],
                                         'source':r['evidence']['chapter_id']} for r in g['rules']]}
                                for g in doc['rotation_groups']],
            'advanced_items':[{'id':tip['id'],'heading':tip['title_ko'],
                               'text':tip['text_ko'],'source':tip['evidence']['chapter_id']}
                              for tip in doc['advanced_guidance']],
        }
    return out

if __name__=='__main__':
    out=ROOT/'dist'/'extracted_priority_and_advanced_index.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    idx=index_all()
    out.write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for gid,x in idx['guides'].items():
        print(f'{gid}: {len(x["priority_tables"])} tables, {len(x["advanced_items"])} advanced items')
    print('Saved:',out)
