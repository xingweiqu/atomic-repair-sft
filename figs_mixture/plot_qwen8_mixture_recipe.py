#!/usr/bin/env python3
"""Qwen3-8B Repair Mixture main figure: top = Actual U per mixture arm,
bottom = the frozen 2000-example allocation strip per arm.
ALL numbers read from PAPER_EVIDENCE_FREEZE (no hand-typed data).
Outputs: fig_qwen8_mixture_recipe_main.{png,pdf}, fig_qwen8_mixture_recipe_slide.png,
fig_qwen8_mixture_recipe_source.json (next to this script or OUT env dir)."""
import json, os, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

HERE = pathlib.Path(__file__).parent
FRZ = pathlib.Path(os.environ.get("FREEZE_DIR", HERE.parent / "PAPER_EVIDENCE_FREEZE"))
OUT = pathlib.Path(os.environ.get("OUT", HERE))
OUT.mkdir(parents=True, exist_ok=True)

spec = json.load(open(FRZ / "MIXTURE_SPEC_FROZEN.json"))["arms"]
res = json.load(open(FRZ / "MIXTURE_OPEN_RESULT.json"))["results"]

ARMS = [("replay", "Replay"), ("worst_repair", "Worst\nRepair"),
        ("predicted_optimal", "Predicted\nOptimal"), ("retention_constrained", "Retention\nConstrained"),
        ("uniform", "Uniform"), ("failure_freq", "Failure\nFrequency")]
CELLS = ["replay_total", "fmt_R", "fmt_K", "fmt_IF", "ans_R", "ans_K", "ans_IF"]
CELL_LABEL = {"replay_total": "Clean", "fmt_R": "FMT_R", "fmt_K": "FMT_K", "fmt_IF": "FMT_IF",
              "ans_R": "ANS_R", "ans_K": "ANS_K", "ans_IF": "ANS_IF"}
COLOR = {"replay_total": "#BFBFBF",
         "fmt_R": "#1F4E8C", "fmt_K": "#4C7FBF", "fmt_IF": "#9DBFE3",
         "ans_R": "#B35900", "ans_K": "#E08214", "ans_IF": "#F6C580"}
STRIP_NOTE = {"replay": "clean only", "worst_repair": "concentrated",
              "uniform": "full 6-cell coverage",
              "failure_freq": "diagnosis-heavy; violates FA"}
FA_LIMIT = 0.10

source = {"arms": {}, "provenance": "MIXTURE_SPEC_FROZEN.json (allocations) + MIXTURE_OPEN_RESULT.json (actual_U, false_abstain_R)"}
for key, _ in ARMS:
    source["arms"][key] = {"allocation": {c: spec[key][c] for c in CELLS},
                           "actual_U": res[key]["actual_U"], "false_abstain_R": res[key]["false_abstain_R"],
                           "valid": res[key]["false_abstain_R"] <= FA_LIMIT}
json.dump(source, open(OUT / "fig_qwen8_mixture_recipe_source.json", "w"), indent=1)

def draw(figsize, fs, title, fname_stem, slide=False):
    fig = plt.figure(figsize=figsize, facecolor="white")
    gs = fig.add_gridspec(2, 1, height_ratios=[65, 35], hspace=0.08)
    ax = fig.add_subplot(gs[0]); axb = fig.add_subplot(gs[1], sharex=ax)
    X = np.arange(len(ARMS))
    for i, (key, lab) in enumerate(ARMS):
        U = res[key]["actual_U"]; fa = res[key]["false_abstain_R"]
        invalid = fa > FA_LIMIT
        ax.bar(i, U, 0.62,
               color="#FFFFFF" if invalid else "#6E7FA8",
               edgecolor="#C0392B" if invalid else "#3A4A6B",
               hatch="///" if invalid else None, lw=1.4 if invalid else 0.8, zorder=3)
        ax.text(i, U + 0.004, f"{U:.3f}", ha="center", fontsize=fs, fontweight="bold",
                color="#C0392B" if invalid else "black")
        if invalid:
            ax.text(i, U + 0.021, f"INVALID:\nFalse Abstain = {fa:.2f} > {FA_LIMIT:.2f}",
                    ha="center", fontsize=fs - 2.2, color="#C0392B")
            ax.plot(i, U / 2, marker="x", ms=14 if slide else 10, mew=2.4, color="#C0392B", zorder=4)
    uni = [i for i, (k, _) in enumerate(ARMS) if k == "uniform"][0]
    po = [i for i, (k, _) in enumerate(ARMS) if k == "predicted_optimal"][0]
    ax.text(uni, res["uniform"]["actual_U"] + 0.021, "Best valid arm", ha="center",
            fontsize=fs - 1, color="#1E7A1E", fontweight="bold")
    ax.text(po, res["predicted_optimal"]["actual_U"] + 0.019, "Additive model\ntop pick", ha="center",
            fontsize=fs - 1.6, color="#3A4A6B")
    yarr = res["uniform"]["actual_U"] + 0.030
    ax.annotate("", xy=(uni - 0.2, yarr), xytext=(po + 0.2, yarr),
                arrowprops=dict(arrowstyle="->", lw=1.1, color="#555555"))
    ax.text((uni + po) / 2, yarr + 0.004, "Predicted top pick $\\neq$ Actual best valid",
            ha="center", fontsize=fs - 1.4, style="italic", color="#333333")
    ax.set_ylabel("Actual Utility $U$", fontsize=fs)
    ax.set_ylim(0.50, 0.70)
    ax.set_title(title, fontsize=fs + 2, pad=10)
    ax.tick_params(labelbottom=False)
    ax.grid(axis="y", lw=0.3, alpha=0.4, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    # bottom allocation strips
    W, H = 0.82, 0.34
    for i, (key, lab) in enumerate(ARMS):
        left = i - W / 2; y0 = 0.42
        for c in CELLS:
            n = spec[key][c]
            if n == 0: continue
            w = W * n / 2000.0
            axb.add_patch(Rectangle((left, y0), w, H, fc=COLOR[c], ec="white", lw=0.4))
            if n >= (140 if slide else 300):
                axb.text(left + w / 2, y0 + H / 2, f"{n}", ha="center", va="center",
                         fontsize=fs - 2.5, color="white" if c != "fmt_IF" and c != "ans_IF" else "#333")
            left += w
        note = STRIP_NOTE.get(key)
        if note:
            ynote = 0.16 if key == "failure_freq" else 0.30
            axb.text(i, ynote, f"({note})", ha="center", fontsize=fs - 2.6, style="italic", color="#555")
    axb.set_ylim(0, 1); axb.set_xlim(-0.6, len(ARMS) - 0.4)
    axb.set_yticks([]); axb.set_xticks(X)
    axb.set_xticklabels([lab for _, lab in ARMS], fontsize=fs - 0.5)
    axb.set_ylabel("allocation of\n2000 examples", fontsize=fs - 2)
    for s in ("top", "right", "left"):
        axb.spines[s].set_visible(False)
    handles = [Rectangle((0, 0), 1, 1, fc=COLOR[c]) for c in CELLS]
    axb.legend(handles, [CELL_LABEL[c] for c in CELLS], ncol=7, loc="lower center",
               bbox_to_anchor=(0.5, -0.52 if not slide else -0.42), fontsize=fs - 2.4, frameon=False)
    # finding box
    txt = ("Mixture quality $\\neq \\sum_i$ single-repair gain$_i$\n"
           "Composition depends on carrier and diversity-by-dose:\n"
           "full 6-cell coverage + sufficient total dose $\\rightarrow$ premium;\n"
           "concentrated high dose $\\rightarrow$ no comparable premium.")
    ax.text(0.005, 0.975, txt, transform=ax.transAxes, ha="left", va="top",
            fontsize=fs - 1.8, bbox=dict(boxstyle="round,pad=0.45", fc="#F5F5F0", ec="#999999", lw=0.7))
    fig.savefig(OUT / f"{fname_stem}.png", dpi=250, bbox_inches="tight")
    if not slide:
        fig.savefig(OUT / f"{fname_stem}.pdf", bbox_inches="tight")
    plt.close(fig)

draw((7.2, 5.1), 8.5, "Qwen3-8B: Repair Allocation Matters Beyond Additive Single-Repair Scaling",
     "fig_qwen8_mixture_recipe_main")
draw((12.8, 7.2), 13, "How Should Atomic Repairs Be Mixed?",
     "fig_qwen8_mixture_recipe_slide", slide=True)

# self-check
chk = {a: (res[a]["actual_U"], sum(spec[a][c] for c in CELLS)) for a, _ in ARMS}
assert all(v[1] == 2000 for v in chk.values()), chk
assert abs(res["uniform"]["actual_U"] - 0.6021) < 1e-6 and abs(res["failure_freq"]["actual_U"] - 0.6343) < 1e-6
print("SELF-CHECK OK:", {a: v[0] for a, v in chk.items()})
