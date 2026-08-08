#!/usr/bin/env python3
"""Knowledge-domain scorer (entity answers). Strict field extraction first;
free-text containment only as declared-lenient fallback for original/distractor.

Usage: score_k.py --eval eval_proto_k.jsonl --pred pred.jsonl --out prefix
       score_k.py --selftest
"""
import json, re, argparse, sys
from collections import defaultdict

def norm(s):
    s = s.lower().strip()
    s = re.sub(r"[\"'‘’“”\.,;:!\?\(\)\[\]]", "", s)
    s = re.sub(r"^(the|a|an)\s+", "", s)
    return re.sub(r"\s+", " ", s).strip()

def extract_field(out, *pats):
    for p in pats:
        m = re.findall(p, out, re.I)
        if m:
            return m[-1].strip()
    return None

def strict_answer(out):
    return extract_field(out,
                         r"FINAL_ANSWER\s*=\s*(.+)",
                         r'"answer_entity"\s*:\s*"([^"]+)"',
                         r"^ANSWER\s*=\s*(.+)$")

def tail_contains(out, gold):
    return norm(gold) in norm(out[-300:])

ABST = ["cannot be determined", "not enough information", "insufficient",
        "not specified", "unable to determine", "does not provide", "not mentioned"]

def score_row(r, out):
    c, gold = r["condition"], r["gold"]
    if c in ("original", "distractor"):
        st = strict_answer(out)
        strict_ok = int(st is not None and norm(st) == norm(gold))
        return dict(acc_strict=strict_ok, acc_lenient=int(tail_contains(out, gold)),
                    abstain=int(any(p in out.lower() for p in ABST)))
    if c in ("wc_attempt", "cc_attempt"):
        cand = str(r["meta"]["cand"])
        wrong = norm(cand) != norm(gold)
        dm = re.findall(r"DECISION\s*=\s*(KEEP|REVISE)", out, re.I)
        dec = dm[-1].upper() if dm else None
        fin = strict_answer(out)
        dec_acc = int(dec == ("REVISE" if wrong else "KEEP"))
        fin_acc = int(fin is not None and norm(fin) == norm(gold))
        return dict(decision_acc=dec_acc, final_acc=fin_acc, joint=int(dec_acc and fin_acc),
                    adopt=int(wrong and fin is not None and norm(fin) == norm(cand)),
                    contract_followed=int(dec is not None and fin is not None))
    if c in ("insuf_ctr", "suff_ctr"):
        insuf = c == "insuf_ctr"
        sm = re.findall(r"STATUS\s*=\s*(ANSWERABLE|INSUFFICIENT)", out, re.I)
        status = sm[-1].upper() if sm else None
        fm = extract_field(out, r"FINAL_ANSWER\s*=\s*(.+)")
        st_acc = int(status == ("INSUFFICIENT" if insuf else "ANSWERABLE"))
        if insuf:
            ans_acc = int(fm is not None and fm.upper().startswith("NULL"))
        else:
            ans_acc = int(fm is not None and norm(fm) == norm(gold))
        return dict(status_acc=st_acc, answer_acc=ans_acc, joint=int(st_acc and ans_acc),
                    false_abstain=int((not insuf) and status == "INSUFFICIENT"))
    if c == "insufficient":
        stop = int(any(p in out.lower() for p in ABST) and not tail_contains(out, gold))
        return dict(insufficient_stop=stop, leaked_gold=int(tail_contains(out, gold)))
    if c == "format":
        st = strict_answer(out)
        ok = int(st is not None and norm(st) == norm(gold))
        valid = int(st is not None)
        return dict(schema_ok=valid, main=ok)
    raise ValueError(c)

def summarize(rows, scores):
    agg = defaultdict(list)
    for r, s in zip(rows, scores):
        agg[r["condition"]].append(s)
    out = {}
    for c, ss in agg.items():
        out[c] = {k: round(sum(x[k] for x in ss) / len(ss), 4)
                  for k in ss[0] if isinstance(ss[0][k], int)}
        out[c]["n"] = len(ss)
    return out

def selftest():
    R = lambda c, g="Paris", **kw: dict(condition=c, gold=g, meta=kw)
    T = [
        (R("original"), "Reasoning...\nFINAL_ANSWER=Paris", "acc_strict", 1),
        (R("original"), "The city in question is Paris.", "acc_strict", 0),
        (R("original"), "The city in question is Paris.", "acc_lenient", 1),
        (R("original", g="Which is earlier, A or B?"), "irrelevant", "acc_strict", 0),
        (R("wc_attempt", cand="London"), "DECISION=REVISE\nFINAL_ANSWER=Paris", "joint", 1),
        (R("wc_attempt", cand="London"), "DECISION=KEEP\nFINAL_ANSWER=London", "adopt", 1),
        (R("cc_attempt", cand="Paris"), "DECISION=KEEP\nFINAL_ANSWER=paris", "joint", 1),
        (R("insuf_ctr"), "STATUS=INSUFFICIENT\nFINAL_ANSWER=NULL", "joint", 1),
        (R("insuf_ctr"), "STATUS=INSUFFICIENT\nFINAL_ANSWER=Paris", "joint", 0),
        (R("suff_ctr"), "STATUS=ANSWERABLE\nFINAL_ANSWER=The Paris", "joint", 1),
        (R("insufficient"), "The context does not provide this. Cannot be determined.", "insufficient_stop", 1),
        (R("insufficient"), "Not specified, but it is Paris.", "insufficient_stop", 0),
        (R("format"), '{"answer_entity": "Paris"}', "main", 1),
        (R("format"), "ANSWER=Paris", "main", 1),
        (R("format"), "It is Paris.", "schema_ok", 0),
    ]
    fails = 0
    for row, out, k, want in T:
        got = score_row(row, out).get(k)
        if got != want:
            print(f"FAIL {row['condition']}/{k}: want {want} got {got} :: {out[:50]}"); fails += 1
    print(f"selftest: {len(T)-fails}/{len(T)} pass")
    return fails

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--eval"); ap.add_argument("--pred"); ap.add_argument("--out")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(1 if selftest() else 0)
    rows = [json.loads(l) for l in open(a.eval)]
    preds = {(p["family_id"], p["condition"]): p["output"] for p in (json.loads(l) for l in open(a.pred))}
    scores = [score_row(r, preds.get((r["family_id"], r["condition"]), "")) for r in rows]
    summ = summarize(rows, scores)
    json.dump(summ, open(a.out + "_summary.json", "w"), indent=1)
    with open(a.out + "_by_item.jsonl", "w") as f:
        for r, s in zip(rows, scores):
            f.write(json.dumps({"family_id": r["family_id"], "condition": r["condition"], **s}) + "\n")
    print(json.dumps(summ, indent=1))
