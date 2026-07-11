#!/usr/bin/env python3
"""Build the paper figure package (C-12 track A). All numbers machine-traceable;
greyed data (contaminated controls, n<50 cells) never enters a figure.
Run: python3 figs/make_figs.py            (from repo root)
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from figs.style import plt, OKABE, save  # noqa: E402

BS = json.load((ROOT / "loop3/eval/batch1_scores.json").open())
GS = json.loads((ROOT / "loop3/eval/genre_scores.json").read_text())


def row(arm):
    return next(r for r in BS if r["arm"] == arm)


# ---------------------------------------------------------------- fig 1
def fig1():
    from loop3.score_batch1 import load_pre_signatures
    from probes.profile_classify import classify
    pre, meta = load_pre_signatures()
    frac = {}
    for pool in ("gsm", "hard"):
        c = Counter()
        n = 0
        for bid, s in pre.items():
            if meta.get(bid) != pool:
                continue
            n += 1
            labs = classify(s)
            c[labs[0] if len(labs) == 1 else "mixed"] += 1
        frac[pool] = {k: v / n for k, v in c.items()}, n
    order = ["ok", "conduct", "format", "phrasing", "scaffold", "rule",
             "local_exec", "mixed", "unresolved"]
    cols = {"ok": "#DDDDDD", "conduct": OKABE["drills"], "format": OKABE["format_"],
            "phrasing": OKABE["phrasing"], "scaffold": OKABE["scaffold"],
            "rule": OKABE["rule"], "local_exec": "#F0E442", "mixed": "#888888",
            "unresolved": "#000000"}
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8),
                             gridspec_kw=dict(width_ratios=[1, 1]))
    for ax, pool, title in zip(axes, ("gsm", "hard"), ("GSM8K test", "GSM-hard bucket")):
        d, n = frac[pool]
        bottom = 0.0
        for k in order:
            v = d.get(k, 0.0)
            if v == 0:
                continue
            ax.bar([0], [100 * v], bottom=bottom, color=cols[k], width=.5,
                   label=k if pool == "gsm" else None)
            if v > 0.04:
                ax.text(0, bottom + 50 * v, f"{k} {100*v:.1f}", ha="center",
                        va="center", fontsize=7)
            bottom += 100 * v
        ax.set_title(f"{title} (n={n})")
        ax.set_xticks([])
        ax.set_ylabel("% of items" if pool == "gsm" else "")
    # surface vs robust annotation on gsm panel
    d, _ = frac["gsm"]
    axes[0].axhline(100 * d.get("ok", 0), color="k", lw=1, ls="--")
    axes[0].annotate(f"robust {100*d.get('ok',0):.1f}", xy=(0.30, 100 * d.get("ok", 0) + 1.5), fontsize=8)
    axes[0].annotate("surface score 93.5", xy=(0.30, 96), fontsize=8, color="#555")
    fig.tight_layout()
    save(fig, "fig1_profile",
         "A benchmark score hides a failure profile: of the 93.5 surface score, "
         "only the robust fraction survives interface perturbation; the failure mass "
         "decomposes into credulity (conduct), format coupling, phrasing, and "
         "assistance-recoverable buckets. Footnote trio (denominator/pool filter/"
         "labile core discount: 57% of the conduct bucket is placebo-fixable) per ruling.",
         ["probes/out*/answers.shard*.jsonl via loop3/score_batch1.load_pre_signatures",
          "probes/profile_classify.py (frozen rules)",
          "notes/NOTES_b2_0a_flip_overlap.md (labile-core footnote)"],
         "CL-4, CL-5 premise; profile v1")


# ---------------------------------------------------------------- fig 3
def fig3():
    bc = json.load((ROOT / "data_v4/results/bleed_curve.json").open())
    es = json.load((ROOT / "data_v4/results/epoch_sweep_v4.json").open())
    eps = [1, 2, 3, 8, 30]
    sc = {e: bc.get(f"scaffold_conv_e{e}") for e in eps if bc.get(f"scaffold_conv_e{e}")}
    xs = sorted(sc)
    fig, ax = plt.subplots(figsize=(4.2, 2.8))
    ax.plot(xs, [100 * sc[e]["plain"] for e in xs], "-o", color=OKABE["A1"], label="plain-genre answers")
    ax.plot(xs, [100 * sc[e]["bleed"] for e in xs], "-s", color=OKABE["drills"], label="JSON bleed")
    ax.plot(xs, [100 * sc[e]["acc"] for e in xs], "-^", color=OKABE["B"], label="plain accuracy")
    tk = [k for k in es if k.startswith("targeted_override") and "resist" in (es[k] or {})]
    if tk:
        te = sorted(int(k.rsplit("_e", 1)[1]) for k in tk)
        ax.plot(te, [100 * es[f"targeted_override_wrong_claim_e{e}"]["resist"] for e in te],
                "-D", color=OKABE["black"], label="resist (D, targeted)")
    ax.axvline(8, color="k", lw=1, ls=":")
    ax.annotate("operating point e8", xy=(8, 20), rotation=90, fontsize=7, ha="right")
    ax.annotate("D lands e2–3", xy=(2.4, 92), fontsize=8)
    ax.annotate("tax collected e8+", xy=(11, 40), fontsize=8, color=OKABE["drills"])
    ax.set_xscale("log")
    ax.set_xticks(xs); ax.set_xticklabels(xs)
    ax.set_xlabel("epochs"); ax.set_ylabel("%")
    ax.legend(fontsize=7, loc="center left")
    fig.tight_layout()
    save(fig, "fig3_ridge",
         "Repair gains and their costs are separable on the epoch axis: the decision "
         "gain lands by epoch 2-3, while genre tax (JSON bleed into plain answers) is "
         "collected only past the operating point; the three-gate stopping rule parks "
         "training between the two. C-9-corrected numbers.",
         ["data_v4/results/bleed_curve.json", "data_v4/results/epoch_sweep_v4.json"],
         "CL-1; ridge protocol R-11/R-18")


# ---------------------------------------------------------------- fig 4
def fig4():
    comps = ["conduct", "format", "phrasing", "scaffold", "rule", "drills"]
    single = {"conduct": "single_conduct_s42_e8", "format": None,  # no clean point
              "phrasing": "single_phrasing_s42_e4", "scaffold": "single_scaffold_s42_e2",
              "rule": "single_rule_s42_e4", "drills": "single_drills_s42_e4"}
    own = {"conduct": "REd_conduct", "phrasing": "REd_phrasing",
           "scaffold": "REd_scaffold", "rule": "REd_rule", "drills": "REd_conduct"}
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8))
    ax = axes[0]
    pl = row("cleanreplay_s42_e4")
    for i, c in enumerate(comps):
        if single[c] is None:
            ax.bar(i, 0, color="none", edgecolor=OKABE["format_"], hatch="//")
            ax.text(i, 3, "no clean\npoint", ha="center", fontsize=7)
            continue
        r = row(single[c])
        v = 100 * (r[own[c]] - pl[own[c]])
        ax.bar(i, v, color=OKABE.get(c, OKABE.get(c + "_", "#333")),
               edgecolor="k", linewidth=.5)
    ax.axhline(0, color="k", lw=1)
    ax.set_xticks(range(len(comps))); ax.set_xticklabels(comps, rotation=30, fontsize=7)
    ax.set_ylabel("own-bucket rescue, Δ placebo (pp)")
    ax.set_title("(a) single components (single seed, hollow)")
    ax = axes[1]
    fams = [("A1", ["A1_s42_e4", "A1_s43_e4", "A1_s44_e4"], True),
            ("B", ["B_s42_e2", "B_s43_e4", "B_s44_e2"], True),
            ("C", ["C_s42_e2", "C_s43_e2", "C_s44_e2"], True),
            ("D", ["D_s42_e2"], False),
            ("placebo", ["cleanreplay_s42_e4"], False)]
    for i, (name, keys, multi) in enumerate(fams):
        vals = [GS[k.replace("_e4", "_e4").replace("_e2", "_e2")]["overall"]
                for k in [x.replace("cleanreplay_s42_e4", "cleanreplay_s42_e4") for x in keys]]
        vals = [GS[k]["overall"] for k in keys]
        m = sum(vals) / len(vals)
        col = OKABE.get(name, "#333")
        if multi:
            ax.bar(i, m, color=col, edgecolor="k", linewidth=.5,
                   yerr=[[m - min(vals)], [max(vals) - m]], capsize=3)
        else:
            ax.bar(i, m, color="none", edgecolor=col, linewidth=1.5)
    ax.set_xticks(range(len(fams)))
    ax.set_xticklabels([f[0] for f in fams], fontsize=8)
    ax.set_ylabel("repair-genre overall")
    ax.set_title("(b) mixtures (err = min-max over 3 seeds)")
    fig.tight_layout()
    save(fig, "fig4_recipe",
         "Components matter, ratios do not: (a) only format shows a large specific "
         "own-bucket rescue over the training placebo; drills is actively harmful. "
         "(b) in the repair genre, arms containing repair components separate from "
         "placebo and generic CoT, but matched ratios (A1) never exceed uniform (B). "
         "Hollow bars = single seed. E (steering-only) slot pending decision (never run).",
         ["loop3/eval/batch1_scores.json", "loop3/eval/genre_scores.json",
          "notes/NOTES_b_seeds.md"],
         "CL-5, COR-1; red-card safe sentence only")


# ---------------------------------------------------------------- fig 5
def fig5():
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8))
    ax = axes[0]
    doses = [0, 10, 20, 36]
    keys = {0: "cleanreplay_s42_e4", 10: "fmt10_s42_e4", 20: "fmt20_s42_e4", 36: "fmt36_s42_e4"}
    ax.plot(doses, [100 * row(keys[d])["REd_format"] for d in doses], "-o",
            color=OKABE["format_"])
    ax.scatter([100], [0], marker="x", s=60, color="k")
    ax.annotate("100%: no clean point", xy=(97, 6), fontsize=7, ha="right")
    ax.set_xlabel("format dose (% items)"); ax.set_ylabel("format-bucket rescue REd (%)")
    ax.set_title("(a) format: step at ≤10%, pure diet lethal")
    ax = axes[1]
    dd = [0, 10, 25, 100]
    dkeys = {0: "cleanreplay_s42_e4", 10: "drl10_s42_e4", 25: "drl25_s42_e4",
             100: "single_drills_s42_e4"}
    gkeys = {0: "cleanreplay_s42_e4", 10: "drl10_s42_e4", 25: "drl25_s42_e4",
             100: "single_drills_s42_e4"}
    ax.plot(dd, [100 * row(dkeys[d]).get("W_adopt", 0) for d in dd], "-s",
            color=OKABE["drills"], label="plain W-adopt")
    ax.plot(dd, [100 * GS[gkeys[d]]["per_policy"]["keep_answer"]["acc"] for d in dd],
            "-o", color=OKABE["black"], label="repair-genre keep acc")
    ax.set_xlabel("drills dose (% items)")
    ax.set_ylabel("%")
    ax.legend(fontsize=7)
    ax.set_title("(b) drills: repair genre poisons first")
    fig.tight_layout()
    save(fig, "fig5_dose",
         "Dose curves. (a) Format rescue is a step, not a slope: a 10% dose (60 items) "
         "buys full rescue, higher doses add nothing, and only the 100% pure diet is "
         "lethal (no clean operating point, mute-side). (b) Drills harm enters by genre: "
         "plain-genre adoption stays at carrier level through 25% dose, while "
         "repair-genre keep accuracy already collapses at 25%; at 100% both genres fail. "
         "All dose arms single seed.",
         ["loop3/eval/batch1_scores.json", "loop3/eval/genre_scores.json",
          "notes/NOTES_batch2_dose.md"],
         "CL-5 rules 1-3, COR-2")


# ---------------------------------------------------------------- fig 6
def fig6():
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.6))
    genres = ["plain", "repair"]
    ax = axes[0]
    plain = [2.3, 6.7, 5.7]   # mean Δ placebo REd_conduct A1/B/D  (batch1_scores)
    a1 = [100 * (sum(row(k)["REd_conduct"] for k in ["A1_s42_e4", "A1_s43_e4", "A1_s44_e4"]) / 3
                 - row("cleanreplay_s42_e4")["REd_conduct"])]
    b_ = [100 * (sum(row(k)["REd_conduct"] for k in ["B_s42_e2", "B_s43_e4", "B_s44_e2"]) / 3
                 - row("cleanreplay_s42_e4")["REd_conduct"])]
    rp_a1 = 100 * (sum(GS[k]["overall"] for k in ["A1_s42_e4", "A1_s43_e4", "A1_s44_e4"]) / 3
                   - GS["cleanreplay_s42_e4"]["overall"])
    rp_b = 100 * (sum(GS[k]["overall"] for k in ["B_s42_e2", "B_s43_e4", "B_s44_e2"]) / 3
                  - GS["cleanreplay_s42_e4"]["overall"])
    x = [0, 1]
    ax.bar([i - .18 for i in x], [a1[0], rp_a1], width=.36, color=OKABE["A1"], label="A1")
    ax.bar([i + .18 for i in x], [b_[0], rp_b], width=.36, color=OKABE["B"], label="B")
    ax.set_xticks(x); ax.set_xticklabels(genres)
    ax.set_ylabel("Δ placebo (pp)"); ax.legend(fontsize=7)
    ax.set_title("(i) gain visibility")
    ax = axes[1]
    ax.bar([0 - .18, 1 - .18], [100 * row("drl25_s42_e4").get("W_adopt", 0)
                                 - 100 * row("cleanreplay_s42_e4").get("W_adopt", 0),
                                 100 * (GS["drl25_s42_e4"]["per_policy"]["keep_answer"]["acc"]
                                        - GS["cleanreplay_s42_e4"]["per_policy"]["keep_answer"]["acc"])],
           width=.36, color=OKABE["drills"])
    ax.axhline(0, color="k", lw=1)
    ax.set_xticks([-.18, .82]); ax.set_xticklabels(genres)
    ax.set_ylabel("harm at 25% dose (pp)")
    ax.set_title("(ii) drills harm")
    ax = axes[2]
    sc_plain = 100 * (row("single_scaffold_s42_e2")["REd_format"]
                      - row("cleanreplay_s42_e4")["REd_format"])
    sc_rep = 100 * (GS["single_scaffold_s42_e2"]["overall"] - GS["cleanreplay_s42_e4"]["overall"])
    ax.bar([0, 1], [sc_plain, sc_rep], width=.5,
           color=[OKABE["scaffold"], OKABE["scaffold"]])
    ax.axhline(0, color="k", lw=1)
    ax.set_xticks([0, 1]); ax.set_xticklabels(genres)
    ax.set_ylabel("scaffold effect (pp)")
    ax.set_title("(iii) benefit sign flips")
    fig.tight_layout()
    save(fig, "fig6_genre",
         "Genre gating: three independent measurements in which the evaluation genre "
         "switches the effect. (i) Repair-component gains are visible in the repair "
         "genre (+10-16pp over placebo) but not on plain items (+2-7pp). (ii) Drills "
         "harm at 25% dose appears only in the repair genre. (iii) The scaffold "
         "component's effect flips sign between genres (single seed; scafffmt "
         "attribution is a known limitation).",
         ["loop3/eval/batch1_scores.json", "loop3/eval/genre_scores.json",
          "notes/NOTES_b2_0b_genre.md", "notes/NOTES_batch2_dose.md"],
         "CL-6")


# ---------------------------------------------------------------- fig 7
def fig7():
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8))
    ax = axes[0]
    # steering E5b (plain-genre probes, L12): resist & ability vs alpha — frozen numbers
    alphas = [0, 4, 8, 16]
    resist = [83, 90, 94, 94]
    ability = [40, 39, 38, 38]
    ax.plot(alphas, resist, "-o", color=OKABE["A1"], label="resist")
    ax.plot(alphas, ability, "-s", color=OKABE["placebo"], label="ability|resist")
    ax.set_xlabel(r"steering strength $\alpha$"); ax.set_ylabel("%")
    ax.set_title("(a) decision is steerable, ability is flat")
    ax.legend(fontsize=7)
    ax = axes[1]
    tiers = ["a\nlookup", "b\n1-step", "c\n2-step", "d\n3-step"]
    idacc = [0.2, 100, 100, 99.6]
    ood = [0.0, 99.6, 99.4, 95.2]
    x = range(4)
    ax.bar([i - .18 for i in x], idacc, width=.36, color=OKABE["format_"], label="ID")
    ax.bar([i + .18 for i in x], ood, width=.36, color=OKABE["A1"], label="OOD")
    ax.set_xticks(list(x)); ax.set_xticklabels(tiers, fontsize=7)
    ax.set_ylabel("accuracy after SFT (%)")
    ax.set_title("(b) learnability frontier (zero-shot = 0 all tiers)")
    ax.legend(fontsize=7)
    fig.tight_layout()
    save(fig, "fig7_mechanism",
         "Mechanism and boundary. (a) A single activation direction moves the "
         "keep/update decision (83->94% resist) without moving computation "
         "(ability|resist flat) — the decision is separable and installable without "
         "the genre. (b) Explicit rules up to 3 steps are fully teachable and "
         "OOD-general; zero-structure lookup is not (0.2%/0.0%) — the K/A boundary "
         "is constructive, and GSM's unrepairability lies elsewhere.",
         ["notes/NOTES_steering_e5b.md (curve numbers)", "steering/out_e5b/",
          "notes/NOTES_tier2_frontier.md"],
         "CL-2, CL-3")


if __name__ == "__main__":
    for f in (fig1, fig3, fig4, fig5, fig6, fig7):
        f()
