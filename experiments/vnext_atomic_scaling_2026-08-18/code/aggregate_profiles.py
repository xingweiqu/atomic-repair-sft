#!/usr/bin/env python3
"""Aggregate multi-model base profiles (C-48 Phase B).
Reads /mnt/hdfs/xwqu/vnext0818/profiles/<tag>/{score_summary.json,loss.jsonl}
Writes MULTIMODEL_ATOMIC_PROFILE.{csv,json} + fig_multimodel_profile.pdf (score/loss panels)
+ LOSS_SCORE_ALIGNMENT.csv (per axis: behavioral score vs mean NLL/margin per model).
Usage: aggregate_profiles.py <profiles_dir> <out_dir>
"""
import json, sys, csv, pathlib, statistics as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PD, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

SCORE_AXES = [
    ("Original", lambda s: s["original"]["acc_exact"]),
    ("Paraphrase", lambda s: s["paraphrase"]["acc_exact"]),
    ("Distractor", lambda s: s["distractor"]["acc_exact"]),
    ("WC decision", lambda s: s["wc_attempt"]["decision_acc"]),
    ("CC keep", lambda s: s["cc_attempt"]["joint"]),
    ("Insuf stop", lambda s: s["insufficient"]["insufficient_stop"]),
    ("Format contract", lambda s: s["format"]["contract_exact"]),
]
LOSS_AXES = [
    ("L_gold orig", "original", "nll_gold_per_tok"),
    ("dL para", "paraphrase", None),
    ("dL distractor", "distractor", None),
    ("M dec WC", "wc_attempt", "margin_decision"),
    ("M dec CC", "cc_attempt", "margin_decision"),
    ("M status insuf", "insuf_ctr", "margin_status"),
    ("L contract fmt", "format", "nll_contract_tokens"),
]

profiles = {}
for d in sorted(PD.iterdir()):
    tag = d.name
    ss, lf = d / "score_summary.json", d / "loss.jsonl"
    if not ss.exists() or not lf.exists():
        continue
    s = json.load(open(ss))
    loss_rows = [json.loads(l) for l in open(lf)]
    bycond = {}
    for r in loss_rows:
        bycond.setdefault(r["condition"], []).append(r)
    orig_by_fam = {r["family_id"]: r.get("nll_gold") for r in bycond.get("original", [])}
    def mean_field(cond, f):
        vals = [r[f] for r in bycond.get(cond, []) if f in r]
        return st.mean(vals) if vals else None
    def mean_delta(cond):
        vals = [r["nll_gold"] - orig_by_fam[r["family_id"]]
                for r in bycond.get(cond, [])
                if "nll_gold" in r and orig_by_fam.get(r["family_id"]) is not None]
        return st.mean(vals) if vals else None
    prof = {"scores": {}, "losses": {}}
    for name, fn in SCORE_AXES:
        try: prof["scores"][name] = round(fn(s), 4)
        except Exception: prof["scores"][name] = None
    for name, cond, f in LOSS_AXES:
        v = mean_delta(cond) if f is None else mean_field(cond, f)
        prof["losses"][name] = round(v, 4) if v is not None else None
    prof["clean_loss_per_tok"] = round(mean_field("original", "nll_gold_per_tok") or -1, 4)
    prof["margin_flip_rates"] = {}
    for cond in ("wc_attempt", "cc_attempt", "insuf_ctr"):
        key = "margin_decision" if cond.startswith(("wc", "cc")) else "margin_status"
        vals = [r[key] for r in bycond.get(cond, []) if key in r]
        if vals:
            prof["margin_flip_rates"][cond] = round(sum(1 for v in vals if v < 0) / len(vals), 4)
    profiles[tag] = prof

json.dump(profiles, open(OUT / "MULTIMODEL_ATOMIC_PROFILE.json", "w"), indent=1)
with open(OUT / "MULTIMODEL_ATOMIC_PROFILE.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["model"] + [a for a, _ in SCORE_AXES] + [a for a, _, _ in LOSS_AXES] + ["clean_loss_per_tok"])
    for tag, p in profiles.items():
        w.writerow([tag] + [p["scores"][a] for a, _ in SCORE_AXES]
                   + [p["losses"][a] for a, _, _ in LOSS_AXES] + [p["clean_loss_per_tok"]])

# LOSS_SCORE_ALIGNMENT.csv: axis-level (score, loss/margin) pairs across models
with open(OUT / "LOSS_SCORE_ALIGNMENT.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["model", "axis", "behavioral_score", "loss_or_margin", "kind"])
    pairing = [("Distractor", "dL distractor", "deltaL"), ("Paraphrase", "dL para", "deltaL"),
               ("WC decision", "M dec WC", "margin"), ("CC keep", "M dec CC", "margin"),
               ("Insuf stop", "M status insuf", "margin"), ("Format contract", "L contract fmt", "nll"),
               ("Original", "L_gold orig", "nll")]
    for tag, p in profiles.items():
        for sa, la, kind in pairing:
            w.writerow([tag, sa, p["scores"].get(sa), p["losses"].get(la), kind])

tags = list(profiles)
if tags:
    fig, axs = plt.subplots(1, 2, figsize=(13, 0.6 * len(tags) + 2.2))
    Ms = np.array([[profiles[t]["scores"][a] if profiles[t]["scores"][a] is not None else np.nan
                    for a, _ in SCORE_AXES] for t in tags], dtype=float)
    im0 = axs[0].imshow(Ms, vmin=0, vmax=1, cmap="YlGnBu", aspect="auto")
    axs[0].set_title("behavioral score"); plt.colorbar(im0, ax=axs[0], fraction=0.03)
    Ml = np.array([[profiles[t]["losses"][a] if profiles[t]["losses"][a] is not None else np.nan
                    for a, _, _ in LOSS_AXES] for t in tags], dtype=float)
    Mn = (Ml - np.nanmin(Ml, 0)) / (np.nanmax(Ml, 0) - np.nanmin(Ml, 0) + 1e-9)
    im1 = axs[1].imshow(Mn, cmap="RdBu_r", aspect="auto")
    axs[1].set_title("loss / margin (col-normalized; annot = raw)"); plt.colorbar(im1, ax=axs[1], fraction=0.03)
    for ax, M, cols, raw in [(axs[0], Ms, [a for a, _ in SCORE_AXES], Ms),
                             (axs[1], Mn, [a for a, _, _ in LOSS_AXES], Ml)]:
        ax.set_xticks(range(len(cols))); ax.set_xticklabels(cols, rotation=30, ha="right", fontsize=7)
        ax.set_yticks(range(len(tags))); ax.set_yticklabels(tags, fontsize=8)
        for i in range(len(tags)):
            for j in range(len(cols)):
                if not np.isnan(raw[i, j]):
                    ax.text(j, i, f"{raw[i,j]:.2f}", ha="center", va="center", fontsize=6)
    fig.tight_layout()
    fig.savefig(OUT / "fig_multimodel_profile.pdf", bbox_inches="tight")
print("AGG_DONE", len(tags), "models")
