"""Score atomic-repair v2 predictions. CPU-only, stdlib-only.

Modes:
  --mode inject  : knowledge floor. accuracy of fact/rule recall vs inject.jsonl.
                   --sanity makes it the cleanliness gate (base model should ~0) or
                   the learned gate (injected model should ~100%).
  --mode repair  : per-9-cell metrics vs repair_eval.jsonl. Skill-free final_answer
                   signal + per-cell accuracy + accept-rates on the Cor cells.

Align by ROW INDEX vs --eval-source (zero-shot has no gold string).
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

CELLS = ["K-Aug", "K-Abl", "K-Cor", "R-Aug", "R-Abl", "R-Cor", "H-Aug", "H-Abl", "H-Cor", "Clean"]


def load_pred(p):
    rows = []
    for line in p.open():
        line = line.strip()
        if not line:
            continue
        o = json.loads(line)
        rows.append(o.get("predict", o.get("prediction", o.get("output", ""))))
    return rows


def load_jsonl(p):
    with p.open() as f:
        return [json.loads(l) for l in f if l.strip()]


def parse_json(t):
    if not t:
        return None
    try:
        o = json.loads(t)
        return o if isinstance(o, dict) else None
    except Exception:
        pass
    s = t.find("{")
    while s != -1:
        depth = 0
        for e in range(s, len(t)):
            if t[e] == "{":
                depth += 1
            elif t[e] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        o = json.loads(t[s:e+1])
                        if isinstance(o, dict):
                            return o
                    except Exception:
                        break
        s = t.find("{", s + 1)
    return None


def norm(s):
    if s is None:
        return ""
    return re.sub(r"[\s.]+$", "", str(s).strip()).lower()


def final_answer(t):
    o = parse_json(t)
    if o and "final_answer" in o:
        return str(o["final_answer"])
    m = re.search(r"final answer\s*[:\-]\s*(.+)", t or "", re.I)
    if m:
        return m.group(1).strip().splitlines()[0]
    lines = [x.strip() for x in (t or "").splitlines() if x.strip()]
    return lines[-1] if lines else ""


def boot_ci(hits, n=2000, seed=0):
    m = len(hits)
    if not m:
        return [0, 0]
    st = seed | 1
    means = []
    for _ in range(n):
        s = 0
        for _ in range(m):
            st = (1103515245 * st + 12345) & 0x7FFFFFFF
            s += hits[st % m]
        means.append(s / m)
    means.sort()
    return [round(means[int(0.025*n)], 4), round(means[int(0.975*n)], 4)]


def stat(h):
    return {"n": len(h), "acc": round(sum(h)/len(h), 4) if h else None, "ci95": boot_ci(h) if h else [0, 0]}


def eval_inject(pred, src, out, sanity, thresh):
    P = load_pred(pred)
    S = load_jsonl(src)
    n = min(len(P), len(S))
    hits, leaked = [], []
    by_kind = defaultdict(list)
    for i in range(n):
        gold = norm(S[i]["answer"])
        got = norm(final_answer(P[i]))
        # entity facts: exact/substring; rule facts: check rule short-form keywords present
        if S[i]["kind"] == "rule_fact":
            hit = int(any(w in got for w in gold.split()[:6]))
        else:
            hit = int(got == gold or (gold and gold in got))
        hits.append(hit)
        by_kind[S[i]["kind"]].append(hit)
        if hit and sanity:
            leaked.append(S[i].get("question"))
    acc = sum(hits)/len(hits) if hits else 0.0
    rep = {"mode": "inject", "overall": stat(hits),
           "by_kind": {k: stat(v) for k, v in by_kind.items()}, "hit_vector": hits}
    if sanity:
        rep["sanity"] = {"threshold": thresh, "acc": round(acc, 4),
                         "passed_clean": acc <= thresh, "leaked": len(leaked)}
    out.write_text(json.dumps(rep, indent=2, ensure_ascii=False))
    print(f"[inject] acc={acc:.3f} (n={len(hits)})", "-> ", out)


def eval_repair(pred, src, out, report):
    P = load_pred(pred)
    S = load_jsonl(src)
    n = min(len(P), len(S))
    per = {c: {"final": [], "json": [], "diag": [], "skill": []} for c in CELLS}
    accept = defaultdict(list)  # cell -> planted-wrong accept
    over, under = [], []
    has_skill = False
    for i in range(n):
        r = S[i]
        c = r["cell"]
        t = P[i]
        gold = norm(r["gold_answer"])
        tent = norm(r["tentative_answer"])
        fa = norm(final_answer(t))
        o = parse_json(t)
        per[c]["final"].append(int(fa == gold))
        per[c]["json"].append(int(o is not None))
        changed = fa != tent
        if c == "Clean":
            over.append(int(changed))
        else:
            under.append(int(not changed))
        if c.endswith("Cor"):
            accept[c].append(int(fa == norm(r["planted_wrong_answer"])))
        if o and "diagnosis" in o:
            has_skill = True
            per[c]["diag"].append(int(o["diagnosis"] == r["diagnosis"]))
        if o and "repair_skill" in o:
            has_skill = True
            per[c]["skill"].append(int(o["repair_skill"] == r["repair_skill"]))
    allf = [x for c in CELLS for x in per[c]["final"]]
    rep = {"mode": "repair", "overall_final": stat(allf),
           "per_cell": {c: {"n": len(per[c]["final"]), "final_answer": stat(per[c]["final"]),
                            "json_valid": stat(per[c]["json"]), "diagnosis": stat(per[c]["diag"]),
                            "repair_skill": stat(per[c]["skill"])} for c in CELLS},
           "failure_modes": {"over_repair_clean": stat(over), "under_repair_nonclean": stat(under),
                             "kcor_accept": stat(accept.get("K-Cor", [])),
                             "rcor_accept": stat(accept.get("R-Cor", [])),
                             "hcor_accept": stat(accept.get("H-Cor", []))},
           "has_skill_labels": has_skill,
           "per_cell_final_vectors": {c: per[c]["final"] for c in CELLS},
           "hit_vector_final": allf}
    out.write_text(json.dumps(rep, indent=2, ensure_ascii=False))
    print(f"[repair] final={rep['overall_final']['acc']} (n={len(allf)}) skill={has_skill} ->", out)
    if report:
        L = ["# v2 repair eval", "", f"Overall final_answer: {_p(rep['overall_final'])}", "",
             "| cell | n | final | json | diagnosis | skill |", "|---|---|---|---|---|---|"]
        for c in CELLS:
            pc = rep["per_cell"][c]
            L.append(f"| {c} | {pc['n']} | {_p(pc['final_answer'])} | {_p(pc['json_valid'])} | {_p(pc['diagnosis'])} | {_p(pc['repair_skill'])} |")
        fm = rep["failure_modes"]
        L += ["", f"- Clean over-repair: {_p(fm['over_repair_clean'])}",
              f"- under-repair (non-Clean): {_p(fm['under_repair_nonclean'])}",
              f"- K-Cor accept: {_p(fm['kcor_accept'])} | R-Cor accept: {_p(fm['rcor_accept'])} | H-Cor accept: {_p(fm['hcor_accept'])}"]
        report.write_text("\n".join(L))
        print("wrote", report)


def _p(s):
    if s.get("acc") is None:
        return "n/a"
    return f"{s['acc']*100:.1f}% [{s['ci95'][0]*100:.0f},{s['ci95'][1]*100:.0f}] (n={s['n']})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["inject", "repair"], required=True)
    ap.add_argument("--pred", type=Path, required=True)
    ap.add_argument("--eval-source", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--report", type=Path, default=None)
    ap.add_argument("--sanity", action="store_true")
    ap.add_argument("--sanity-thresh", type=float, default=0.05)
    a = ap.parse_args()
    if a.mode == "inject":
        eval_inject(a.pred, a.eval_source, a.out, a.sanity, a.sanity_thresh)
    else:
        eval_repair(a.pred, a.eval_source, a.out, a.report)


if __name__ == "__main__":
    main()
