#!/usr/bin/env python3
"""C-19 report pack: group-meeting figures/tables, zero new compute.
All numbers re-sourced from repo data files (iron rule 0); every figure gets a
.meta.md with caption draft + data paths. Output: report_pack/out/.
"""
from __future__ import annotations

import itertools
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from figs.style import OKABE  # noqa: E402  (rc setup on import)
import matplotlib as mpl  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

# CJK fallback for slide text (latin stays DejaVu per FIGURE_STYLE)
mpl.rcParams["font.sans-serif"] = ["DejaVu Sans", "PingFang SC",
                                   "Hiragino Sans GB", "Arial Unicode MS"]
OUT = ROOT / "report_pack/out"
OUT.mkdir(parents=True, exist_ok=True)
P0C = ROOT / "prescription/p0c/p0c_scores.json"
P1S = ROOT / "prescription/p1/p1_scores.json"
V2 = ROOT / "prescription/p1/v2_audit.json"


def save(fig, slug, meta):
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{slug}.{ext}", dpi=300)
    (OUT / f"{slug}.meta.md").write_text(meta)
    plt.close(fig)
    print("saved", slug)


# ---------------- Fig A: variance decomposition ----------------
def fig_a():
    S = json.loads(P0C.read_text())
    base = S["BASE"]
    cells = sorted(base)
    obs = []
    for tag, cd in S.items():
        if tag == "BASE":
            continue
        rs = {c: cd[c] - base[c] for c in cells}
        m = st.mean(rs.values())
        obs += [(tuple(c.split("|")), rs[c] - m) for c in cells]
    grand = st.mean(r for _, r in obs)
    ss_tot = sum((r - grand) ** 2 for _, r in obs)
    names = ["Evidence", "Operation", "Interface", "Answerability"]

    def gmean(keyf):
        g = defaultdict(list)
        for lv, r in obs:
            g[keyf(lv)].append(r)
        return {k: (st.mean(v), len(v)) for k, v in g.items()}

    eta, mains = {}, {}
    for i, nm in enumerate(names):
        gm = gmean(lambda l, i=i: l[i])
        mains[nm] = gm
        eta[nm] = sum(n * (m - grand) ** 2 for m, n in gm.values()) / ss_tot
    for i, j in itertools.combinations(range(4), 2):
        gm = gmean(lambda l, i=i, j=j: (l[i], l[j]))
        ss = sum(n * (m - mains[names[i]][a][0] - mains[names[j]][b][0] + grand) ** 2
                 for (a, b), (m, n) in gm.items())
        eta[f"{names[i]}×{names[j]}"] = ss / ss_tot
    order = names + [k for k in eta if "×" in k]
    order.sort(key=lambda k: -eta[k])
    ab = {"Evidence": "Ev", "Operation": "Op", "Interface": "Itf", "Answerability": "Ans"}

    def short(k):
        return "×".join(ab[p] for p in k.split("×")) if "×" in k else k

    fig, ax = plt.subplots(figsize=(7.0, 2.8))
    cols = [OKABE["A1"] if "×" not in k else "#999999" for k in order]
    ax.bar(range(len(order)), [eta[k] * 100 for k in order], color=cols)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels([short(k) for k in order], fontsize=8, rotation=20)
    ax.set_ylabel("share of training-effect variance (%)")
    iop = order.index("Operation")
    ax.text(iop + .45, eta["Operation"] * 100 - 1, "Operation dominates",
            fontsize=9, va="top")
    iev = order.index("Evidence")
    ax.annotate("Evidence ≈ 0", (iev, eta["Evidence"] * 100 + .3),
                xytext=(iev - 1.5, 7), fontsize=9,
                arrowprops=dict(arrowstyle="-", lw=1))
    rem = 1 - sum(eta.values())
    ax.set_title("Where does the old “genre effect” live? "
                 "(231-ckpt × 16-cell factorial re-eval)", fontsize=10, pad=10)
    fig.text(.01, -.06,
             f"Method: balanced 2⁴ ANOVA on within-checkpoint-centered R = S(ckpt,cell) − S(base,cell); "
             f"η² = SS/SS_total; remainder (3/4-way + ckpt×cell) = {rem*100:.1f}%. "
             f"Data: prescription/p0c/p0c_scores.json, n = 230 trained ckpts + base.",
             fontsize=6, color="#555555")
    meta = (
        "# figA_variance\n\n"
        "**Caption**: 旧 plain/repair 二分的效应，在 factorial 坐标下"
        "几乎全部由“要求模型执行什么操作”承载。\n\n"
        f"η²: {json.dumps({k: round(v,4) for k,v in eta.items()})}\n"
        f"remainder {rem:.4f}\n\n"
        "**Data**: prescription/p0c/p0c_scores.json (231 entries; 230 trained + BASE)\n"
        "**Method**: balanced 2^4 ANOVA on within-ckpt-centered R; eta^2 shares; "
        "2-way interactions listed, higher-order + ckpt heterogeneity in remainder.\n"
    )
    save(fig, "figA_variance", meta)
    return eta


# ---------------- Fig B: abstention tax poster ----------------
def fig_b():
    S = json.loads(P0C.read_text())
    base = S["BASE"]
    icells = [c for c in base if "INSUFFICIENT" in c]
    b = st.mean(base[c] for c in icells)
    rows = []
    for tag, cd in S.items():
        if tag == "BASE":
            continue
        rows.append((tag, st.mean(cd[c] - base[c] for c in icells),
                     st.mean(cd[c] for c in icells)))
    neg = [x for x in rows if x[1] < 0]
    exc = [x for x in rows if x[1] >= 0]
    assert all(t.startswith("bend_f_") for t, _, _ in exc), exc
    fig = plt.figure(figsize=(7.0, 4.6))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.4, 1], hspace=.45)
    ax0 = fig.add_subplot(gs[0])
    ax0.axis("off")
    ax0.text(.5, .62, f"{len(neg)} / {len(rows)}", ha="center", va="center",
             fontsize=52, fontweight="bold", color=OKABE["drills"])
    ax0.text(.5, .18, "训练臂损伤“信息不足应答不可答”能力的比例",
             ha="center", fontsize=13, fontfamily="Arial Unicode MS")
    ax0.text(.5, -.02, f"(the only {len(exc)} exceptions are all step-checkpoints "
             "of one synthetic run, bend_f)", ha="center", fontsize=8, color="#555555")
    ax1 = fig.add_subplot(gs[1])
    ax1.hist([a for _, _, a in rows], bins=30, color=OKABE["A1"], alpha=.85)
    ax1.axvline(b, color="black", lw=1.5, ls="--")
    ax1.text(b + .008, ax1.get_ylim()[1] * .9, f"base {b:.3f}", fontsize=8)
    ax1.set_xlabel("abstain retention (mean of 8 INSUFFICIENT cells)")
    ax1.set_ylabel("# ckpts")
    fig.text(.01, -.02,
             f"Criterion: mean R over the 8 INSUFFICIENT cells < 0, i.e. strictly below base ({b:.4f}). "
             "Data: prescription/p0c/p0c_scores.json, n = 230 trained ckpts. "
             "NOTE: corrects the “230/231” in NOTES_p0c_pilot.md (tally error; see correction appended there).",
             fontsize=6, color="#555555")
    meta = (
        "# figB_abstain_tax\n\n"
        f"**Headline**: {len(neg)}/{len(rows)} trained checkpoints damage abstention "
        f"(mean INSUFFICIENT R < 0 vs base {b:.4f}).\n"
        f"**Exceptions**: {len(exc)}, ALL step-checkpoints of the single bend_f synthetic run "
        f"(R +.017…+.049).\n\n"
        "**口径更正**: NOTES_p0c_pilot.md 写的 230/231 是记账笔误；"
        "按数据文件实算为 214/230，16 个例外全部来自同一个 "
        "bend_f 合成臂的 16 个 step-checkpoint。普适税结论定性不变"
        "（除一个合成域训练运行外全部受损），"
        "但大字报数字用实算值。\n\n"
        "**Data**: prescription/p0c/p0c_scores.json\n"
    )
    save(fig, "figB_abstain_tax", meta)
    return len(neg), len(rows), b


# ---------------- Fig C: P1 hard-stop table ----------------
def fig_c():
    P = json.loads(P1S.read_text())
    b6 = [P[f"d4_bal_600_s{s}_e4"] for s in (42, 43, 44)]

    def f3(x):
        return f"{x:.3f}".replace("0.", ".", 1)

    def rng(key):
        v = sorted(x[key] for x in b6)
        return f"{f3(v[0])}–{f3(v[-1])}"

    def arm(tag):
        v = P[tag]
        return f3(v["keep_rate"]), f3(v["override_rate"]), f3(v["insuf_retention"])

    rows = [
        ("base (untrained)", ".888", ".242", ".463"),
        ("cleanreplay placebo", ".464", ".410", ".063"),
        ("pure keep @e4", *arm("d4_pure_keep_600_s42_e4")),
        ("pure override @e4", *arm("d4_pure_override_600_s42_e4")),
        ("D4 balanced @600 e4 (3 seeds)", rng("keep_rate"), rng("override_rate"),
         rng("insuf_retention")),
        ("D4 balanced @2000 e8", *arm("d4_bal_2000_s42_e8")),
    ]
    fig, ax = plt.subplots(figsize=(7.0, 2.9))
    ax.axis("off")
    tab = ax.table(cellText=[r[1:] for r in rows],
                   rowLabels=[r[0] for r in rows],
                   colLabels=["keep", "override", "abstain retention"],
                   cellLoc="center", loc="center")
    tab.auto_set_font_size(False)
    tab.set_fontsize(9)
    tab.scale(1, 1.55)
    # emphases: placebo alone smashes keep; base override = credulity evidence
    tab[2, 0].set_facecolor("#F8DCDC"); tab[2, 0].set_text_props(fontweight="bold")
    tab[1, 1].set_facecolor("#F8DCDC"); tab[1, 1].set_text_props(fontweight="bold")
    ax.set_title("P1 hard-stop: neither preregistered outcome occurred", fontsize=10)
    fig.text(.01, .02,
             "3-seed arm shown as min–max range; all other rows single arm (as-is). "
             "Red: placebo alone smashes keep .888→.464; base override .242 (credulity). "
             "Data: prescription/p1/p1_scores.json + p0c preds (base/placebo re-derived, "
             "n=412 keep / 388 override cells).",
             fontsize=6, color="#555555")
    meta = (
        "# figC_p1_table\n\n"
        "**Caption**: P1 预注册二分双落空——keep 塌方由"
        "安慰剂单独造成（非特异税），而非 keep/override "
        "数据打架；base 高 keep 含盲从成分（override 仅 .242）。\n\n"
        "3-seed 臂：d4_bal_600 s42/s43/s44 e4；其余单臂如实。\n"
        "**Data**: prescription/p1/p1_scores.json; base/cleanreplay keep-override 从 "
        "prescription/p0c/pred_{BASE,l3_cleanreplay_s42_e4}.jsonl 重算核对（.8883/.2423, .4636/.4098）。\n"
    )
    save(fig, "figC_p1_table", meta)


# ---------------- Fig D: V-2 joint five-row table ----------------
def fig_d():
    V = json.loads(V2.read_text())

    def f3(x):
        return f"{x:.3f}".replace("0.", ".", 1)

    cr = [V[f"l3_cleanreplay_s42_e{e}"] for e in (2, 4, 8, 16)]
    crj = sorted(x["joint"] for x in cr)
    crb = sorted(x["blind_follow"] for x in cr)
    rows = [
        ("base (untrained)", f3(V["BASE"]["joint"]), f3(V["BASE"]["blind_follow"])),
        ("cleanreplay placebo (e2–e16)", f"{f3(crj[0])}–{f3(crj[-1])}",
         f"{f3(crb[0])}–{f3(crb[-1])}"),
        ("pure override @e4", f3(V["d4_pure_override_600_s42_e4"]["joint"]),
         f3(V["d4_pure_override_600_s42_e4"]["blind_follow"])),
        ("pure keep @e4", f3(V["d4_pure_keep_600_s42_e4"]["joint"]),
         f3(V["d4_pure_keep_600_s42_e4"]["blind_follow"])),
        ("D4 balanced @2000 e8", f3(V["d4_bal_2000_s42_e8"]["joint"]),
         f3(V["d4_bal_2000_s42_e8"]["blind_follow"])),
    ]
    fig, ax = plt.subplots(figsize=(6.2, 2.5))
    ax.axis("off")
    tab = ax.table(cellText=[r[1:] for r in rows], rowLabels=[r[0] for r in rows],
                   colLabels=["joint pairwise accuracy", "blind-follow rate"],
                   cellLoc="center", loc="center")
    tab.auto_set_font_size(False)
    tab.set_fontsize(9)
    tab.scale(1, 1.5)
    ax.set_title("V-2 joint re-read — preliminary, zero-compute re-read", fontsize=10)
    fig.text(.01, .02,
             "joint = same-family (keep twin correct ∧ override twin corrected); n_fam = 170. "
             "All single-arm, single-seed. Data: prescription/p1/v2_audit.json.",
             fontsize=6, color="#555555")
    meta = (
        "# figD_v2_table\n\n"
        "**Slide label**: preliminary, zero-compute re-read（只出数不出结论）\n"
        "**Data**: prescription/p1/v2_audit.json (n_fam=170)\n"
        "预测已先 commit：见 NOTES_v2_audit.md（V-2 三条裁决流程，2026-08-03）。\n"
    )
    save(fig, "figD_v2_table", meta)


if __name__ == "__main__":
    eta = fig_a()
    n_neg, n_all, b = fig_b()
    fig_c()
    fig_d()
    print("etaOperation", round(eta["Operation"], 4), "| abstain", n_neg, "/", n_all)
    print("REPORT_PACK_FIGS_OK")
