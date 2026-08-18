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

FORMS = {
    "satexp": (f_satexp, [0.3, 100.0]),
    "spower": (f_spower, [0.3, 0.3, 10.0, 0.5]),
    "hill": (f_hill, [0.3, 1.0, 200.0]),
    "loglin": (f_loglin, [0.0, 0.05]),
    "dblexp": (f_dblexp, [0.3, 100.0, 0.3, 800.0]),
}

def fit_form(fn, p0, x, y):
    try:
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
    for name in cand:
        fn, p0 = FORMS[name]
        errs, dirok = [], []
        for i in range(len(doses)):
            if doses[i] == 0: continue
            mask = np.ones(len(doses), bool); mask[i] = False
            p, _ = fit_form(fn, p0, doses[mask], g[mask])
            if p is None: errs.append(math.inf); continue
            pred = float(fn(np.array([doses[i]]), *p)[0])
            errs.append(abs(pred - g[i]))
            dirok.append((pred > 0) == (g[i] > 0) if abs(g[i]) > .005 else True)
        full_p, full_mae = fit_form(fn, p0, doses, g)
        lodo[name] = {"lodo_mae": round(float(np.mean(errs)), 5) if errs else None,
                      "dir_acc": round(float(np.mean(dirok)), 3) if dirok else None,
                      "fit_mae": round(full_mae, 5),
                      "params": [round(float(v), 5) for v in full_p] if full_p is not None else None}
    best = min((v["lodo_mae"], k) for k, v in lodo.items() if v["lodo_mae"] is not None)[1]
    # noise band from multi-seed doses
    seeds_sd = [np.std(vs) for _, _, vs in ser if len(vs) > 1]
    results[f"{rep}.{ep}"] = {"doses": doses.tolist(), "gain": [round(float(v), 5) for v in g],
                              "base": round(float(base), 5), "forms": lodo, "best_form": best,
                              "seed_sd_mean": round(float(np.mean(seeds_sd)), 5) if seeds_sd else None}
    for i in range(len(doses)):
        if doses[i] == 0: continue
        fn, p0 = FORMS[best]
        mask = np.ones(len(doses), bool); mask[i] = False
        p, _ = fit_form(fn, p0, doses[mask], g[mask])
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
