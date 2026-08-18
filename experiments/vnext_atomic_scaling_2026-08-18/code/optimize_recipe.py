#!/usr/bin/env python3
"""C-48 Phase H: clean-no-drop constrained optimal prescription per model.

Hard constraints (never traded into the objective):
  1. predicted CleanScore(n) >= base CleanScore      (strict; also noise-band variant)
  2. predicted CleanLoss(n)  <= base CleanLoss       (via lambda-scaled proxy when loss law absent)
  3. predicted false-abstain <= .10                  (ANS damage law)
Budget: sum(n_i) + n_clean = 2000, n_clean free (>=0).
Objectives: Opt-Loss = weighted normalized atomic deficit reduction (loss/margin-side proxy
via score-side laws tonight, declared); Opt-U = R-branch utility aggregate of predicted endpoints.
Composition terms: Qwen carrier/diversity corrections applied as FIXED development-family
terms (G): diversity premium requires all-cells>=50 & total>=600 (from INTERACTION_CORRECTION).
Usage: optimize_recipe.py <fits.json> <adapt.json> <collected.json> <out.json>
"""
import json, sys, itertools
import numpy as np

FITS = json.load(open(sys.argv[1]))
AD = json.load(open(sys.argv[2]))["models"]
COLL = json.load(open(sys.argv[3]))
OUTP = sys.argv[4]

FORM_FN = {
    "satexp": lambda n, p: p[0] * (1 - np.exp(-n / max(p[1], 1e-3))),
    "spower": lambda n, p: p[0] - p[1] * np.power(n + max(p[2], 1e-3), -abs(p[3])),
    "hill": lambda n, p: p[0] * np.power(n, p[1]) / (np.power(n, p[1]) + np.power(max(p[2], 1e-3), p[1]) + 1e-12),
    "loglin": lambda n, p: p[0] + p[1] * np.log1p(n),
    "dblexp": lambda n, p: p[0] * (1 - np.exp(-n / max(p[1], 1e-3))) - p[2] * (1 - np.exp(-n / max(p[3], 1e-3))),
}
def shape(ep, n):
    if n <= 0: return 0.0
    e = FITS[ep]; fn = FORM_FN[e["best_form"]]
    return float(fn(np.array([float(n)]), e["forms"][e["best_form"]]["params"])[0])

EP = {"FMT": ("FMT.contract", "fmt_contract"), "EVD": ("EVD.distractor", "dist"),
      "REV": ("REV.fix", "wc_joint"), "ANS": ("ANS.gain_insuf", "insuf_stop")}
REPAIRS = ["FMT", "EVD", "REV", "ANS", "PARA"]
GRID = [0, 30, 60, 120, 240, 480, 960]
NOISE = 0.012  # 3-seed placebo sd on original acc (anchor grids)

runs, profs = COLL["runs"], COLL["profiles"]
def placebo(m, key):
    for rep in REPAIRS:
        r = runs.get(f"{m}_{rep}-0000")
        if r and r.get(key) is not None: return r[key]
    return profs.get(m, {}).get(key)

out = {}
for m, ad in AD.items():
    a1 = ad["a_M1"]
    lam = ad.get("lambda_M3") or 0.0
    base_clean = placebo(m, "orig")
    base_eps = {r: placebo(m, EP[r][1]) for r in EP}
    base_fa = placebo(m, "suff_fa") or 0.0
    if base_clean is None: continue
    def predict(nvec):
        gains, clean_delta = {}, 0.0
        for r, n in zip(REPAIRS, nvec):
            if n == 0 or r == "PARA" or r not in a1: continue
            gains[r] = a1[r] * shape(EP[r][0], n)
            ck = f"{r}.clean"
            if ck in FITS: clean_delta += lam * shape(ck, n)
        fa = base_fa + (a1.get("ANS", 1.0) * shape("ANS.damage_fa", nvec[REPAIRS.index("ANS")])
                        if nvec[REPAIRS.index("ANS")] > 0 else 0.0)
        total = sum(nvec)
        # fixed development-family diversity term (single-domain tonight: applies only via total dose on >=3 active repairs proxy; declared coarse)
        active = sum(1 for n in nvec if n > 0)
        div = 0.02 if (total >= 600 and active >= 4) else 0.0
        return gains, clean_delta, fa, div
    best = {"strict": None, "noise_band": None}
    for nvec in itertools.product(GRID, repeat=len(REPAIRS)):
        total = sum(nvec)
        if total > 1400: continue  # n_clean >= 600 implicit floor removed: allow up to 2000
        gains, cdelta, fa, div = predict(nvec)
        clean_pred = base_clean + cdelta
        if fa > 0.10: continue
        # Opt-U (R-branch): mean of predicted target endpoints (capped at 1) + div
        vals = []
        for r in EP:
            b = base_eps[r] or 0.0
            vals.append(min(1.0, b + gains.get(r, 0.0)))
        U = float(np.mean(vals)) + div
        # Opt-Loss proxy: normalized deficit reduction
        L = sum((gains.get(r, 0.0)) / max(1e-6, 1 - (base_eps[r] or 0)) for r in EP) + div
        for mode, ok in [("strict", clean_pred >= base_clean), ("noise_band", clean_pred >= base_clean - NOISE)]:
            if not ok: continue
            cur = best[mode]
            if cur is None or U > cur["pred_U"]:
                best[mode] = {"recipe": dict(zip(REPAIRS, nvec)), "n_clean": 2000 - total,
                              "pred_U": round(U, 4), "pred_optloss": round(L, 4),
                              "pred_clean_score": round(clean_pred, 4), "pred_fa": round(fa, 4),
                              "pred_gains": {k: round(v, 4) for k, v in gains.items()}}
    out[m] = {"base_clean": round(base_clean, 4), "solutions": best,
              "objectives_note": "Opt-U = R-branch endpoint mean tonight; Opt-Loss = normalized-deficit proxy; clean-loss constraint enforced via lambda clean-score proxy (loss-law absent for anchor ckpts) — declared",
              "lambda": lam}
json.dump(out, open(OUTP, "w"), indent=1)
print("OPT_DONE", len(out), "models")
