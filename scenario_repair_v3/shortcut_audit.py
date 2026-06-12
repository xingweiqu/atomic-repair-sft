"""Shortcut audit (v3.1 hard acceptance gate).

Question: can the surface TEXT of `problem` predict `update_decision` without any
fact-checking? If yes, the data has a template shortcut and the "verification capability"
is partly template routing. We fit a TF-IDF + logistic-regression classifier to predict
update_decision from problem text, report 5-fold balanced accuracy, and compare old vs new
data. Acceptance: new data balanced accuracy < 0.65 (old is expected near 1.0).

Also runs a chi-square test that the presence of a hedging marker is INDEPENDENT of whether
the planted claim is false (it must be, after the Cor-True fix).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import balanced_accuracy_score
from scipy.stats import chi2_contingency

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scenario_repair_v3 import policies as P

MARKERS = ["some notes say", "some sources say", "i read somewhere", "according to my notes",
           "apparently", "a source i saw", "i was told", "my notes indicate", "it says here",
           "reportedly", "someone mentioned"]


def load(d):
    rows = []
    for fn in ("repair_train.jsonl", "repair_eval.jsonl"):
        p = Path(d) / fn
        if p.exists():
            rows += [json.loads(l) for l in p.open() if l.strip()]
    return rows


def bow_audit(rows):
    X = [r["problem"] or "" for r in rows if r.get("problem")]
    y = [r["update_decision"] for r in rows if r.get("problem")]
    vec = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=2)
    Xv = vec.fit_transform(X)
    y = np.array(y)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
    accs = []
    for tr, te in skf.split(Xv, y):
        clf = LogisticRegression(max_iter=2000, C=4.0)
        clf.fit(Xv[tr], y[tr])
        accs.append(balanced_accuracy_score(y[te], clf.predict(Xv[te])))
    return float(np.mean(accs)), float(np.std(accs)), len(X)


def marker_independence(rows):
    # only over Corrupt-derived items that carry a claim (have a marker or are Cor*)
    corr = [r for r in rows if r["failure_type"].startswith(("K-Cor", "H-Cor"))]
    has_marker = lambda p: any(m in (p or "").lower() for m in MARKERS)
    a = sum(1 for r in corr if has_marker(r["problem"]) and r.get("planted_wrong_answer") is not None)  # marker & false
    b = sum(1 for r in corr if has_marker(r["problem"]) and r.get("planted_wrong_answer") is None)       # marker & true
    c = sum(1 for r in corr if not has_marker(r["problem"]) and r.get("planted_wrong_answer") is not None)
    d = sum(1 for r in corr if not has_marker(r["problem"]) and r.get("planted_wrong_answer") is None)
    table = [[a, b], [c, d]]
    try:
        chi2, p, _, _ = chi2_contingency(table)
    except Exception:
        chi2, p = float("nan"), float("nan")
    return {"table_[marker_false,marker_true,nomarker_false,nomarker_true]": [a, b, c, d],
            "chi2": round(chi2, 3), "p_value": round(p, 4),
            "independent (p>0.05 desired)": p > 0.05 if p == p else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dirs", nargs="+", default=["data_v3", "data_v3_1"])
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    report = {}
    for d in a.data_dirs:
        rows = load(d)
        if not rows:
            print(f"{d}: (no data)"); continue
        acc, std, n = bow_audit(rows)
        ind = marker_independence(rows)
        report[d] = {"n": n, "bow_balanced_acc": round(acc, 4), "bow_std": round(std, 4),
                     "pass_<0.65": acc < 0.65, "marker_independence": ind}
        print(f"{d}: BoW balanced acc = {acc:.3f} ± {std:.3f} (n={n}) "
              f"-> {'PASS' if acc < 0.65 else 'FAIL'} (<0.65)")
        print(f"    marker-vs-falsity chi2={ind['chi2']} p={ind['p_value']} "
              f"independent={ind['independent (p>0.05 desired)']}")
    if a.out:
        a.out.write_text(json.dumps(report, indent=2))
        print("wrote", a.out)
    return report


if __name__ == "__main__":
    main()
