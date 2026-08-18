#!/usr/bin/env python3
"""C-48 Phase E: fit atomic repair scaling laws on the Qwen3-8B anchor grids
(existing frozen curves, read-only) with a frozen candidate form family + LODO CV.

Candidate forms (gain G(n), n = repair examples):
  satexp:  A*(1-exp(-n/tau))
  spower:  A - B*(n+n0)^(-alpha)
  hill:    A*n^a/(n^a+tau^a)
  loglin:  a + b*log(1+n)
  dblexp (harmful/non-monotone): A*(1-exp(-n/t1)) - B*(1-exp(-n/t2))
ANS fits Gain_insuff and Damage_false_abstain SEPARATELY.
Usage: fit_laws.py <freeze_dir> <out_dir>
"""
import json, sys, pathlib, itertools, math
import numpy as np
from scipy.optimize import curve_fit

FRZ, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

curves = json.load(open(FRZ / "curves_e500_all.json"))
ansf = json.load(open(FRZ / "curves_ans_formal_e500.json"))

def series(src, fam, path):
    import statistics as st
    by = {}
    for k, v in src.items():
        if not k.startswith(fam + "-"): continue
        dose = int(k.split("-")[1])
        x = v
        for p in path.split("."): x = x[p]
        by.setdefault(dose, []).append(x)
    return sorted((d, st.mean(vs), vs) for d, vs in by.items())

# endpoint definitions: (repair, endpoint_name, source, family, path, kind)
ENDPOINTS = [
    ("FMT", "contract", curves, "FMT", "format.contract_exact", "gain"),
    ("EVD", "distractor", curves, "EVD", "distractor.acc_exact", "gain"),
    ("REV", "fix", curves, "REV", "wc_attempt.joint", "harm_ok"),
    ("REV", "keep_damage", curves, "REV", "cc_attempt.joint", "harm_ok"),
    ("ANS", "gain_insuf", ansf, "ANS", "insufficient.insufficient_stop", "gain"),
    ("ANS", "damage_fa", ansf, "ANS", "suff_ctr.false_abstain", "gain"),
    ("FMT", "clean", curves, "FMT", "original.acc_exact", "harm_ok"),
    ("ANS", "clean", ansf, "ANS", "original.acc_exact", "harm_ok"),
    ("REV", "clean", curves, "REV", "original.acc_exact", "harm_ok"),
    ("EVD", "clean", curves, "EVD", "original.acc_exact", "harm_ok"),
]

def f_satexp(n, A, tau): return A * (1 - np.exp(-n / np.maximum(tau, 1e-3)))
def f_spower(n, A, B, n0, al): return A - B * np.power(n + np.maximum(n0, 1e-3), -np.abs(al))
def f_hill(n, A, a, tau): return A * np.power(n, a) / (np.power(n, a) + np.power(np.maximum(tau, 1e-3), a) + 1e-12)
def f_loglin(n, a, b): return a + b * np.log1p(n)
def f_dblexp(n, A, t1, B, t2): return A * (1 - np.exp(-n / np.maximum(t1, 1e-3))) - B * (1 - np.exp(-n / np.maximum(t2, 1e-3)))

# C-49: legal parameter regions enforced (A>=0 magnitudes, tau>0, alpha>0).
# Gain endpoints use monotone forms by construction under these bounds; harmful
# endpoints use the explicit benefit-damage double-exponential.
FORMS = {
    "satexp": (f_satexp, [0.3, 100.0], ([-1.0, 1.0], [1.0, 4000.0])),
    "spower": (f_spower, [0.3, 0.3, 10.0, 0.5], ([-1.0, 0.0, 1e-3, 0.05], [1.0, 2.0, 500.0, 3.0])),
    "hill": (f_hill, [0.3, 1.0, 200.0], ([-1.0, 0.05, 1.0], [1.0, 4.0, 4000.0])),
    "loglin": (f_loglin, [0.0, 0.05], ([-1.0, -0.5], [1.0, 0.5])),
    "dblexp": (f_dblexp, [0.3, 100.0, 0.3, 800.0], ([0.0, 1.0, 0.0, 1.0], [1.5, 4000.0, 1.5, 4000.0])),
}

def fit_form(fn, p0, x, y, bounds=None):
    try:
        if bounds is not None:
            p, _ = curve_fit(fn, x, y, p0=np.clip(p0, bounds[0], bounds[1]), bounds=bounds, maxfev=40000)
        else:
            p, _ = curve_fit(fn, x, y, p0=p0, maxfev=20000)
        return p, float(np.mean(np.abs(fn(x, *p) - y)))
    except Exception:
        return None, math.inf

results = {}
heldout_rows = []
for rep, ep, src, fam, path, kind in ENDPOINTS:
    ser = series(src, fam, path)
    if len(ser) < 4: continue
    doses = np.array([d for d, _, _ in ser], float)
    ys = np.array([m for _, m, _ in ser], float)
    base = ys[doses == 0][0] if (doses == 0).any() else ys[0]
    g = ys - base  # gain relative to placebo
    cand = ["satexp", "spower", "hill", "loglin"] + (["dblexp"] if kind == "harm_ok" else [])
    lodo = {}
    lowmask = doses <= 240
    for name in cand:
        fn, p0, bnd = FORMS[name]
        errs, dirok = [], []
        for i in range(len(doses)):
            if doses[i] == 0: continue
            mask = np.ones(len(doses), bool); mask[i] = False
            p, _ = fit_form(fn, p0, doses[mask], g[mask], bnd)
            if p is None: errs.append(math.inf); continue
            pred = float(fn(np.array([doses[i]]), *p)[0])
            errs.append(abs(pred - g[i]))
            dirok.append((pred > 0) == (g[i] > 0) if abs(g[i]) > .005 else True)
        full_p, full_mae = fit_form(fn, p0, doses, g, bnd)
        # C-49 extrapolation validation: fit on doses<=240, predict all higher doses
        ex = None
        if lowmask.sum() >= 3 and (~lowmask).sum() >= 1:
            pl, _ = fit_form(fn, p0, doses[lowmask], g[lowmask], bnd)
            if pl is not None:
                hi_d, hi_g = doses[~lowmask], g[~lowmask]
                preds = np.array([float(fn(np.array([d]), *pl)[0]) for d in hi_d])
                ex = {"extrap_mae": round(float(np.mean(np.abs(preds - hi_g))), 5),
                      "extrap_dir_acc": round(float(np.mean([(pv > 0) == (gv > 0) if abs(gv) > .005 else True
                                                             for pv, gv in zip(preds, hi_g)])), 3),
                      "extrap_points": [[int(d), round(float(gv), 5), round(float(pv), 5)]
                                        for d, gv, pv in zip(hi_d, hi_g, preds)]}
        lodo[name] = {"lodo_mae": round(float(np.mean(errs)), 5) if errs else None,
                      "dir_acc": round(float(np.mean(dirok)), 3) if dirok else None,
                      "fit_mae": round(full_mae, 5),
                      "params": [round(float(v), 5) for v in full_p] if full_p is not None else None,
                      "extrapolation": ex}
    best = min((v["lodo_mae"], k) for k, v in lodo.items() if v["lodo_mae"] is not None)[1]
    # noise band from multi-seed doses
    seeds_sd = [np.std(vs) for _, _, vs in ser if len(vs) > 1]
    results[f"{rep}.{ep}"] = {"doses": doses.tolist(), "gain": [round(float(v), 5) for v in g],
                              "base": round(float(base), 5), "forms": lodo, "best_form": best,
                              "seed_sd_mean": round(float(np.mean(seeds_sd)), 5) if seeds_sd else None}
    for i in range(len(doses)):
        if doses[i] == 0: continue
        fn, p0, bnd = FORMS[best]
        mask = np.ones(len(doses), bool); mask[i] = False
        p, _ = fit_form(fn, p0, doses[mask], g[mask], bnd)
        if p is not None:
            heldout_rows.append({"endpoint": f"{rep}.{ep}", "held_dose": int(doses[i]),
                                 "true_gain": round(float(g[i]), 5),
                                 "pred_gain": round(float(fn(np.array([doses[i]]), *p)[0]), 5),
                                 "form": best})

json.dump(results, open(OUT / "SCALING_LAW_FITS.json", "w"), indent=1)
import csv
with open(OUT / "heldout_dose_predictions.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["endpoint", "held_dose", "true_gain", "pred_gain", "form"])
    w.writeheader(); w.writerows(heldout_rows)
print("FIT_DONE", len(results), "endpoints;", len(heldout_rows), "heldout rows")
