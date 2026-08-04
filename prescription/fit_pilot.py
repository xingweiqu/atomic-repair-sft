#!/usr/bin/env python3
"""Zero-compute fitting pilot (C-18 v1.2 blueprint step 1): can a small form
library fit archived dose grids and blindly predict a held-out dose?

Frozen BEFORE running (this file is the prereg):
- curves + held-out points (interior, one per curve, chosen a priori);
- form library (primary, from blueprint): sat-exp / step / null;
  exploratory (flagged, non-primary): linear / log-quadratic (peak);
- fit = Huber loss (delta=.05), dense grid + L-BFGS-B refine, multi-init;
- report fit error (train Huber) and blind held-out |error| SEPARATELY.

Sources (iron rule 0):
- format REd_format, drills W_adopt: loop3/eval/batch1_scores.json (e4, s42)
- drills repair keep acc: loop3/eval/genre_scores.json
- datasize targeted resist@ridge: notes/NOTES_datasize.md table (tier-2: notes
  table, original eval jsons on server; declared, not reconstructed)
- keep-ratio resist@ridge: notes/NOTES_e1b.md (same tier-2 caveat)
Noise scale references (multi-seed spreads): datasize@300 .63-.76 (13pp),
keep@33 .60-.76 (16pp).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

B = {r["arm"]: r for r in json.loads((ROOT / "loop3/eval/batch1_scores.json").read_text())}
G = json.loads((ROOT / "loop3/eval/genre_scores.json").read_text())

CURVES = {
    "format_rescue": dict(
        x=[0, 10, 20, 36],
        y=[B[k]["REd_format"] for k in ("cleanreplay_s42_e4", "fmt10_s42_e4",
                                        "fmt20_s42_e4", "fmt36_s42_e4")],
        holdout=20, noise=None),
    "drills_adopt": dict(
        x=[0, 10, 25, 100],
        y=[B[k]["W_adopt"] for k in ("cleanreplay_s42_e4", "drl10_s42_e4",
                                     "drl25_s42_e4", "single_drills_s42_e4")],
        holdout=25, noise=None),
    "drills_keep": dict(
        x=[0, 10, 25, 100],
        y=[G[k]["per_policy"]["keep_answer"]["acc"] for k in
           ("cleanreplay_s42_e4", "drl10_s42_e4", "drl25_s42_e4", "single_drills_s42_e4")],
        holdout=25, noise=None),
    # notes/NOTES_datasize.md, targeted s42 resist@ridge (300 spread .63-.76)
    "datasize_resist": dict(x=[100, 300, 1000, 3000], y=[.60, .76, .83, .69],
                            holdout=1000, noise=.13),
    # notes/NOTES_e1b.md, keep-ratio resist@ridge s42 (33 spread .60-.76)
    "keep_resist": dict(x=[0, 15, 33, 100], y=[1.00, .90, .76, .33],
                        holdout=33, noise=.16),
}


def huber(res, d=.05):
    a = np.abs(res)
    return np.sum(np.where(a <= d, .5 * res ** 2, d * (a - .5 * d)))


FORMS = {
    # primary library (blueprint)
    "satexp": (3, lambda p, x: p[0] + p[1] * (1 - np.exp(-np.maximum(x, 0) / max(p[2], 1e-6)))),
    "step":   (3, lambda p, x: p[0] + p[1] * (x >= p[2])),
    "null":   (1, lambda p, x: p[0] + 0 * x),
    # exploratory (non-primary, flagged in report)
    "linear": (2, lambda p, x: p[0] + p[1] * x),
    "logquad": (3, lambda p, x: p[0] + p[1] * np.log1p(x) + p[2] * np.log1p(x) ** 2),
}
PRIMARY = ("satexp", "step", "null")


def fit(form, x, y):
    k, f = FORMS[form]
    x, y = np.asarray(x, float), np.asarray(y, float)
    lo, hi = y.min(), y.max()
    xm = x.max()
    inits = []
    for c0 in (lo, y[0], np.mean(y)):
        for a0 in (hi - lo, lo - hi, 0.1):
            for t0 in (xm * .1, xm * .3, xm * .7):
                inits.append([c0, a0, t0][:k])
    if form == "step":  # theta on a dense grid, others by L-BFGS
        best = None
        for th in np.linspace(x.min() + 1e-3, xm, 400):
            for c0, a0 in [(lo, hi - lo), (hi, lo - hi), (np.mean(y), 0)]:
                r = minimize(lambda p: huber(f([p[0], p[1], th], x) - y),
                             [c0, a0], method="L-BFGS-B")
                cand = (huber(f([*r.x, th], x) - y), [*r.x, th])
                if best is None or cand[0] < best[0]:
                    best = cand
        return best[1], best[0]
    best = None
    for p0 in inits:
        r = minimize(lambda p: huber(f(p, x) - y), p0, method="L-BFGS-B")
        if best is None or r.fun < best[0]:
            best = (r.fun, list(r.x))
    return best[1], best[0]


def main():
    out = {}
    for cname, c in CURVES.items():
        x, y, ho = c["x"], c["y"], c["holdout"]
        i = x.index(ho)
        xtr = [v for j, v in enumerate(x) if j != i]
        ytr = [v for j, v in enumerate(y) if j != i]
        rows = {}
        for form in FORMS:
            p, tr_loss = fit(form, xtr, ytr)
            pred = float(FORMS[form][1](p, np.asarray([ho], float))[0])
            rows[form] = dict(
                train_huber=round(float(tr_loss), 5),
                pred=round(pred, 4), obs=y[i],
                blind_abs_err=round(abs(pred - y[i]), 4),
                params=[round(float(v), 4) for v in p],
                primary=form in PRIMARY)
        # model pick among primary forms by train loss (small-n; ties -> fewer params)
        pick = min(PRIMARY, key=lambda f: (round(rows[f]["train_huber"], 6), FORMS[f][0]))
        out[cname] = dict(points=dict(zip(map(str, x), [round(v, 4) for v in y])),
                          holdout=ho, noise_ref=c["noise"], forms=rows,
                          primary_pick=pick,
                          pick_blind_err=rows[pick]["blind_abs_err"])
    (ROOT / "prescription/fit_pilot_results.json").write_text(json.dumps(out, indent=1))
    for cn, r in out.items():
        print(f"{cn:18} pick={r['primary_pick']:7} blind|err|={r['pick_blind_err']:.3f} "
              f"(noise_ref={r['noise_ref']}) obs={r['forms'][r['primary_pick']]['obs']:.3f} "
              f"pred={r['forms'][r['primary_pick']]['pred']:.3f}")


if __name__ == "__main__":
    main()
