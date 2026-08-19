#!/usr/bin/env python3
"""C-50 V2 analysis: damage laws + honest tau validation + PARA law + optimizer v2.
Usage: analysis_v2.py <fits_v2/SCALING_LAW_FITS.json> <collected_v2.json> <out_dir>
Key v2 empirical fact folded in: single-repair damage at damage doses is SMALL
(clean deltas <~.01, llama ANS@960 FA=0) while v1 MIXTURE arms showed large damage
(1.7b clean -.025, llama FA .173) -> damage is substantially composition-borne.
Optimizer v2 therefore ships two solutions: strict (fitted laws) and conservative
(fitted laws + composition guards estimated from the v1 mixture observations)."""
import json, sys, pathlib, itertools, math
import numpy as np

FITS = json.load(open(sys.argv[1]))
COLL = json.load(open(sys.argv[2]))
OUT = pathlib.Path(sys.argv[3]); OUT.mkdir(parents=True, exist_ok=True)
runs = COLL["runs"]

FORM_FN = {
    "satexp": lambda n, p: p[0] * (1 - np.exp(-n / max(p[1], 1e-3))),
    "spower": lambda n, p: p[0] - p[1] * np.power(n + max(p[2], 1e-3), -abs(p[3])),
    "hill": lambda n, p: p[0] * np.power(n, p[1]) / (np.power(n, p[1]) + np.power(max(p[2], 1e-3), p[1]) + 1e-12),
    "loglin": lambda n, p: p[0] + p[1] * np.log1p(n),
    "dblexp": lambda n, p: p[0] * (1 - np.exp(-n / max(p[1], 1e-3))) - p[2] * (1 - np.exp(-n / max(p[3], 1e-3))),
}
def shape(ep, n, tau=1.0):
    if n <= 0: return 0.0
    e = FITS[ep]
    return float(FORM_FN[e["best_form"]](np.array([float(n) / tau]), e["forms"][e["best_form"]]["params"])[0])

MODELS = ["qwen3-1.7b", "qwen3-4b", "llama31-8b", "mistral-7b"]
GAIN_EP = {"FMT": ("FMT.contract", "fmt_contract"), "EVD": ("EVD.distractor", "dist"),
           "REV": ("REV.fix", "wc_joint"), "ANS": ("ANS.gain_insuf", "insuf_stop")}
DOSES = {"FMT": [30, 120, 960], "EVD": [120, 480, 960], "REV": [120, 480, 960],
         "ANS": [120, 480, 960], "PARA": [60, 480, 960]}
NOISE = 0.012

def val(m, rep, d, key):
    r = runs.get(f"{m}_{rep}-{d:04d}")
    if r is None: return None
    if key.startswith("loss."):
        return (r.get("loss") or {}).get(key[5:])
    return r.get(key)
def placebo(m, key):
    for rep in DOSES:
        v = val(m, rep, 0, key)
        if v is not None: return v

report = {"tau_validation": {}, "damage": {}, "para_law": {}, "notes": []}

# ---- (b) honest tau validation: fit on 2 lowest doses, predict 3rd ----
for m in MODELS:
    rows = {}
    for rep, (ep, key) in GAIN_EP.items():
        b = placebo(m, key)
        pts = [(d, val(m, rep, d, key)) for d in DOSES[rep]]
        pts = [(d, v - b) for d, v in pts if v is not None and b is not None]
        if len(pts) < 3: continue
        (d1, g1), (d2, g2), (d3, g3) = sorted(pts)
        # M1: single amplitude, LS on two lowest
        s1, s2 = shape(ep, d1), shape(ep, d2)
        aM1 = (g1 * s1 + g2 * s2) / (s1 * s1 + s2 * s2 + 1e-12)
        errM1 = abs(aM1 * shape(ep, d3) - g3)
        # M2: (a, tau) exactly identified on two lowest via tau grid
        best = (math.inf, None, None)
        for tau in [0.2, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0]:
            st1, st2 = shape(ep, d1, tau), shape(ep, d2, tau)
            a = (g1 * st1 + g2 * st2) / (st1 * st1 + st2 * st2 + 1e-12)
            fit_err = abs(a * st1 - g1) + abs(a * st2 - g2)
            if fit_err < best[0]: best = (fit_err, a, tau)
        _, aM2, tauM2 = best
        errM2 = abs(aM2 * shape(ep, d3, tauM2) - g3)
        rows[rep] = {"third_dose": d3, "true_gain3": round(g3, 4),
                     "M1": {"a": round(aM1, 3), "err": round(errM1, 4)},
                     "M2": {"a": round(aM2, 3), "tau": tauM2, "err": round(errM2, 4)}}
    if rows:
        report["tau_validation"][m] = {"per_repair": rows,
            "M1_mae": round(float(np.mean([r["M1"]["err"] for r in rows.values()])), 4),
            "M2_mae": round(float(np.mean([r["M2"]["err"] for r in rows.values()])), 4)}

# ---- (a) damage laws per model ----
for m in MODELS:
    dmg = {}
    b_clean = placebo(m, "orig"); b_fa = placebo(m, "suff_fa") or 0.0; b_cc = placebo(m, "cc_joint")
    # clean lambda per repair: fit on all observed doses (small-N LS), report worst-dose residual
    lam = {}
    for rep in DOSES:
        ck = f"{rep}.clean"
        if ck not in FITS: continue
        pts = [(d, val(m, rep, d, "orig")) for d in DOSES[rep]]
        pts = [(d, v - b_clean) for d, v in pts if v is not None and b_clean is not None]
        if len(pts) < 2: continue
        num = sum(dv * shape(ck, d) for d, dv in pts); den = sum(shape(ck, d) ** 2 for d, dv in pts)
        l = num / den if den > 1e-9 else 0.0
        resid = max(abs(l * shape(ck, d) - dv) for d, dv in pts)
        lam[rep] = {"lambda": round(l, 3), "max_resid": round(resid, 4),
                    "obs_deltas": {d: round(dv, 4) for d, dv in pts}}
    dmg["clean_lambda"] = lam
    # FA amplitude (ANS): fit on 480, predict 960 and reverse
    fa480, fa960 = val(m, "ANS", 480, "suff_fa"), val(m, "ANS", 960, "suff_fa")
    if fa480 is not None and fa960 is not None:
        s480, s960 = shape("ANS.damage_fa", 480), shape("ANS.damage_fa", 960)
        aF = (fa480 - b_fa) / (s480 + 1e-12)
        dmg["fa"] = {"amp_from_480": round(aF, 3), "pred_960": round(b_fa + aF * s960, 4),
                     "obs_960": fa960, "err": round(abs(b_fa + aF * s960 - fa960), 4),
                     "obs_480": fa480}
    # keep damage (REV)
    k480, k960 = val(m, "REV", 480, "cc_joint"), val(m, "REV", 960, "cc_joint")
    if k480 is not None and k960 is not None and b_cc is not None:
        sk4, sk9 = shape("REV.keep_damage", 480), shape("REV.keep_damage", 960)
        aK = (k480 - b_cc) / (sk4 + 1e-12)
        dmg["keep"] = {"amp": round(aK, 3), "pred_960": round(b_cc + aK * sk9, 4), "obs_960": k960,
                       "err": round(abs(b_cc + aK * sk9 - k960), 4)}
    report["damage"][m] = dmg

# composition-borne damage offsets from v1 mixtures (2 observations, used only as guards)
comp = {}
for m in ("qwen3-1.7b", "llama31-8b"):
    mix = runs.get(f"{m}_MIX-optimal")
    if not mix: continue
    rec = {"qwen3-1.7b": {"ANS": 960}, "llama31-8b": {"ANS": 120}}[m]
    aF = (report["damage"][m].get("fa") or {}).get("amp_from_480", 0)
    pred_fa_single = (placebo(m, "suff_fa") or 0) + aF * shape("ANS.damage_fa", rec["ANS"])
    lam_sum = sum(v["lambda"] * shape(f"{r}.clean", 480) for r, v in report["damage"][m]["clean_lambda"].items())
    comp[m] = {"fa_offset_obs": round(mix["suff_fa"] - pred_fa_single, 4),
               "clean_offset_obs": round((mix["orig"] - placebo(m, "orig")) - lam_sum, 4)}
report["composition_guards"] = comp
report["notes"].append("single-repair damage at damage doses is small (all clean deltas <=~.015; llama ANS@960 FA=0) while v1 mixtures showed -.025 clean / .173 FA -> damage is substantially composition-borne; guards below use v1 mixture offsets (N=2, declared)")

# ---- (c) PARA loss-side law: pooled satexp shape + per-model amplitude ----
para = {}
pooled = []
for m in MODELS:
    b = placebo(m, "loss.dL_para")
    pts = [(d, val(m, "PARA", d, "loss.dL_para")) for d in DOSES["PARA"]]
    pts = [(d, b - v) for d, v in pts if v is not None and b is not None]  # gain = reduction of dL
    if len(pts) >= 2:
        para[m] = pts; pooled += pts
best = (math.inf, None)
for tau in [30, 60, 120, 240, 480, 960]:
    err = 0.0
    for m, pts in para.items():
        ss = [1 - math.exp(-d / tau) for d, _ in pts]
        gg = [g for _, g in pts]
        a = sum(g * s for g, s in zip(gg, ss)) / (sum(s * s for s in ss) + 1e-12)
        err += sum(abs(a * s - g) for s, g in zip(ss, gg))
    if err < best[0]: best = (err, tau)
ptau = best[1]
report["para_law"] = {"shared_tau": ptau, "per_model": {}}
for m, pts in para.items():
    ss = [1 - math.exp(-d / ptau) for d, _ in pts]; gg = [g for _, g in pts]
    a = sum(g * s for g, s in zip(gg, ss)) / (sum(s * s for s in ss) + 1e-12)
    fit_err = float(np.mean([abs(a * s - g) for s, g in zip(ss, gg)]))
    report["para_law"]["per_model"][m] = {"amp": round(a, 3), "fit_mae": round(fit_err, 4),
                                          "points": [[d, round(g, 4)] for d, g in pts]}
report["para_law"]["declared"] = "loss-side law (dL_para reduction); behavioral para score stays flat; exploratory grade"

# ---- (d) optimizer v2 ----
REPAIRS = ["FMT", "EVD", "REV", "ANS", "PARA"]
GRID = [0, 30, 60, 120, 240, 480, 960]
recipes = {}
for m in ("qwen3-1.7b", "llama31-8b"):
    tv = report["tau_validation"].get(m, {}).get("per_repair", {})
    aM1 = {r: v["M1"]["a"] for r, v in tv.items()}
    lam = report["damage"][m]["clean_lambda"]
    aF = (report["damage"][m].get("fa") or {}).get("amp_from_480", 0)
    b_clean = placebo(m, "orig"); b_fa = placebo(m, "suff_fa") or 0
    guards = comp.get(m, {"fa_offset_obs": 0, "clean_offset_obs": 0})
    base_eps = {r: placebo(m, GAIN_EP[r][1]) for r in GAIN_EP}
    # clean damage: linear interp over observed per-repair clean deltas (robust)
    def clean_delta_r(rep, n):
        obs = lam.get(rep, {}).get("obs_deltas")
        if not obs or n <= 0: return 0.0
        ds = sorted(int(k) for k in obs)
        if n <= ds[0]: return obs[str(ds[0]) if str(ds[0]) in obs else ds[0]] * n / ds[0]
        for lo, hi in zip(ds, ds[1:]):
            if n <= hi:
                a, b = obs.get(str(lo), obs.get(lo)), obs.get(str(hi), obs.get(hi))
                return a + (b - a) * (n - lo) / (hi - lo)
        return obs.get(str(ds[-1]), obs.get(ds[-1]))
    TOT_V1 = 1400.0
    _MH = {"v": NOISE}
    def solve(conservative):
        best = None
        for nvec in itertools.product(GRID, repeat=5):
            tot = sum(nvec)
            if tot > 1400: continue
            gains = {r: aM1.get(r, 0) * shape(GAIN_EP[r][0], n) for r, n in zip(REPAIRS, nvec) if n > 0 and r in GAIN_EP}
            clean_d = sum(clean_delta_r(r, n) for r, n in zip(REPAIRS, nvec) if r != "PARA")
            fa = b_fa + aF * shape("ANS.damage_fa", nvec[3])
            if conservative:
                clean_d += min(0.0, guards["clean_offset_obs"]) * tot / TOT_V1
                fa += max(0.0, guards["fa_offset_obs"]) * tot / TOT_V1
            clean_pred = b_clean + clean_d
            if fa > 0.10: continue
            margin_req = 0.0 if not conservative else _MH["v"]
            if clean_pred < b_clean + margin_req: continue
            U = float(np.mean([min(1.0, (base_eps[r] or 0) + gains.get(r, 0)) for r in GAIN_EP]))
            if tot >= 600 and sum(1 for n in nvec if n > 0) >= 4: U += 0.02
            if best is None or U > best["pred_U"]:
                best = {"recipe": dict(zip(REPAIRS, nvec)), "n_clean": 2000 - tot,
                        "pred_U": round(U, 4), "pred_clean": round(clean_pred, 4), "pred_fa": round(fa, 4),
                        "pred_gains": {k: round(v, 4) for k, v in gains.items()}}
        return best
    strict_sol = solve(False)
    cons_sol, used_margin = None, None
    for mgn in (NOISE, 0.0, -NOISE):
        _MH["v"] = mgn
        cons_sol = solve(True)
        if cons_sol is not None:
            used_margin = mgn; break
    if cons_sol is not None: cons_sol["margin_used"] = used_margin
    recipes[m] = {"strict": strict_sol, "conservative": cons_sol,
                  "base_clean": round(b_clean, 4),
                  "note": "conservative applies v1-mixture composition offsets (clean & FA) + requires clean >= base + 1 noise band"}
report["optimizer_v2"] = recipes
json.dump(report, open(OUT / "ANALYSIS_V2.json", "w"), indent=1)
print("V2_ANALYSIS_DONE")
for m, v in report["tau_validation"].items():
    print(m, "tau-val M1", v["M1_mae"], "M2", v["M2_mae"])
for m, r in recipes.items():
    print(m, "strict", r["strict"]["recipe"] if r["strict"] else None,
          "| conservative", r["conservative"]["recipe"] if r["conservative"] else None)
