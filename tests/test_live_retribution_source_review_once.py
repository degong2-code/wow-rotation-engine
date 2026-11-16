"""Temporary source-grounded Retribution WHML review; emit only short row metadata."""
import json,re,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from engine.source_acquisition_pipeline import run_specialization
from engine.embedded_markup import TAG, _attrs
class Review(unittest.TestCase):
    def test_retribution_hero_st_whml(self):
        try:
            with TemporaryDirectory() as temp:
                audit=run_specialization("징벌 성기사",Path(temp),expected_patch="12.1.5")
                packet=json.loads((Path(temp)/"editorial-evidence-private.json").read_text(encoding="utf8"))
                p=packet["payloads"][0]
                body=p["original_whml"]
                print("RET_SOURCE",json.dumps({"sha":p["sha256"],"chars":len(body),"patch":audit.get("visible_patch_candidates"),"date":audit.get("observed_guide_update_date"),"options":[x.get("id") for x in p["option_definitions"]],"tooltip_count":audit.get("named_tooltip_definition_count")}),flush=True)
                h1=body.lower().find("best retribution paladin single target rotation")
                h2=body.lower().find("aoe rotation",h1+1)
                if h2<0: h2=body.lower().find("multitarget rotation",h1+1)
                if h2<0: h2=min(len(body),h1+8500)
                print("RET_SECTION_MARKERS",json.dumps([{"i":m.start(),"text":body[max(0,m.start()-35):m.start()+45].replace("\\n"," ")} for m in list(re.finditer(r"(?i)(?:single.target|aoe|priority)",body)) if h1<=m.start()<h1+5500][:22]),flush=True)
                print("RET_BOUNDS",json.dumps({"st":h1,"aoe":h2,"prefix":re.sub(r"\s+"," ",body[h1:h1+420])[:260]}),flush=True)
                region=body[h1:h2] if 0<=h1<h2 else ""
                print("RET_ST_TAGS",json.dumps({k:len(re.findall(r"\["+k+r"\b",region,re.I)) for k in ["ol","li","display-option","toggler","rt-step","spell","tooltip","tab"]}),flush=True)
                # Every source list item in ST region, no complete guide reproduction.
                rows=[]
                for m in re.finditer(r"\[li([^\]]*)\](.*?)\[/li\]",region,re.I|re.S):
                    text=m.group(2)
                    ids=[x for x in re.findall(r"\[spell\s*=\s*(\d{2,8})",text,re.I)]
                    # Fact-like keys, small condition preview only (not all source prose)
                    plain=re.sub(r"\[[^\]]+\]"," ",text)
                    plain=re.sub(r"<[^>]+>"," ",plain)
                    plain=re.sub(r"\s+"," ",plain).strip()
                    rows.append({"i":len(rows)+1,"offset":m.start(),"spell_ids":ids[:7],"short":plain[:110]})
                print("RET_ST_ROWS",json.dumps(rows[:55],ensure_ascii=False),flush=True)
                tags=[]
                for t in TAG.finditer(region):
                    a=_attrs(t.group(2))
                    if "display-options" in a or t.group(1).lower()=="display-option":
                        tags.append({"pos":t.start(),"tag":t.group(1).lower(),"condition":a.get("display-options",""),"attr":t.group(2)[:75]})
                print("RET_ST_CONDITIONALS",json.dumps(tags[:35],ensure_ascii=False),flush=True)
                # Brief surrounding structure for recognizing dynamic markup only
                print("RET_ST_FIRSTOL",json.dumps([region[max(0,m.start()-170):m.start()+120] for m in list(re.finditer(r"\[ol\b",region,re.I))[:3]],ensure_ascii=False),flush=True)
        except Exception as exc:
            print("RET_SOURCE_UNAVAILABLE",type(exc).__name__,str(exc)[:250],flush=True)
            self.fail("Cannot acquire exact 12.1.5 Wowhead source for this review")
