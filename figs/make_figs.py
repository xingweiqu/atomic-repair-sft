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
    cols = {"ok": "#EDEDED", "conduct": OKABE["drills"], "format": OKABE["format_"],
            "phrasing": OKABE["phrasing"], "scaffold": OKABE["scaffold"],
            "rule": OKABE["rule"], "local_exec": "#F0E442", "mixed": "#BBBBBB",
            "unresolved": "white"}
    hatch = {"unresolved": "///", "mixed": "..."}
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
                   hatch=hatch.get(k, ""), edgecolor="#666666", linewidth=.4,
                   label=k if (pool == "gsm" or k == "unresolved") else None)
            if v > 0.035:
                ax.text(0, bottom + 50 * v, f"{k} {100*v:.1f}", ha="center",
                        va="center", fontsize=7, color="black")
            bottom += 100 * v
        ax.set_title(f"{title} (n={n})")
        ax.set_xticks([])
        ax.set_ylabel("% of items" if pool == "gsm" else "")
    # surface vs robust annotation on gsm panel (inside axes; xlim set explicitly)
    d, _ = frac["gsm"]
    ax0 = axes[0]
    ax0.set_xlim(-0.55, 1.25)
    rob = 100 * d.get("ok", 0)
    ax0.axhline(rob, color="k", lw=1.2, ls="--")
    ax0.hlines(93.5, -0.25, 0.25, ls=":", color="#444", lw=1.2)
    ax0.annotate(f"robust {rob:.1f}", xy=(0.32, rob - 1), fontsize=8, va="top", fontweight="bold")
    ax0.annotate("surface 93.5", xy=(0.32, 93.5), fontsize=8, va="center", color="#444")
    fig.tight_layout()
    save(fig, "fig1_profile",
         "A benchmark score hides a failure profile: the model scores 93.5 on GSM8K "
         "but only 60.6% of items survive interface perturbation. Segment heights are "
         "exclusive (multi-signature items form the mixed segment, 3.7%); including "
         "mixed memberships, conduct totals 16.4% and phrasing 6.4% -- the frozen "
         "profile-v1 reading used in the text. Footnote trio (denominator/pool filter/"
         "labile-core discount: 57% of the conduct bucket is placebo-fixable) per ruling.",
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
    tk = [k for k in es if k.startswith("targeted_override") and "resist_wrong" in (es[k] or {})]
    if tk:
        te = sorted(int(k.rsplit("_e", 1)[1]) for k in tk)
        rv = [100 * es[f"targeted_override_wrong_claim_e{e}"]["resist_wrong"] for e in te]
        ax.plot(te, rv, "-D", color=OKABE["black"], label="resist (D, targeted)")
        ax.annotate("decision lands e2-3", xy=(2, rv[te.index(2)]),
                    xytext=(3.5, 55), fontsize=8,
                    arrowprops=dict(arrowstyle="->", lw=1))
    ax.axvline(8, color="k", lw=1, ls=":")
    ax.annotate("operating point e8", xy=(8, 20), rotation=90, fontsize=7, ha="right")
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
    multi = {"scaffold": ["single_scaffold_s42_e2", "single_scaffold_s43_e4", "single_scaffold_s44_e4"],
             "drills": ["single_drills_s42_e4", "single_drills_s44_e4"]}
    ax = axes[0]
    pl = row("cleanreplay_s42_e4")
    for i, c in enumerate(comps):
        if single[c] is None:
            ax.bar(i, 0, color="none", edgecolor=OKABE["format_"], hatch="//")
            ax.text(i, 3, "no clean\npoint", ha="center", fontsize=7)
            continue
        col = OKABE.get(c, OKABE.get(c + "_", "#333"))
        if c in multi:
            vs = [100 * (row(k)[own[c]] - pl[own[c]]) for k in multi[c]]
            m = sum(vs) / len(vs)
            ax.bar(i, m, color=col, edgecolor="k", linewidth=.5,
                   yerr=[[m - min(vs)], [max(vs) - m]], capsize=3)
        else:
            r = row(single[c])
            v = 100 * (r[own[c]] - pl[own[c]])
            ax.bar(i, v, color="none", edgecolor=col, linewidth=1.5)
    ax.axhline(0, color="k", lw=1)
    ax.set_xticks(range(len(comps))); ax.set_xticklabels(comps, rotation=30, fontsize=7)
    ax.set_ylabel("own-bucket rescue, Δ placebo (pp)")
    ax.set_title("(a) single components (hollow = single seed)")
    ax = axes[1]
    fams = [("A1", ["A1_s42_e4", "A1_s43_e4", "A1_s44_e4"], True),
            ("B", ["B_s42_e2", "B_s43_e4", "B_s44_e2"], True),
            ("C", ["C_s42_e2", "C_s43_e2", "C_s44_e2"], True),
            ("D", ["D_s42_e2", "D_s43_e2", "D_s44_e2"], True),
            ("placebo", ["cleanreplay_s42_e4"], False)]
    if "E_steer_e0" in GS:  # zero-data steering anchor (PREREG_e_arm), lands when E-arm harvested
        fams.append(("E steer\n(0 data)", ["E_steer_e0"], False))
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
         "The zero-data steering anchor E (.760) exceeds every trained arm; its edge "
         "over placebo decomposes entirely into the two decision policies (keep +.41, "
         "abstain +.35; computation policies at placebo level) — preregistered P-E-2 "
         "scored as a MISS (predicted <+10pp). Hollow bars = single seed. "
         "HARD-STOP AUTOPSY PASSED (notes/NOTES_e_arm_autopsy.md), pending advisor sign-off.",
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
    fig, axes = plt.subplots(1, 2, figsize=(5.2, 2.6))
    genres = ["plain", "repair"]
    ax = axes[0]
    a1 = 100 * (sum(row(k)["REd_conduct"] for k in ["A1_s42_e4", "A1_s43_e4", "A1_s44_e4"]) / 3
                - row("cleanreplay_s42_e4")["REd_conduct"])
    b_ = 100 * (sum(row(k)["REd_conduct"] for k in ["B_s42_e2", "B_s43_e4", "B_s44_e2"]) / 3
                - row("cleanreplay_s42_e4")["REd_conduct"])
    rp_a1 = 100 * (sum(GS[k]["overall"] for k in ["A1_s42_e4", "A1_s43_e4", "A1_s44_e4"]) / 3
                   - GS["cleanreplay_s42_e4"]["overall"])
    rp_b = 100 * (sum(GS[k]["overall"] for k in ["B_s42_e2", "B_s43_e4", "B_s44_e2"]) / 3
                  - GS["cleanreplay_s42_e4"]["overall"])
    x = [0, 1]
    ax.bar([i - .18 for i in x], [a1, rp_a1], width=.36, color=OKABE["A1"], label="A1")
    ax.bar([i + .18 for i in x], [b_, rp_b], width=.36, color=OKABE["B"], label="B")
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
    fig.tight_layout()
    save(fig, "fig6_genre",
         "Genre gating: independent measurements in which the evaluation genre "
         "switches the effect. (i) Repair-component gains are visible in the repair "
         "genre (+10-16pp over placebo, 3 seeds) but not on plain items (+2-7pp). "
         "(ii) Drills harm at a 25% dose appears only in the repair genre. A third "
         "GSM case (scaffold benefit sign flip) was single-seed and failed "
         "replication at healthy operating points; it is retired to the appendix. "
         "The 2Wiki domain reverses the revealing genre (Fig. 8), completing the "
         "(domain x genre) claim.",
         ["loop3/eval/batch1_scores.json", "loop3/eval/genre_scores.json",
          "notes/NOTES_b2_0b_genre.md", "notes/NOTES_c15a.md (retirement)"],
         "CL-6 (revised per 2026-07-20 ruling)")


# ---------------------------------------------------------------- fig 7
def fig7():
    """Steering, single-theme (C-17 P2): (a) Qwen decision curves, (b) Llama L22 lever."""
    import json as _j
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8))
    ax = axes[0]
    alphas = [0, 4, 8, 16]
    resist = [83, 90, 94, 94]
    ability = [40, 39, 38, 38]
    ax.plot(alphas, resist, "-o", color=OKABE["A1"], label="resist")
    ax.plot(alphas, ability, "-s", color=OKABE["placebo"], label="ability|resist")
    ax.set_xlabel(r"steering strength $\alpha$"); ax.set_ylabel("%")
    ax.set_title("(a) Qwen3-8B: decision moves, computation flat")
    ax.legend(fontsize=7)
    ax = axes[1]
    grid = {}
    import glob as _g
    for f in _g.glob(str(ROOT / "loop3/eval_m3/scan2_shard*.json")):
        grid.update(_j.load(open(f)))
    al = [0, 2, 4, 6, 8]
    res = [100 * grid["base"]["resist"]] + [100 * grid[f"L22_a{a}"]["resist"] for a in (2, 4, 6, 8)]
    ab = [100 * grid["base"]["ability_given_resist"]] +          [100 * grid[f"L22_a{a}"]["ability_given_resist"] for a in (2, 4, 6, 8)]
    ax.plot(al, res, "-o", color=OKABE["D"], label="resist")
    ax.plot(al, ab, "-s", color=OKABE["placebo"], label="ability|resist")
    ax.set_xlabel(r"steering strength $\alpha$ (layer 22)"); ax.set_ylabel("%")
    ax.set_title("(b) Llama-3.1-8B: the lever transfers")
    ax.legend(fontsize=7)
    fig.tight_layout()
    save(fig, "fig7_mechanism",
         "The decision lever, on both families. (a) On Qwen3-8B a single activation "
         "direction moves resist (83->94%) while computation stays flat. (b) On "
         "Llama-3.1-8B the same extraction recipe finds the lever at layer 22 "
         "(96-item scan subset): resist rises from 52% to 82% with ability|resist "
         "flat until alpha 8. The repair-genre dividend is contract-gated and does "
         "not follow (section 6).",
         ["notes/NOTES_steering_e5b.md", "loop3/eval_m3/scan2_shard*.json"],
         "CL-3 two-layer")


def fig_a_frontier():
    """Frontier figure, appendix home (C-17 P2)."""
    fig, ax = plt.subplots(figsize=(4.8, 2.6))
    tiers = ["a\nlookup", "b\n1-step", "c\n2-step", "d\n3-step",
             "e\n5-step", "f\nbranch", "g\nNL-wrap"]
    idacc = [0.2, 100, 100, 99.6, 99.4, 100, 100]
    ood = [0.0, 99.6, 99.4, 95.2, 83.0, 100, 100]
    x = range(7)
    ax.bar([i - .18 for i in x], idacc, width=.36, color=OKABE["format_"], label="ID")
    ax.bar([i + .18 for i in x], ood, width=.36, color=OKABE["A1"], label="OOD")
    ax.set_xticks(list(x)); ax.set_xticklabels(tiers, fontsize=6.5)
    ax.set_ylabel("accuracy after SFT (%)")
    ax.annotate("overtrain dip:\nOOD .91@ep1 -> .66@ep4", xy=(4.18, 83), xytext=(2.6, 45),
                fontsize=6.5, arrowprops=dict(arrowstyle="->", lw=.8))
    ax.legend(fontsize=7)
    fig.tight_layout()
    save(fig, "fig_a_frontier",
         "The synthetic learnability frontier (appendix). Explicit invented rules are "
         "fully teachable and OOD-general through 5-step chains, branching and "
         "natural-language wrapping; zero-structure lookup is not. In this synthetic "
         "frontier these factors alone do not create a learning boundary.",
         ["notes/NOTES_tier2_frontier.md", "data_bend/race_summary.json"],
         "CL-2 (synthetic-scoped)")


# ---------------------------------------------------------------- fig 7
def fig7_old():
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
    tiers = ["a\nlookup", "b\n1-step", "c\n2-step", "d\n3-step",
             "e\n5-step", "f\nbranch", "g\nNL-wrap"]
    idacc = [0.2, 100, 100, 99.6, 99.4, 100, 100]
    ood = [0.0, 99.6, 99.4, 95.2, 83.0, 100, 100]
    x = range(7)
    ax.bar([i - .18 for i in x], idacc, width=.36, color=OKABE["format_"], label="ID")
    ax.bar([i + .18 for i in x], ood, width=.36, color=OKABE["A1"], label="OOD")
    ax.set_xticks(list(x)); ax.set_xticklabels(tiers, fontsize=6.5)
    ax.set_ylabel("accuracy after SFT (%)")
    ax.set_title("(b) learnability frontier (zero-shot = 0 all tiers)")
    ax.annotate("overtrain dip:\nOOD .91@ep1 -> .66@ep4", xy=(4.18, 83), xytext=(3.0, 45),
                fontsize=6.5, arrowprops=dict(arrowstyle="->", lw=.8))
    ax.legend(fontsize=7)
    fig.tight_layout()
    save(fig, "fig7_mechanism_old",
         "Mechanism and boundary. (a) A single activation direction moves the "
         "keep/update decision (83->94% resist) without moving computation "
         "(ability|resist flat) — the decision is separable and installable without "
         "the genre. (b) Explicit rules up to 3 steps are fully teachable and "
         "OOD-general; zero-structure lookup is not (0.2%/0.0%) — the K/A boundary "
         "is constructive. The frontier stays unbent through 5-step chains (OOD 83%, "
         "with overtraining damaging OOD from its epoch-1 peak), conditional branching "
         "(100%), and natural-language wrapping (100%): GSM's unrepairability is not "
         "chain depth, control flow, or wrapping.",
         ["notes/NOTES_steering_e5b.md (curve numbers)", "steering/out_e5b/",
          "notes/NOTES_tier2_frontier.md", "data_bend/race_summary.json"],
         "CL-2, CL-3")


if __name__ == "__main__":
    for f in (fig1, fig3, fig4, fig5, fig6, fig7, fig_a_frontier):
        f()


# ---------------------------------------------------------------- fig 2
def fig2():
    import csv
    rows = list(csv.DictReader((ROOT / "ledger/master_ledger.csv").open()))
    rows = [r for r in rows if r["grey"] == ""]  # greyed rows never enter a figure

    def fl(r, k):
        try:
            return float(r[k])
        except (ValueError, KeyError):
            return None

    for r in rows:  # C-5: v2_inject is the canonical K row; it belongs in the v2 group
        if r["domain"] == "v2_inject":
            r["domain"] = "v2"
    doms = ["v2", "v2_1", "v3", "v3_1", "v4", "v5"]
    labels = {"v2": "v2 fact-inject", "v2_1": "v2.1", "v3": "v3 synthetic",
              "v3_1": "v3.1", "v4": "v4 GSM", "v5": "v5 clean"}
    chans = [("F_judge", "F (format/judge)", OKABE["format_"]),
             ("F_parse", "F (parse/floor)", "#9BD1EE"),
             ("K", "K (content recall)", OKABE["conduct"]),
             ("M", "M (leak/memor.)", "#8C6BB1"),
             ("D", "D (decision)", OKABE["B"]),
             ("A_delivered", "A (delivered)", OKABE["drills"])]
    fig, ax = plt.subplots(figsize=(6.4, 2.9))
    nrow = {}
    for i, d in enumerate(doms):
        sub = [r for r in rows if r["domain"] == d]
        nrow[d] = len(sub)
        pos = neg = 0.0
        for key, lab, col in chans:
            vals = [fl(r, key) for r in sub]
            vals = [v for v in vals if v is not None]
            if not vals:
                continue
            m = 100 * sum(vals) / len(vals)
            if m >= 0:
                ax.bar(i, m, bottom=pos, color=col, width=.62,
                       label=lab if i == max(range(len(doms)), key=lambda j: doms[j] == "v4") else None)
                pos += m
            else:
                ax.bar(i, m, bottom=neg, color=col, width=.62)
                neg += m
    ax.axhline(0, color="k", lw=1)
    ax.set_xticks(range(len(doms)))
    ax.set_xticklabels([f"{labels[d]}\n(n={nrow[d]})" for d in doms], fontsize=7)
    ax.set_ylabel("mean channel contribution (pp)")
    handles, labs_ = ax.get_legend_handles_labels()
    ax.legend(handles, labs_, fontsize=6.5, ncol=2, loc="upper right")
    fig.tight_layout()
    save(fig, "fig2_ledger",
         "Where repair gains actually come from: re-accounting 644 non-grey historical "
         "runs decomposes raw gains into format (judge+parse), content recall (K), "
         "leak/memorisation (M), decision (D), and delivered ability (A). The C-5 K/M "
         "split is applied by evaluation construct (recall vs procedure): the v2 "
         "fact-injection exemplar row enters as K (+98pp), not M. Greyed rows "
         "(REF/contaminated) excluded per style rule. Ledger grew 672->678 rows via "
         "the R-17 ridge re-accounting (floor=e8 rebuild); Loop-3 arms are not ledger rows.",
         ["ledger/master_ledger.csv (678 rows; 34 REF-grey excluded)",
          "qc/LOOP1_5_RULINGS_C5.md (K/M split rules)"],
         "CL-1 context; ledger chapter")


# ---------------------------------------------------------------- fig 8
def fig8():
    w2 = json.loads((ROOT / "wiki2/data/scores_2wiki.json").read_text())
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.7), gridspec_kw=dict(width_ratios=[1, 1, 1.3]))
    arms = [("pre-repair", "Qwen3-8B", OKABE["placebo"]),
            ("U mix", "w2_U_e4", OKABE["B"]),
            ("FMT 10%", "w2_FMT_e4", OKABE["format_"]),
            ("placebo", "w2_cleanreplay_e2", "#BBBBBB")]
    ax = axes[0]
    for i, (lab, k, col) in enumerate(arms):
        p = w2[k]["profile"]
        ax.bar(i - .17, p.get("conduct_adopt", 0), width=.34, color=col, edgecolor="k", lw=.4)
        ax.bar(i + .17, p.get("conduct_derail", 0), width=.34, color=col, alpha=.45,
               edgecolor="k", lw=.4)
    ax.set_xticks(range(len(arms))); ax.set_xticklabels([a[0] for a in arms], fontsize=6.5)
    ax.set_ylabel("items"); ax.set_title("(a) 2Wiki plain: adopt | derail", fontsize=8.5)
    ax = axes[1]
    for i, (lab, k, col) in enumerate(arms):
        ax.bar(i, 100 * w2[k]["repair"]["acc_strict"], color=col, edgecolor="k", lw=.4)
    ax.set_xticks(range(len(arms))); ax.set_xticklabels([a[0] for a in arms], fontsize=6.5)
    ax.set_ylabel("%"); ax.set_title("(b) 2Wiki repair genre (strict)", fontsize=8.5)
    # (c) natural-set mapping matrix
    ns = [json.loads(l) for l in (ROOT / "naturalset/natural_set_v1.jsonl").open()]
    srcs = ["CREPE", "GSM-IC", "FalseQA", "sycophancy-eval/answer", "NQ-Swap", "RGB"]
    probes = ["W2", "W1", "abstain", "K-conflict(W2)", "none"]
    mat = [[sum(1 for r in ns if r["source"] == s and r["mapped_probe"] == pr)
            for pr in probes] for s in srcs]
    ax = axes[2]
    im = ax.imshow(mat, cmap="Blues", aspect="auto")
    for i in range(len(srcs)):
        for j in range(len(probes)):
            if mat[i][j]:
                ax.text(j, i, mat[i][j], ha="center", va="center", fontsize=7,
                        color="white" if mat[i][j] > 30 else "black")
    ax.set_xticks(range(len(probes)))
    ax.set_xticklabels(["W2", "W1", "abstain", "K-confl", "none\n(blind)"], fontsize=6.5)
    ax.set_yticks(range(len(srcs)))
    ax.set_yticklabels(["CREPE", "GSM-IC", "FalseQA", "syco", "NQ-Swap", "RGB"], fontsize=6.5)
    ax.set_title("(c) real-world failures -> probes", fontsize=8.5)
    ax.grid(False)
    fig.tight_layout()
    save(fig, "fig8_validation",
         "The pipeline off GSM. (a-b) 2WikiMultihopQA miniature: the anti-credulity "
         "component transfers on the plain face (adopt 19->0, derail 28->4) while "
         "repair-genre accuracy does not separate from placebo and every 600-item arm "
         "sits below the pre-repair model — genre gating's direction is domain-"
         "dependent (fourth case). (c) 200 real-world messy prompts from six public "
         "datasets map onto the probe taxonomy; the blind-spot column (retrieval "
         "noise) is reported honestly. e4/e2 operating points; single seed.",
         ["wiki2/data/scores_2wiki.json", "naturalset/natural_set_v1.jsonl",
          "notes/NOTES_2wiki.md"],
         "CL-6 (domain x genre), PREREG_2wiki P-2W-1/2/3, PREREG_naturalset")


# ---------------------------------------------------------------- appendix: overlap matrix
def fig_a_overlap():
    fo = json.loads((ROOT / "loop3/eval/flip_overlap.json").read_text())
    core = fo["stable_core"]
    labs = ["conduct", "format", "phrasing", "scaffold"]
    fig, ax = plt.subplots(figsize=(4.6, 2.4))
    x = range(len(labs))
    ax.bar([i - .2 for i in x], [100 * core[l]["core"] / core[l]["denom"] for l in labs],
           width=.4, color=OKABE["placebo"], label="core (rescued by ALL incl. placebo)")
    ax.bar([i + .2 for i in x], [100 * core[l]["union"] / core[l]["denom"] for l in labs],
           width=.4, color=OKABE["A1"], label="union (rescued by ANY)")
    ax.set_xticks(list(x)); ax.set_xticklabels(labs, fontsize=8)
    ax.set_ylabel("% of bucket")
    ax.legend(fontsize=7)
    fig.tight_layout()
    save(fig, "fig_a_overlap",
         "Flip-overlap audit: rescue is not dice. Every bucket has a deterministic "
         "core rescued by all arms including the training placebo (conduct 57%) and "
         "a fringe; format's near-zero core (1%) is the converse evidence — no free "
         "rescue without the component. Observed Jaccard exceeds the independent-"
         "rescue baseline in all pairs (see loop3/eval/flip_overlap.json).",
         ["loop3/eval/flip_overlap.json", "notes/NOTES_b2_0a_flip_overlap.md"],
         "Fig-1 footnote (labile-core discount); CL-5")
