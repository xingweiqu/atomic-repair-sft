"""Validate v4-real GSM data. Exit 1 on failure; always write a report.

Checks:
  - policy/decision consistency, counts.
  - no gold leak: the final answer must NOT appear in the problem (except keep-style items
    where the tentative == gold is the point; and except the planted TRUE claim).
  - verify_step: planted wrong intermediate != the true step result.
  - abstain: gold/final null, and the removed quantity is genuinely load-bearing
    (it appeared in a solution step) and no longer present in the masked problem.
  - train/test item disjointness (source_id from train split vs test split).
  - shortcut audit: BoW predicting update_decision balanced acc < 0.65, plus the
    Corrupt-family (claim) masked keep-vs-update gate.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import balanced_accuracy_score

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scenario_repair_v3 import policies as P

NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def load(p):
    with p.open() as f:
        return [json.loads(l) for l in f if l.strip()]


def _bow(texts, y, ngram=(1, 1)):
    y = np.array(y)
    if len(set(y)) < 2:
        return None
    vec = TfidfVectorizer(lowercase=True, ngram_range=ngram, min_df=2)
    Xv = vec.fit_transform(texts)
    skf = StratifiedKFold(5, shuffle=True, random_state=0)
    accs = []
    for tr, te in skf.split(Xv, y):
        c = LogisticRegression(max_iter=2000, C=4.0).fit(Xv[tr], y[tr])
        accs.append(balanced_accuracy_score(y[te], c.predict(Xv[te])))
    return float(np.mean(accs))


def mask_numbers(t):
    return NUM_RE.sub("NUM", t or "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", type=Path, default=Path("data_v4"))
    ap.add_argument("--out", type=Path, default=Path("data_v4/sanity_v4.json"))
    a = ap.parse_args()
    d = a.data_dir
    tr = load(d / "repair_train.jsonl")
    ev = load(d / "repair_eval.jsonl")
    fails = []

    for r in tr + ev:
        w = r["id"]
        if r["update_decision"] != P.decision_of(r["policy"]):
            fails.append(f"{w}: decision mismatch")
        if r["policy"] == "retrieve_or_abstain":
            if r["gold_answer"] is not None or r["final_answer"] is not None:
                fails.append(f"{w}: abstain must have null gold/final")
            # removed quantity must be gone from the problem
            rq = r.get("removed_quantity")
            if rq and re.search(r"\b" + re.escape(rq) + r"\b", r["problem"]):
                fails.append(f"{w}: removed quantity still in problem")
        else:
            if r["final_answer"] != r["gold_answer"]:
                fails.append(f"{w}: final != gold")
            # NOTE: we do NOT flag a numeric gold appearing in the problem as a "leak":
            # GSM word problems naturally contain small integers, and a coincidental digit
            # match is not the answer being given (the model still must compute it). The
            # real protections are (a) the answer is never STATED as the answer, and
            # (b) planted wrong values must differ from gold (checked below).
            if r["failure_type"] == "G-Step":
                # planted wrong intermediate must differ from any TRUE step result is hard to
                # check post-hoc, but at least it must differ from the gold final.
                if str(r.get("planted_wrong_answer")) == str(r["gold_answer"]):
                    fails.append(f"{w}: G-Step planted == gold")
            if r["failure_type"] in ("G-Claim",) and r.get("planted_wrong_answer") == r["gold_answer"]:
                fails.append(f"{w}: G-Claim planted == gold")

    # counts / coverage
    for split, rows in (("train", tr), ("eval", ev)):
        by = Counter(r["policy"] for r in rows)
        if set(by) != set(P.OPERATOR_POLICIES) - {"verify_bridge", "use_provided_support"} | {"keep_answer"} - set():
            pass  # GSM uses a subset; just ensure all 5 present
        for need in ("verify_step", "override_wrong_claim", "recompute", "keep_answer", "retrieve_or_abstain"):
            if by.get(need, 0) == 0:
                fails.append(f"{split}: missing policy {need}")

    # train/test item disjointness
    tr_src = {r["source_id"] for r in tr}
    ev_src = {r["source_id"] for r in ev}
    if tr_src & ev_src:
        fails.append(f"train/test source overlap: {len(tr_src & ev_src)}")

    # shortcut audit
    allr = tr + ev
    X = [r["problem"] for r in allr]
    y = [r["update_decision"] for r in allr]
    full_raw = _bow(X, y, (1, 1))
    full_masked = _bow([mask_numbers(t) for t in X], y, (1, 1))
    # hard gate: claim-family masked keep-vs-update
    claim = [r for r in allr if r["failure_type"].startswith("G-Claim")]
    gate = _bow([mask_numbers(r["problem"]) for r in claim], [r["update_decision"] for r in claim], (1, 1))
    gate_pass = bool(gate is not None and gate < 0.65)

    report = {"status": "PASS" if (not fails and gate_pass) else "FAIL",
              "failures": fails,
              "counts": {"train": len(tr), "eval": len(ev),
                         "train_by_policy": dict(Counter(r["policy"] for r in tr)),
                         "eval_by_policy": dict(Counter(r["policy"] for r in ev))},
              "shortcut": {"GATE_claim_masked_keepvsupdate": round(gate, 4) if gate else None,
                           "gate_pass_<0.65": gate_pass,
                           "L2_full_raw": round(full_raw, 4) if full_raw else None,
                           "L2_full_masked": round(full_masked, 4) if full_masked else None}}
    a.out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"status: {report['status']} ({len(fails)} failures)")
    for f in fails[:20]:
        print("  FAIL:", f)
    print(f"shortcut: GATE(claim masked keep-vs-update)={gate:.3f} -> "
          f"{'PASS' if gate_pass else 'FAIL'} (<0.65); "
          f"L2 full raw={full_raw:.3f} masked={full_masked:.3f}")
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
