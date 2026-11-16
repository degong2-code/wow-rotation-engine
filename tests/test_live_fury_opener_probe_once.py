"""One-shot actual WHML metadata probe; no full third-party source in logs. Delete after use."""
import json, re, unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from collections import Counter
from engine.source_acquisition_pipeline import run_specialization
from engine.embedded_markup import TAG, _attrs

class Probe(unittest.TestCase):
    def test_live_fury_opener_metadata(self):
        try:
            with TemporaryDirectory() as t:
                report=run_specialization("분노 전사",Path(t))
                packet=json.loads((Path(t)/"editorial-evidence-private.json").read_text(encoding="utf8"))
                item=packet["payloads"][0]
                body=item["original_whml"]
                print("FURY_PROBE SOURCE",json.dumps({"len":len(body),"sha":item["sha256"],"patch":report.get("visible_patch_candidates"),"modified":report.get("observed_guide_update_date"),"tooltip":report["named_tooltip_definition_count"],"choices":report["option_definition_count"]}),flush=True)
                start=body.lower().find("best fury warrior opener")
                stop=body.lower().find("pre-combat checks",start)
                if start<0:
                    print("FURY_PROBE opener_heading_missing",flush=True)
                    return
                seg=body[start:stop if stop>start else start+40000]
                print("FURY_PROBE TAGS",json.dumps(Counter(m.group(1).lower() for m in TAG.finditer(seg)).most_common(30)),flush=True)
                for name in ("Single Target (Slayer)","Multitarget (Slayer)","Single Target (Thane)","Multitarget (Thane)","Slayer","Mountain Thane"):
                    pos=[m.start() for m in re.finditer(re.escape(name),seg,re.I)]
                    print("FURY_PROBE LABEL",json.dumps({"name":name,"offsets":pos[:8]}),flush=True)
                stages=[]
                for m in TAG.finditer(seg):
                    tag=m.group(1).lower()
                    if tag not in ("rt-step","rt-step-group","opener-step","rotation-step","step","rt-opener","rt-steps"):
                        continue
                    a=_attrs(m.group(2))
                    sample=seg[m.end():m.end()+550]
                    ids=re.findall(r"(?:spell|item|icon|id)[\\s=:]+[\\\"']?(\\d{3,8})",sample,re.I)
                    stages.append({"pos":m.start(),"tag":tag,"attrs":{k:v[:80] for k,v in a.items() if k in ("spell","id","display-options","name","type","offset","time","prepull")},"ids":ids[:8]})
                print("FURY_PROBE STAGES",json.dumps(stages[:80]),flush=True)
                cond=[]
                for m in TAG.finditer(seg):
                    a=_attrs(m.group(2))
                    if "display-options" in a:
                        cond.append({"pos":m.start(),"tag":m.group(1).lower(),"expr":a["display-options"][:100]})
                print("FURY_PROBE COND",json.dumps(cond[:60]),flush=True)
                print("FURY_PROBE OPTION_IDS",json.dumps([{"id":o["id"],"group":o["radio_group"]} for o in item["option_definitions"] if start<=o["position"]<start+len(seg)][:25]),flush=True)
        except Exception as e:
            print("FURY_PROBE UNAVAILABLE",type(e).__name__,str(e)[:180],flush=True)
            self.skipTest("Source unavailable; no content claim")
