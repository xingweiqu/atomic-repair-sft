"""Score v2.1 predictions: per-cell repair + the 4 repair-decision metrics.

Adds to evaluate_v2: false-keep rate, tentative-copy rate, gold-in-trace-but-wrong,
repair-decision accuracy (keep vs repair). Handles all v2.1 output schemas:
CoT, Skill+CoT, RandomSkill, Decision (repair_decision), Actionized (trace prefix).

Usage:
  python evaluate_v2_1.py --pred P --eval-source data_v2_1/repair_eval.jsonl --out R.json [--report R.md]
"""
from __future__ import annotations
import argparse, json, re
from collections import defaultdict
from pathlib import Path

CELLS = ["K-Aug","K-Abl","K-Cor","R-Aug","R-Abl","R-Cor","H-Aug","H-Abl","H-Cor","Clean"]


def load_pred(p):
    return [json.loads(l).get("predict","") for l in p.open() if l.strip()]
def load_src(p):
    return [json.loads(l) for l in p.open() if l.strip()]
def parse(t):
    try: return json.loads(t)
    except:
        m=re.search(r'\{.*\}',t,re.S)
        try: return json.loads(m.group(0)) if m else None
        except: return None
def norm(s): return re.sub(r'[\s.]+$','',str(s or '').strip()).lower()
def final(o,raw):
    if o and 'final_answer' in o: return o['final_answer']
    m=re.search(r'final answer\s*[:\-]\s*(.+)',raw or '',re.I)
    if m: return m.group(1).splitlines()[0]
    return (raw or '').strip().splitlines()[-1] if raw else ''
def decision(o):
    if not o: return None
    if 'repair_decision' in o: return o['repair_decision']
    tr=norm(o.get('repair_trace'))
    if ('no repair needed' in tr) or ('is correct' in tr and ' not ' not in tr): return 'keep'
    return 'repair'
def boot(h,n=2000,seed=0):
    m=len(h)
    if not m: return [0,0]
    st=seed|1; means=[]
    for _ in range(n):
        s=0
        for _ in range(m):
            st=(1103515245*st+12345)&0x7FFFFFFF; s+=h[st%m]
        means.append(s/m)
    means.sort(); return [round(means[int(.025*n)],4),round(means[int(.975*n)],4)]
def stat(h): return {"n":len(h),"acc":round(sum(h)/len(h),4) if h else None,"ci95":boot(h) if h else [0,0]}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--pred",type=Path,required=True)
    ap.add_argument("--eval-source",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--report",type=Path,default=None)
    a=ap.parse_args()
    P=load_pred(a.pred); S=load_src(a.eval_source); n=min(len(P),len(S))
    per={c:{"final":[],"json":[],"skill":[],"dec":[]} for c in CELLS}
    fk=[]; tc=[]; git=[]  # false-keep, tentative-copy, gold-in-trace-wrong
    over=[]
    for i in range(n):
        r=S[i]; c=r["cell"]; o=parse(P[i])
        g=norm(r["gold_answer"]); t=norm(r["tentative_answer"])
        fa=norm(final(o,P[i])); tr=norm(o.get("repair_trace") if o else "")
        per[c]["final"].append(int(fa==g))
        per[c]["json"].append(int(o is not None))
        if o and "repair_skill" in o:
            per[c]["skill"].append(int(o["repair_skill"]==r["repair_skill"]))
        gold_dec="keep" if c=="Clean" else "repair"
        dec=decision(o)
        per[c]["dec"].append(int(dec==gold_dec))
        if c=="Clean": over.append(int(fa!=t))
        if dec=="keep" and c!="Clean": fk.append(1)
        else: fk.append(0)
        tc.append(int(fa==t and fa!=g))
        git.append(int(bool(g and g in tr and fa!=g)))
    allf=[x for c in CELLS for x in per[c]["final"]]
    rep={"overall_final":stat(allf),
         "per_cell":{c:{"n":len(per[c]["final"]),"final":stat(per[c]["final"]),
                        "json":stat(per[c]["json"]),"skill":stat(per[c]["skill"]),
                        "decision_acc":stat(per[c]["dec"])} for c in CELLS},
         "decision_metrics":{"false_keep":sum(fk),"tentative_copy":sum(tc),
                             "gold_in_trace_but_wrong":sum(git),
                             "repair_decision_acc":stat([x for c in CELLS for x in per[c]["dec"]]),
                             "clean_over_repair":stat(over)},
         "hit_vector_final":allf,
         "per_cell_final_vectors":{c:per[c]["final"] for c in CELLS}}
    a.out.write_text(json.dumps(rep,indent=2,ensure_ascii=False))
    print(f"final={rep['overall_final']['acc']} (n={len(allf)}) "
          f"false_keep={sum(fk)} tent_copy={sum(tc)} decision_acc={rep['decision_metrics']['repair_decision_acc']['acc']} -> {a.out}")
    if a.report:
        L=[f"# {a.pred.parent.name}","",f"overall final: {rep['overall_final']['acc']}",
           f"false-keep: {sum(fk)} | tentative-copy: {sum(tc)} | gold-in-trace-but-wrong: {sum(git)}",
           f"repair-decision acc: {rep['decision_metrics']['repair_decision_acc']['acc']}",
           "","| cell | final | decision-acc |","|---|---|---|"]
        for c in CELLS:
            pc=rep["per_cell"][c]
            fa_=pc["final"]["acc"]; da=pc["decision_acc"]["acc"]
            L.append(f"| {c} | {fa_*100:.1f}% | {da*100:.1f}% |")
        a.report.write_text("\n".join(L)); print("wrote",a.report)


if __name__=="__main__":
    main()
