"""Repackage an independently authored V11+ REVIEW draft into a canonical V11 shell.

This is a cross-specialization HTML assembly boundary, NOT a source→gameplay
parser or content generator. All editorial content/decisions come from the
supplied private authored input; this script preserves the original seven
V11 guide subtrees and deliberately does not claim Q0/Q1 approval.

Usage:
  python repackage_generic_v11.py --base PRIVATE_ORIGINAL_V11.html \
    --authored PRIVATE_AUTHORED_V11_PLUS.html --output PRIVATE_REVIEW.html

Never commit private HTML, raw source, or outputs to a public repository.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

OLD_IDS = ('fire', 'frost', 'dk', 'hunter', 'bm', 'rogue', 'assassination')
BASELINE_SHA256 = '5d70279c4dd073eccef1f3b13565a8f555cd81c9f0a5b7eda7e3485e410742be'
VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}


@dataclass
class Node:
    tag: str
    attrs: dict
    start: int
    open_end: int
    end: int = -1
    parent: object = None

    def has_class(self, value):
        return value in self.attrs.get('class', '').split()

    def raw(self, text):
        if self.end < self.open_end:
            raise ValueError('Open element is not closed: '+self.tag)
        return text[self.start:self.end]


class Scanner(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.text = text
        self.rows = [0]
        for i,ch in enumerate(text):
            if ch == '\n': self.rows.append(i+1)
        self.nodes=[]
        self.stack=[]
        self.feed(text)
        self.close()
        if self.stack:
            raise ValueError('Unclosed source HTML tags: '+repr([x.tag for x in self.stack[-5:]]))

    def pos(self):
        line, col = self.getpos()
        return self.rows[line-1]+col

    def handle_starttag(self,tag,attrs):
        off=self.pos()
        token=self.get_starttag_text()
        node=Node(tag,dict(attrs),off,off+len(token),parent=self.stack[-1] if self.stack else None)
        self.nodes.append(node)
        if tag not in VOID: self.stack.append(node)
        else: node.end=node.open_end

    def handle_startendtag(self,tag,attrs):
        off=self.pos();token=self.get_starttag_text()
        self.nodes.append(Node(tag,dict(attrs),off,off+len(token),off+len(token),self.stack[-1] if self.stack else None))

    def handle_endtag(self,tag):
        off=self.pos()
        close=self.text.find('>',off)
        if close<0:raise ValueError('Unterminated closing tag')
        if not self.stack or self.stack[-1].tag != tag:
            raise ValueError('Nested HTML mismatch at '+tag+' '+str(off))
        node=self.stack.pop()
        node.end=close+1

    def one(self,predicate):
        found=[n for n in self.nodes if predicate(n)]
        if len(found)!=1:raise ValueError('Expected one node; found '+str(len(found)))
        return found[0]

    def all(self,predicate):
        return [n for n in self.nodes if predicate(n)]


def guides(scanner):
    return {n.attrs.get('data-guide'):n for n in scanner.all(lambda n:n.tag=='div' and n.has_class('manual-view') and n.attrs.get('data-guide'))}


def h(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()

# Generic registrar. The old V11 bodies and their internal scripts/DOM remain unchanged.
# It intentionally does not depend on the appended spec's ID, hero names, or number of tables.
GENERIC_NAV_JS = r'''(()=>{
  const views=Object.fromEntries([...document.querySelectorAll('.manual-view[data-guide]')].map(v=>[v.dataset.guide,v]));
  const navs=[...document.querySelectorAll('.reader-toc[data-nav-guide]')];
  const bts=[...document.querySelectorAll('[data-guide-button]')];
  const choices=[...document.querySelectorAll('[data-select-hero]')];
  const jump=document.querySelector('.top-jump');
  const chosenHero=Object.fromEntries(Object.entries(views).map(([k,v])=>[k,v.dataset.hero||'']));
  let current='fire';
  function route(g,hero,scroll=true){
    if(!Object.prototype.hasOwnProperty.call(views,g))return;
    if(hero)chosenHero[g]=hero;
    current=g;
    for(const [id,v] of Object.entries(views)){
      v.classList.toggle('active',id===g);
      if(chosenHero[id])v.dataset.hero=chosenHero[id];
    }
    navs.forEach(n=>{n.hidden=n.dataset.navGuide!==g;});
    const group=bts.filter(b=>b.dataset.guideButton===g);
    const selected=group.find(b=>b.dataset.heroButton===chosenHero[g])||group[0];
    bts.forEach(b=>{
      const yes=b===selected;
      b.classList.toggle('active',yes);
      b.setAttribute('aria-pressed',String(yes));
    });
    choices.forEach(c=>{
      const guide=c.closest('.manual-view[data-guide]');
      if(guide)c.setAttribute('aria-pressed',String(c.dataset.selectHero===chosenHero[guide.dataset.guide]));
    });
    const sections=[...views[g].querySelectorAll('section[id]')];
    const rot=sections.find(s=>s.id.endsWith('-rotation')||s.id==='rotation');
    const overview=sections.find(s=>s.id.endsWith('-overview')||s.id==='overview')||sections[0];
    if(jump && rot)jump.href='#'+rot.id;
    const heading=views[g].querySelector('.intro h1,h1');
    const title=heading?.textContent?.trim()||g;
    const heroName=selected?.textContent?.trim()||'';
    document.title='WoW 딜사이클 교본 · '+title+(group.length>1?' · '+heroName:'');
    if(scroll){window.scrollTo({top:0,behavior:'instant'});
      if(overview)history.replaceState(null,'','#'+overview.id);}
  }
  bts.forEach(b=>b.addEventListener('click',()=>route(b.dataset.guideButton,b.dataset.heroButton,true)));
  choices.forEach(c=>c.addEventListener('click',()=>{
    const guide=c.closest('.manual-view[data-guide]');
    if(guide)route(guide.dataset.guide,c.dataset.selectHero,false);
  }));
  function restore(){
    let target='';try{target=decodeURIComponent(location.hash.slice(1));}catch(e){return;}
    if(!target)return;
    const targetElement=document.getElementById(target);
    const targetView=targetElement?.closest('.manual-view[data-guide]');
    if(targetView){route(targetView.dataset.guide,null,false);return;}
    // The oldest V11 sections may use generic id names rather than a spec prefix.
    if(targetElement)route('fire',null,false);
  }
  restore();window.addEventListener('hashchange',restore);
})();'''


def repackage(base_html, reviewed_html, *, expected_baseline_sha256=BASELINE_SHA256):
    if expected_baseline_sha256 and h(base_html)!=expected_baseline_sha256:
        raise ValueError('V11 baseline digest mismatch; refuse unreviewed source replacement')
    base=Scanner(base_html); authored=Scanner(reviewed_html)
    bg=guides(base); ag=guides(authored)
    if set(bg)!=set(OLD_IDS):raise ValueError('Source is not exactly seven original V11 guides')
    added=set(ag)-set(bg)
    if len(added)!=1 or not set(bg).issubset(ag):
        raise ValueError('Expected exactly one independently authored guide')
    spec=next(iter(added))
    if not re.fullmatch('[a-z][a-z0-9-]*',spec):raise ValueError('Unsafe guide identity')
    for id in OLD_IDS:
        if bg[id].raw(base_html)!=ag[id].raw(reviewed_html):
            raise ValueError('A legacy V11 guide subtree was modified: '+id)
    src_style=base.all(lambda n:n.tag=='style')
    new_style=authored.all(lambda n:n.tag=='style')
    if len(src_style)!=1 or not new_style or src_style[0].raw(base_html)!=new_style[0].raw(reviewed_html):
        raise ValueError('Original V11 stylesheet was modified')
    base_scripts=base.all(lambda n:n.tag=='script')
    authored_scripts=authored.all(lambda n:n.tag=='script')
    if len(base_scripts)!=2: raise ValueError('V11 baseline JS layout changed')
    source_script=base_scripts[0].raw(base_html)
    if sum(x.raw(reviewed_html)==source_script for x in authored_scripts)!=1:
        raise ValueError('Baseline V11 script was modified')
    # The source's navigation script can differ by specialization, but the
    # authored artifact must explicitly supply exactly one navigation script.
    edited_nav=[x for x in authored_scripts if x.attrs.get('type') is None
                and 'const views=' in x.raw(reviewed_html)]
    if len(edited_nav)!=1:
        raise ValueError('Expected exactly one authored navigation script')
    nav=authored.one(lambda n:n.tag=='nav' and n.has_class('toc'))
    old_nav=base.one(lambda n:n.tag=='nav' and n.has_class('toc'))
    old_main=base.one(lambda n:n.tag=='main')
    head=base.one(lambda n:n.tag=='head')
    body=base.one(lambda n:n.tag=='body')
    # Preserve exactly one extra guide JSON metadata source if present. Original
    # authored JSON may use different schemas; no semantic rewrite here.
    extra_scripts=[]
    for x in authored_scripts:
        if ag[spec].start <= x.start and x.end <= ag[spec].end:
            continue  # canonical metadata is already inside the authored guide
        if x.raw(reviewed_html)==source_script:continue
        if x.attrs.get('type')=='application/json' or (not x.attrs.get('type') and
             x.raw(reviewed_html)!=base_scripts[1].raw(base_html) and
             'const views=' not in x.raw(reviewed_html)):
            extra_scripts.append(x.raw(reviewed_html))
    # Make no further assumptions about authored section counts/hero names.
    additions='\n'+ag[spec].raw(reviewed_html)+'\n'
    notes={
       'spec':spec,'original_guide_count':7,'new_guide_bytes':len(ag[spec].raw(reviewed_html).encode()),
       'source_legacy_sha256':h(base_html),'reviewed_input_sha256':h(reviewed_html),
       'authored_html_preserved_in_guide':True,
       'new_guide_review_only':True,'gameplay_meaning_verified':False,
       'automatic_publish_allowed':False,
    }
    edits=[
        (old_nav.start,old_nav.end,nav.raw(reviewed_html)),
        (old_main.end-len('</main>'),old_main.end-len('</main>'),additions),
        (head.end-len('</head>'),head.end-len('</head>'),'\n'+'\n'.join(x.raw(reviewed_html) for x in new_style[1:])+'\n'),
        (base_scripts[1].start,base_scripts[1].end,'<script>\n'+GENERIC_NAV_JS+'\n</script>'),
        (body.end-len('</body>'),body.end-len('</body>'),'\n'+'\n'.join(extra_scripts)+'\n')
    ]
    # Apply edits in reverse offset order, leaving all original subtree bytes intact.
    result=base_html
    for start,end,new in sorted(edits,key=lambda e:e[0],reverse=True):
        result=result[:start]+new+result[end:]
    final=Scanner(result)
    fg=guides(final)
    if set(fg)!={*OLD_IDS,spec}:raise ValueError('Unexpected output guide set')
    if any(fg[id].raw(result)!=bg[id].raw(base_html) for id in OLD_IDS):
        raise ValueError('V11 existing guide subtree was altered')
    if fg[spec].raw(result)!=ag[spec].raw(reviewed_html):
        raise ValueError('Authored spec content altered by packaging')
    ids=[n.attrs['id'] for n in final.nodes if n.attrs.get('id')]
    if len(ids)!=len(set(ids)):
        from collections import Counter
        raise ValueError('Duplicate document ids '+str([k for k,v in Counter(ids).items() if v>1][:10]))
    if not final.all(lambda n:n.attrs.get('data-guide-button')==spec):
        raise ValueError('Missing new spec navigation')
    if not final.all(lambda n:n.has_class('reader-toc') and n.attrs.get('data-nav-guide')==spec):
        raise ValueError('Missing new spec TOC')
    notes['html_sha256']=h(result)
    notes['all_legacy_subtrees_byte_identical']=True
    notes['generated_bytes']=len(result.encode('utf8'))
    return result, notes


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',required=True,type=Path)
    p.add_argument('--authored',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    out,notes=repackage(a.base.read_text('utf8'),a.authored.read_text('utf8'))
    if a.output.exists(): raise FileExistsError('Do not overwrite an existing user HTML')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(out,encoding='utf8')
    print(json.dumps(notes,ensure_ascii=False,indent=2))

if __name__=='__main__':main()