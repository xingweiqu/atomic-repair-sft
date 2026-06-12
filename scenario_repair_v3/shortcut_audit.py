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
import generate_repair_data as v0
import reasoning_world_v2 as R
from scenario_repair_v3 import policies as P


def _entity_vocab():
    """All entity surface strings in the synthetic world, for masking."""
    ents = set()
    for fam in v0.FAMILY_NAMES:
        g = v0.build_family_graph(fam)
        for e in g["edges"]:
            ents.update([e["head"], e["bridge"], e["tail"]])
    for op in R.OPERATIONS:
        ents.add(op)
    # split multiword entities into tokens too (so "Maria Voss" -> mask both)
    toks = set()
    for e in ents:
        toks.add(e)
        for t in str(e).split():
            if len(t) > 2:
                toks.add(t)
    return sorted(toks, key=len, reverse=True)  # longest-first for replacement


_ENT = _entity_vocab()
import re as _re
_ENT_RE = _re.compile(r"\b(" + "|".join(_re.escape(e) for e in _ENT) + r")\b", _re.IGNORECASE)


def mask_entities(text: str) -> str:
    """Replace every world entity (and numbers) with a placeholder, so the classifier
    cannot route by entity identity — only by structural/template surface."""
    t = _ENT_RE.sub("ENT", text or "")
    t = _re.sub(r"\b-?\d+\b", "NUM", t)
    return t

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


def _bow_cv(texts, y, ngram):
    vec = TfidfVectorizer(lowercase=True, ngram_range=ngram, min_df=2)
    Xv = vec.fit_transform(texts)
    y = np.array(y)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
    accs = []
    for tr, te in skf.split(Xv, y):
        clf = LogisticRegression(max_iter=2000, C=4.0)
        clf.fit(Xv[tr], y[tr])
        accs.append(balanced_accuracy_score(y[te], clf.predict(Xv[te])))
    return float(np.mean(accs)), float(np.std(accs))


def bow_audit(rows):
    sub = [r for r in rows if r.get("problem")]
    X = [r["problem"] for r in sub]
    Xm = [mask_entities(r["problem"]) for r in sub]
    y = [r["update_decision"] for r in sub]

    # ---- The HARD GATE (Layer 1) ----
    # The decisive question is whether KEEP-vs-UPDATE *within the same domain and question
    # type* (i.e. Corrupt-family items: a planted claim that is true [keep] vs false
    # [update]) can be predicted from surface text AFTER masking entities. If yes, the
    # verification decision is a template/marker shortcut. If ~random, the model must
    # actually compare (head, claimed value) -- the capability we want. Cross-domain
    # vocabulary differences (R 'compute' vs K/H 'author') are legitimate task structure,
    # NOT a shortcut, so they are excluded from the gate and reported as Layer 2.
    corr = [r for r in sub if r["failure_type"].startswith(("K-Cor", "H-Cor"))]
    Xc = [mask_entities(r["problem"]) for r in corr]
    yc = [r["update_decision"] for r in corr]
    gate_acc, gate_s = (_bow_cv(Xc, yc, (1, 1)) if len(set(yc)) > 1 else (None, None))

    # ---- Disclosed (Layer 2), no gate ----
    uni_raw, uni_raw_s = _bow_cv(X, y, (1, 1))
    uni_mask, uni_mask_s = _bow_cv(Xm, y, (1, 1))
    bi_raw, bi_raw_s = _bow_cv(X, y, (1, 2))
    return {
        "n": len(X), "n_corrupt": len(corr),
        "GATE_keepvsupdate_masked_corrupt": (round(gate_acc, 4) if gate_acc else None,
                                             round(gate_s, 4) if gate_s else None),
        "L2_full_unigram_raw": (round(uni_raw, 4), round(uni_raw_s, 4)),
        "L2_full_unigram_masked": (round(uni_mask, 4), round(uni_mask_s, 4)),
        "L2_full_bigram_joint_raw": (round(bi_raw, 4), round(bi_raw_s, 4)),
    }


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
        b = bow_audit(rows)
        ind = marker_independence(rows)
        gate = b["GATE_keepvsupdate_masked_corrupt"][0]
        gate_pass = bool(gate is not None and gate < 0.65)
        report[d] = {"n": b["n"], "n_corrupt": b["n_corrupt"],
                     "GATE_keepvsupdate_masked_corrupt": b["GATE_keepvsupdate_masked_corrupt"],
                     "gate_pass_<0.65": gate_pass,
                     "L2_disclosed": {"full_unigram_raw": b["L2_full_unigram_raw"],
                                      "full_unigram_masked": b["L2_full_unigram_masked"],
                                      "full_bigram_joint_raw": b["L2_full_bigram_joint_raw"]},
                     "marker_independence": {k: (bool(v) if isinstance(v, (bool, np.bool_)) else v)
                                             for k, v in ind.items()}}
        print(f"{d}: (n={b['n']}, corrupt={b['n_corrupt']})")
        print(f"  GATE keep-vs-update, masked, Corrupt-family = "
              f"{gate if gate else 'n/a'} -> {'PASS' if gate_pass else 'FAIL'} (<0.65)  [decisive]")
        print(f"  L2 full unigram raw={b['L2_full_unigram_raw'][0]} masked={b['L2_full_unigram_masked'][0]} "
              f"bigram={b['L2_full_bigram_joint_raw'][0]}  (disclosed: incl. cross-domain structure + knowledge)")
        print(f"  marker indep: chi2={ind['chi2']} p={ind['p_value']}")
    if a.out:
        a.out.write_text(json.dumps(report, indent=2, default=str))
        print("wrote", a.out)
    return report


if __name__ == "__main__":
    main()
