#!/usr/bin/env python3
"""C-20 convergent-story figures (7): all from frozen data / existing fit results.
Zero new training or inference. Outputs report_pack/out/convergent/.
P placebo quad | V vector-response matrix | L law shapes (SCHEMATIC) |
K keep-dilution holdout | D shape comparison | N seed-noise ruler | R pipeline (SCHEMATIC)
"""
from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from figs.style import OKABE  # noqa: E402
import matplotlib as mpl  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

mpl.rcParams["font.sans-serif"] = ["DejaVu Sans", "PingFang SC", "Arial Unicode MS"]
OUT = ROOT / "report_pack/out/convergent"
OUT.mkdir(parents=True, exist_ok=True)

B = {r["arm"]: r for r in json.loads((ROOT / "loop3/eval/batch1_scores.json").read_text())}
G = json.loads((ROOT / "loop3/eval/genre_scores.json").read_text())
S = json.loads((ROOT / "prescription/p0c/p0c_scores.json").read_text())
FP = json.loads((ROOT / "prescription/fit_pilot_results.json").read_text())
IC = [c for c in S["BASE"] if "INSUFFICIENT" in c]


def abstain(tag):
    return st.mean(S[tag][c] for c in IC)


def save(fig, slug, meta):
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{slug}.{ext}", dpi=300)
    (OUT / f"{slug}.meta.md").write_text(meta)
    plt.close(fig)
    print("saved", slug)


FOOT = dict(fontsize=6, color="#555555")


def fig_p():
    fig, axes = plt.subplots(1, 4, figsize=(9.5, 2.6))
    a = axes[0]
    a.bar([0, 1], [G["pre-repair(base)"]["overall"], G["cleanreplay_s42_e4"]["overall"]],
          color=["#BBBBBB", OKABE["placebo"]])
    a.set_xticks([0, 1]); a.set_xticklabels(["base", "placebo"], fontsize=8)
    a.set_title("(a) repair-genre overall", fontsize=9)
    for i, v in enumerate([.3333, .575]):
        a.text(i, v + .01, f"{v:.3f}", ha="center", fontsize=8)
    a = axes[1]
    a.bar([0, 1], [B["cleanreplay_s42_e4"]["REd_conduct"],
                   B["single_conduct_s42_e8"]["REd_conduct"]],
          color=[OKABE["placebo"], OKABE["conduct"]])
    a.set_xticks([0, 1]); a.set_xticklabels(["placebo", "conduct\nspecialist"], fontsize=8)
    a.set_title("(b) conduct-bucket rescue", fontsize=9)
    for i, v in enumerate([.732, .746]):
        a.text(i, v + .01, f"{v:.3f}", ha="center", fontsize=8)
    a = axes[2]
    a.bar([0, 1], [.888, .464], color=["#BBBBBB", OKABE["placebo"]])
    a.set_xticks([0, 1]); a.set_xticklabels(["base", "placebo"], fontsize=8)
    a.set_title("(c) P1 keep rate", fontsize=9)
    for i, v in enumerate([.888, .464]):
        a.text(i, v + .01, f"{v:.3f}", ha="center", fontsize=8)
    a = axes[3]
    vals = [5, 40, 41, 41]
    a.bar(range(4), vals, color=["#BBBBBB", OKABE["format_"], OKABE["B"], OKABE["placebo"]])
    a.set_xticks(range(4))
    a.set_xticklabels(["base", "FMT10", "uniform", "placebo"], fontsize=7)
    a.set_title("(d) 2Wiki new fails on known items", fontsize=9)
    for i, v in enumerate(vals):
        a.text(i, v + 1, str(v), ha="center", fontsize=8)
    fig.suptitle("Plain clean data alone changes the model (placebo effects, 4 instruments)",
                 fontsize=10, y=1.04)
    fig.tight_layout()
    fig.text(.01, -.05, "Sources: (a) loop3/eval/genre_scores.json; (b) batch1_scores.json REd_conduct; "
             "(c) p0c preds re-derived (n=412 keep cells); (d) notes/NOTES_2wiki.md table "
             "(range across all trained arms 34-56). All single preregistered arms unless noted.",
             **FOOT)
    save(fig, "figP_placebo_quad",
         "# figP\nCaption: 无 placebo 校正的组件效应必被高估——定律必须拟 placebo-adjusted delta。\n"
         "Numbers: base .3333→placebo .575 (repair overall); conduct rescue placebo .732 vs specialist .746; "
         "P1 keep .888→.464; 2wiki fail_O base 5 → FMT10 40 / uniform 41 / placebo 41 (tier-2: NOTES_2wiki table).\n")


def fig_v():
    rows = ["format@10%", "drills@25%", "conduct (single)", "cleanreplay (vs base)"]
    cols = ["target bucket\n(Δ placebo)", "plain\nO_acc", "repair\nkeep", "abstain"]
    pl = dict(o=B["cleanreplay_s42_e4"]["O_acc"], k=G["cleanreplay_s42_e4"]["per_policy"]["keep_answer"]["acc"],
              a=abstain("l3_cleanreplay_s42_e4"))
    M = np.full((4, 4), np.nan)
    M[0] = [B["fmt10_s42_e4"]["REd_format"] - B["cleanreplay_s42_e4"]["REd_format"],
            B["fmt10_s42_e4"]["O_acc"] - pl["o"],
            G["fmt10_s42_e4"]["per_policy"]["keep_answer"]["acc"] - pl["k"],
            abstain("l3_fmt10_s42_e4") - pl["a"]]
    M[1] = [B["drl25_s42_e4"]["REd_conduct"] - B["cleanreplay_s42_e4"]["REd_conduct"],
            B["drl25_s42_e4"]["O_acc"] - pl["o"],
            G["drl25_s42_e4"]["per_policy"]["keep_answer"]["acc"] - pl["k"],
            abstain("l3_drl25_s42_e4") - pl["a"]]
    M[2] = [B["single_conduct_s42_e8"]["REd_conduct"] - B["cleanreplay_s42_e4"]["REd_conduct"],
            B["single_conduct_s42_e8"]["O_acc"] - pl["o"],
            G["single_conduct_s42_e8"]["per_policy"]["keep_answer"]["acc"] - pl["k"],
            abstain("l3_single_conduct_s42_e8") - pl["a"]]
    M[3] = [np.nan, np.nan,
            pl["k"] - G["pre-repair(base)"]["per_policy"]["keep_answer"]["acc"],
            pl["a"] - st.mean(S["BASE"][c] for c in IC)]
    fig, ax = plt.subplots(figsize=(7.4, 3.0))
    disp = np.where(np.isnan(M), 0, M)
    ax.imshow(np.where(np.isnan(M), np.nan, disp), cmap="RdYlGn", vmin=-.45, vmax=.45,
              aspect="auto")
    for i in range(4):
        for j in range(4):
            if np.isnan(M[i, j]):
                ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, color="#DDDDDD"))
                ax.text(j, i, "n/a", ha="center", va="center", fontsize=7, color="#888")
            else:
                ax.text(j, i, f"{M[i, j]:+.3f}", ha="center", va="center", fontsize=9,
                        fontweight="bold")
    ax.set_xticks(range(4)); ax.set_xticklabels(cols, fontsize=7.5)
    ax.set_yticks(range(4)); ax.set_yticklabels(rows, fontsize=8)
    ax.set_title("One dataset moves the whole 16-cell vector — response is a vector, not a scalar",
                 fontsize=9.5)
    fig.text(.01, -.06, "Component rows = Δ vs placebo (cleanreplay_s42_e4: O_acc .797, keep .481, abstain .062); "
             "bottom row = placebo Δ vs base (keep base .500, abstain base .463); base O_acc / target n/a in frozen json. "
             "Sources: batch1_scores / genre_scores / p0c_scores. Single seed arms (preregistered).", **FOOT)
    save(fig, "figV_vector_matrix",
         "# figV\nCaption: 同一份数据,一维正另一维负——响应是向量不是标量。\n"
         f"Matrix:\n{json.dumps(M.tolist())}\n")


def fig_l():
    fig, ax = plt.subplots(figsize=(5.4, 3.0))
    n = np.linspace(0, 3000, 300)

    def f(A, tau, al):
        return A * (1 - np.exp(-((n / tau) ** al)))

    ax.plot(n, f(.5, 400, 1.0), color=OKABE["B"], label="A>0 saturating gain")
    ax.plot(n, f(.02, 400, 1.0), color="#999999", label="A≈0 no effect")
    ax.plot(n, f(-.4, 800, 1.2), color=OKABE["drills"], label="A<0 progressive damage")
    ax.axhline(0, color="k", lw=.8)
    ax.set_xlabel("dose n (items)"); ax.set_ylabel("ΔS vs placebo")
    ax.legend(fontsize=7.5)
    ax.set_title("Hypothesis: ΔS = A·(1−e^{−(n/τ)^α})   —   SCHEMATIC", fontsize=9.5)
    ax.text(.985, .05, "A: asymptote (sign=direction)\nτ: dose scale\nα: shape (1=exp)",
            transform=ax.transAxes, ha="right", fontsize=7,
            bbox=dict(fc="white", ec="#999999", lw=.7))
    fig.text(.01, -.04, "SCHEMATIC (no data points). Form library also contains threshold/segmented "
             "forms, selected by model comparison (see figD).", **FOOT)
    save(fig, "figL_law_shapes", "# figL\nSCHEMATIC single-form three-curve hypothesis page.\n")


def fig_k():
    x = np.array([0, 15, 33, 100]); y = np.array([1.00, .90, .76, .33])
    p = FP["keep_resist"]["forms"]["satexp"]["params"]  # fit on {0,15,100}
    xs = np.linspace(0, 100, 200)
    ys = p[0] + p[1] * (1 - np.exp(-xs / p[2]))
    fig, ax = plt.subplots(figsize=(5.6, 3.0))
    tr = [0, 1, 3]
    ax.plot(xs, ys, color=OKABE["A1"], label="signed saturating fit on {0,15,100}")
    ax.plot(x[tr], y[tr], "o", mfc="none", color=OKABE["A1"], ms=7, label="train points")
    ax.plot([33], [.76], "s", color="k", ms=7, label="held-out obs .760")
    pred = FP["keep_resist"]["forms"]["satexp"]["pred"]
    ax.plot([33], [pred], "*", color=OKABE["drills"], ms=13,
            label=f"blind prediction {pred:.3f} (err +{(pred-.76)*100:.1f}pp)")
    ax.errorbar([33], [.68], yerr=[[.08], [.08]], fmt="none", ecolor="#999999",
                capsize=4, label="3-seed spread at 33% (.60–.76)")
    ax.axhline(.83, color="#666666", ls=":", lw=1.2)
    ax.text(2, .845, "floor reference .83 (scaffold_conv_e8, trained)", fontsize=7, color="#666666")
    ax.set_xlabel("keep-data ratio (%)"); ax.set_ylabel("resist @ ridge")
    ax.legend(fontsize=6.5, loc="lower left")
    ax.set_title("Verification protocol, damage direction: keep-dilution held-out", fontsize=9.5)
    fig.text(.01, -.14, "Data: notes/NOTES_e1b.md + NOTES_datasize.md (tier-2 notes tables; ridge points). "
             "Fit: prescription/fit_pilot.py (Huber+L-BFGS, frozen prereg).\n"
             "Fitted params in near-linear regime (A=-141.8, τ=21116 → ~linear over [0,100]). "
             "Single seed except 33% (3-seed spread shown).\n"
             "NOTE: instruction labeled the .83 line 'untrained baseline'; source labels it a TRAINED "
             "floor reference arm — drawn with source label.", **FOOT)
    save(fig, "figK_keep_holdout",
         "# figK\nCaption: 同一协议的损伤方向例:盲预测 .779 vs 实测 .760 (+1.9pp)。\n"
         "Independently recomputed from fit_pilot_results.json (matches).\n")


def fig_d():
    x = np.array([0, 10, 25, 100]); y = np.array([1.8, 1.5, 2.0, 24.6])  # % units, batch1 W_adopt
    f = FP["drills_adopt"]["forms"]
    xs = np.linspace(0, 100, 300)
    sp = f["satexp"]["params"]
    ysat = (sp[0] + sp[1] * (1 - np.exp(-xs / sp[2]))) * 100
    fig, ax = plt.subplots(figsize=(5.8, 3.0))
    ax.plot(x[[0, 1, 3]], y[[0, 1, 3]], "o", mfc="none", color="k", ms=7, label="train {0,10,100}")
    ax.plot([25], [2.0], "s", color="k", ms=7, label="held-out obs 2.0")
    ax.plot(xs, ysat, color=OKABE["C"], label=f"saturating: pred {f['satexp']['pred']*100:.1f} (+{(f['satexp']['pred']-.0198)*100:.1f}pp)")
    ax.axhline(f["null"]["params"][0] * 100, color="#999999", ls="--",
               label=f"flat/null: pred {f['null']['pred']*100:.1f} (+{(f['null']['pred']-.0198)*100:.1f}pp)")
    ax.fill_between([10, 100], 1.6, 24.6, color=OKABE["drills"], alpha=.12)
    ax.text(55, 13, "step form: θ censored in (10,100]\n→ honest output = interval [1.6, 24.6]\n"
            "(θ-bracketing grid required)", fontsize=7, color=OKABE["drills"], ha="center")
    ax.set_xlabel("drills dose (% items)"); ax.set_ylabel("plain W_adopt (%)")
    ax.legend(fontsize=6.5, loc="upper left")
    ax.set_title("Model comparison judges shape — and exposes censored thresholds", fontsize=9.5)
    fig.text(.01, -.05, "Data: loop3/eval/batch1_scores.json W_adopt {1.8, 1.5, 2.0, 24.6}% "
             "(instruction quoted {2,1.3,1.5,25} — data-file values drawn). Fits: fit_pilot_results.json "
             "(independently recomputed, match). Single preregistered arms.", **FOOT)
    save(fig, "figD_shape_comparison",
         "# figD\nCaption: 不预设全组件同形;形态由 held-out 预测优劣裁决。\n"
         "satexp pred 6.5 (+4.5pp) rejected; null pred 4.1 (+2.2pp) best at 25; step θ censored -> interval.\n")


def fig_n():
    labels = ["B arm overall (3s)", "A1 overall (3s)", "C overall (3s)", "abstain policy (3s)"]
    Bv = [G[k]["overall"] for k in ("B_s42_e2", "B_s43_e4", "B_s44_e2")]
    A1 = [G[k]["overall"] for k in ("A1_s42_e4", "A1_s43_e4", "A1_s44_e4")]
    Cv = [G[k]["overall"] for k in ("C_s42_e2", "C_s43_e2", "C_s44_e2")]
    Ab = [G[k]["per_policy"]["retrieve_or_abstain"]["acc"] for k in ("B_s42_e2", "B_s43_e4", "B_s44_e2")]
    half = [(max(v) - min(v)) / 2 for v in (Bv, A1, Cv, Ab)]
    fig, ax = plt.subplots(figsize=(5.8, 2.8))
    ax.barh(range(4), [h * 100 for h in half], color=[OKABE["B"], OKABE["A1"], OKABE["C"], "#999999"])
    for i, h in enumerate(half):
        ax.text(h * 100 + .2, i, f"±{h*100:.1f}pp", va="center", fontsize=8)
    ax.axvline(3.9, color="k", ls="--", lw=1.2)
    ax.text(4.05, 1.5, "nf3 blind err +3.9pp\n(data-corrected)", fontsize=7, va="center")
    ax.axvline(1.9, color=OKABE["A1"], ls=":", lw=1.2)
    ax.text(2.0, 0.5, "figK err +1.9pp", fontsize=7, color=OKABE["A1"], va="center")
    ax.set_yticks(range(4)); ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("3-seed half-range (pp)")
    ax.set_title("Seed-noise ruler: prediction errors must sit below arm noise", fontsize=9.5)
    fig.text(.01, -.06, "Sources: loop3/eval/genre_scores.json (3-seed arms; half of max-min). "
             "Abstain = retrieve_or_abstain acc across B seeds .34/.15/.45 → ±15pp: its predictions "
             "must be judged multi-seed. Ref lines: nf3 format holdout (+3.9pp, corrected from slide's "
             "3.5 per batch1_scores) and figK keep holdout (+1.9pp).", **FOOT)
    save(fig, "figN_noise_ruler",
         "# figN\nCaption: 预测误差必须显著小于 seed 噪声才算规律;弃答列噪声±15pp,判定必须 multi-seed。\n"
         f"half-ranges: B ±{half[0]:.3f} A1 ±{half[1]:.3f} C ±{half[2]:.3f} abstain ±{half[3]:.3f}\n"
         "NOTE: instruction's '合格线 6.2' reference not resolvable from repo data — flagged, not drawn.\n")


def fig_r():
    fig, ax = plt.subplots(figsize=(9.0, 2.2))
    ax.axis("off")
    steps = ["Profile\n(inference only)", "2-dose pilots\n(60 / 600)\nper component",
             "Fit / calibrate\nresponse params", "argmax recipe\nunder budget",
             "Train once", "vs 5 baselines\nuniform · hand-ratio\ngeneric · by-freq · patch-worst"]
    for i, s in enumerate(steps):
        w = 1.75 if i == 5 else 1.35
        ax.add_patch(plt.Rectangle((i * 1.55, 0), w, 1, fc="#EAF2FA", ec=OKABE["A1"], lw=1.2))
        ax.text(i * 1.55 + w / 2, .5, s, ha="center", va="center",
                fontsize=6.5 if i == 5 else 7.5)
        if i < 5:
            ax.annotate("", xy=(i * 1.55 + 1.52, .5), xytext=(i * 1.55 + 1.38, .5),
                        arrowprops=dict(arrowstyle="->", lw=1.4))
    ax.set_xlim(-.1, 9.6); ax.set_ylim(-.15, 1.3)
    ax.set_title("Prescription pipeline — SCHEMATIC", fontsize=10)
    fig.text(.01, .01, "SCHEMATIC (roadmap; no data).", **FOOT)
    save(fig, "figR_pipeline", "# figR\nSCHEMATIC pipeline page.\n")


if __name__ == "__main__":
    fig_p(); fig_v(); fig_l(); fig_k(); fig_d(); fig_n(); fig_r()
    print("CONVERGENT_FIGS_OK")
