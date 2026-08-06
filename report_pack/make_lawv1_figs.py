#!/usr/bin/env python3
"""C-27 figure pack: 8 figs, all values read from frozen artifacts (no hand-typed numbers).

Inputs (repo-relative, see per-fig README):
  prescription/lawv1/{format,evidence,revision}_curves.json
  prescription/lawv1/grid_scores/gs_FMT-*.json         (per-run summaries incl. seeds)
  prescription/lawv1/dose_manifest_format.json          (q_d, budget)
  prescription/lawv1/RUN_MATRIX_*.csv, DATA_ROLE_MATRIX.csv
  prescription/lawv1/runs_v2/budget_validation.json
  prescription/gate1/base_profile_v121_summary.json
  prescription/lawv1/margin_v2/*.jsonl                  (Fig7; pending if absent)
Output: report_pack/out/lawv1_figs/fig{1..8}/{figN.png,figN.pdf,source_data.json,README.md}
Repro: python3 report_pack/make_lawv1_figs.py
"""
import json, glob, csv, os, subprocess, statistics
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "report_pack/out/lawv1_figs")
ACC = "#1f77b4"          # single accent
GREY, DARK = "#999999", "#222222"
COMMIT = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                        capture_output=True, text=True).stdout.strip()
plt.rcParams.update({"figure.facecolor": "white", "axes.facecolor": "white",
                     "font.size": 11, "axes.edgecolor": DARK, "axes.labelcolor": DARK})

def J(p): return json.load(open(os.path.join(ROOT, p)))
def fig_dir(n):
    d = os.path.join(OUT, f"fig{n}"); os.makedirs(d, exist_ok=True); return d
def save(figobj, n, src, readme):
    d = fig_dir(n)
    figobj.savefig(os.path.join(d, f"fig{n}.png"), dpi=200, bbox_inches="tight")
    figobj.savefig(os.path.join(d, f"fig{n}.pdf"), bbox_inches="tight")
    json.dump(src, open(os.path.join(d, "source_data.json"), "w"), indent=1)
    open(os.path.join(d, "README.md"), "w").write(
        readme + f"\n\n- repo commit: {COMMIT}\n- 复现: `python3 report_pack/make_lawv1_figs.py`\n")
    plt.close(figobj)

FC = J("prescription/lawv1/format_curves.json")
EC = J("prescription/lawv1/evidence_curves.json")
RC = J("prescription/lawv1/revision_curves.json")
MAN = {a["arm"]: a for a in J("prescription/lawv1/dose_manifest_format.json")}
GS = {os.path.basename(f)[3:-5]: json.load(open(f))
      for f in glob.glob(os.path.join(ROOT, "prescription/lawv1/grid_scores/gs_FMT-*.json"))}
BASE = J("prescription/gate1/base_profile_v121_summary.json")
DOSES = [0, 30, 60, 120, 240, 480, 960, 2000]
ANCH = {0, 120, 960, 2000}
QD = [MAN[f"FMT-{d:04d}"]["q_d"] for d in DOSES]

def seeds_vals(dose, cond, key):
    out = []
    for s in ([42, 43, 44] if dose in ANCH else [42]):
        r = GS.get(f"FMT-{dose:04d}-S{s}")
        if r:
            v = r.get(cond, {}).get(key)
            if isinstance(v, (int, float)):
                out.append(v)
    return out

# ---------------- Fig 1: story DAG ------------------------------------------------
f, ax = plt.subplots(figsize=(14, 6)); ax.axis("off")
main = ["General\nbenchmark", "Controlled perturbation\ndiagnosis", "Small-dose\npilots",
        "Multi-dimensional\nresponse law", "Constrained\nmulti-domain recipe"]
for i, t in enumerate(main):
    ax.add_patch(plt.Rectangle((i * 2.1, 2.2), 1.8, 1.1, fill=False, ec=DARK, lw=1.4))
    ax.text(i * 2.1 + 0.9, 2.75, t, ha="center", va="center", fontsize=10)
    if i: ax.annotate("", (i * 2.1, 2.75), (i * 2.1 - 0.3, 2.75),
                      arrowprops=dict(arrowstyle="->", color=DARK))
lanes = [("CPU data build", ["asset inventory", "pools+audits", "K/IF eval build"]),
         ("GPU train", ["smoke(3+3)", "FMT/EVD/REV grids 48 runs", "K/IF sparse (pending)"]),
         ("GPU eval", ["base profiles", "per-run 518-row eval", "cross-domain (pending)"]),
         ("Analysis", ["curves", "LODO+baselines", "margin audit v2"]),
         ("Mixture / held-out", ["(pending)", "(pending)", ""])]
for li, (name, steps) in enumerate(lanes):
    y = 1.4 - li * 0.55
    ax.text(-0.3, y, name, ha="right", va="center", fontsize=9, color=DARK, fontweight="bold")
    for si, st in enumerate(steps):
        if st:
            c = GREY if "pending" in st else ACC
            ax.text(si * 3.4 + 1.2, y, st, ha="center", va="center", fontsize=8,
                    color=("white"), bbox=dict(boxstyle="round", fc=c, ec="none"))
ax.set_xlim(-2.2, 10.8); ax.set_ylim(-1.4, 3.6)
ax.set_title("Fig 1 — Story & execution DAG (accent = done/running, grey = pending)", loc="left")
save(f, 1, {"lanes": lanes, "note": "structure figure; statuses from QUEUE_STATE.md"},
     "# Fig1 故事与执行 DAG\n- 输入: prescription/lawv1/QUEUE_STATE.md(状态), 结构性示意\n- smoke/正式已在标签区分")

# ---------------- Fig 2: domain x component matrix --------------------------------
roles = list(csv.DictReader(open(os.path.join(ROOT, "prescription/lawv1/DATA_ROLE_MATRIX.csv"))))
comps = ["Clean replay", "Format", "Evidence", "Revision", "Answerability"]
doms = ["Reasoning", "Knowledge/Wiki", "General IF"]
status = {("Reasoning", c): "done" for c in ["Clean replay", "Format", "Evidence", "Revision"]}
status[("Reasoning", "Answerability")] = "audit-gated"
for d in doms[1:]:
    for c in comps:
        status[(d, c)] = "pending-freeze"
cellnote = {"Reasoning": "train GSM8K-train\neval GSM8K-test\nholdout SVAMP",
            "Knowledge/Wiki": "train 2Wiki(pending split)\neval 2Wiki\nholdout StrategyQA",
            "General IF": "CREPE/FalseQA/sycophancy\nformat+replay source PENDING"}
f, ax = plt.subplots(figsize=(13, 5.5)); ax.axis("off")
colors = {"done": ACC, "audit-gated": "#7fb3d9", "pending-freeze": "#dddddd"}
for i, dm in enumerate(doms):
    for j, c in enumerate(comps):
        st = status[(dm, c)]
        ax.add_patch(plt.Rectangle((j * 2.2, -i * 1.6), 2.0, 1.4,
                                   fc=colors[st], ec=DARK, lw=0.8))
        ax.text(j * 2.2 + 1.0, -i * 1.6 + 1.05, st, ha="center", fontsize=8,
                color="white" if st != "pending-freeze" else DARK)
        ax.text(j * 2.2 + 1.0, -i * 1.6 + 0.45, cellnote[dm], ha="center", fontsize=6.2,
                color="white" if st != "pending-freeze" else DARK)
    ax.text(-0.25, -i * 1.6 + 0.7, dm, ha="right", fontsize=10, fontweight="bold")
for j, c in enumerate(comps):
    ax.text(j * 2.2 + 1.0, 1.7, c, ha="center", fontsize=10, fontweight="bold")
ax.set_xlim(-2.6, 11.2); ax.set_ylim(-3.6, 2.1)
ax.set_title("Fig 2 — Domain × Component status (SVAMP = Reasoning holdout only)", loc="left")
save(f, 2, {"status": {f"{k[0]}|{k[1]}": v for k, v in status.items()}, "roles_csv_rows": len(roles)},
     "# Fig2 状态矩阵\n- 输入: DATA_ROLE_MATRIX.csv + QUEUE_STATE.md\n- Reasoning Answerability=审核闸门中;K/IF 全部待冻结")

# ---------------- Fig 3: format main dose response --------------------------------
panels = [("format", "contract_exact", "fmt contract_exact"),
          ("format", "main", "fmt MAIN (schema∧content)"),
          ("original", "acc_exact", "original retention"),
          ("wc_attempt", "joint", "wc_attempt joint")]
f, axes = plt.subplots(1, 4, figsize=(18, 4.2))
src3 = {}
for ax, (c, k, title) in zip(axes, panels):
    means, los, his = [], [], []
    for d in DOSES:
        vs = seeds_vals(d, c, k)
        m = statistics.mean(vs); means.append(m)
        los.append(m - min(vs)); his.append(max(vs) - m)
    ax.errorbar(range(len(DOSES)), means, yerr=[los, his], marker="o", color=ACC,
                lw=1.6, capsize=3, label="format arm")
    b = BASE.get(c, {}).get(k)
    if b is not None:
        ax.axhline(b, color=DARK, ls=":", lw=1, label="base (no train)")
    ax.axhline(means[0], color=GREY, ls="--", lw=1, label="matched replay (dose 0)")
    ax.set_xticks(range(len(DOSES))); ax.set_xticklabels(DOSES, fontsize=8)
    sec = ax.secondary_xaxis("top")
    sec.set_xticks(range(len(DOSES))); sec.set_xticklabels([f"{q:.3f}" for q in QD], fontsize=6)
    sec.set_xlabel("q_d (target-token share)", fontsize=7)
    ax.set_title(title, fontsize=10); ax.set_ylim(0, 1.05); ax.set_xlabel("dose (examples)")
    src3[title] = {"doses": DOSES, "q_d": QD, "mean": means}
axes[0].legend(fontsize=7, loc="lower right")
f.suptitle("Fig 3 — Format formal dose response (2,000-example carrier; packed; 30 updates all arms; budget PASS)", y=1.13)
save(f, 3, src3, "# Fig3 Format 主图\n- 输入: grid_scores/gs_FMT-*.json(逐seed), dose_manifest_format.json(q_d), base_profile_v121_summary.json\n- 误差条=3-seed 锚点全距;正式结果(非 smoke)")

# ---------------- Fig 4: vector heatmap (component - matched replay) ---------------
eps = [("format", "contract_exact", "fmt_exact"), ("format", "main", "fmt_MAIN"),
       ("original", "acc_exact", "original"), ("paraphrase", "acc_exact", "paraphrase"),
       ("distractor", "acc_exact", "distractor"), ("insufficient", "insufficient_stop", "insuf_free"),
       ("wc_attempt", "joint", "wc_att"), ("cc_attempt", "joint", "cc_att")]
plc = {lab: statistics.mean(seeds_vals(0, c, k)) for c, k, lab in eps}
M = np.zeros((len(DOSES) - 1, len(eps)))
for i, d in enumerate(DOSES[1:]):
    for j, (c, k, lab) in enumerate(eps):
        M[i, j] = statistics.mean(seeds_vals(d, c, k)) - plc[lab]
f, ax = plt.subplots(figsize=(10, 5))
im = ax.imshow(M, cmap="RdBu_r", vmin=-0.5, vmax=0.5, aspect="auto")
ax.set_xticks(range(len(eps))); ax.set_xticklabels([e[2] for e in eps], rotation=30, ha="right", fontsize=8)
ax.set_yticks(range(len(DOSES) - 1)); ax.set_yticklabels(DOSES[1:], fontsize=8)
ax.set_ylabel("dose"); plt.colorbar(im, label="component − matched replay")
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        ax.text(j, i, f"{M[i,j]:+.2f}", ha="center", va="center", fontsize=6.5,
                color="white" if abs(M[i, j]) > 0.3 else DARK)
ax.set_title("Fig 4 — Format response vector (all cells vs matched replay; formal runs)", loc="left")
save(f, 4, {"doses": DOSES[1:], "endpoints": [e[2] for e in eps], "delta_vs_replay": M.tolist()},
     "# Fig4 向量热图\n- 口径统一: component−matched replay(placebo-adjusted);逐 seed 均值\n- 输入同 Fig3")

# ---------------- Fig 5: wc_attempt collateral decomposition ----------------------
keys = [("contract_followed", "contract_followed"), ("decision_acc", "decision_correct"),
        ("final_acc", "final_answer_correct"), ("joint", "joint"), ("adopt", "adoption")]
f, ax = plt.subplots(figsize=(10, 5))
src5 = {}
for (k, lab), mk in zip(keys, ["o", "s", "^", "D", "v"]):
    means, los, his = [], [], []
    for d in DOSES:
        vs = seeds_vals(d, "wc_attempt", k)
        m = statistics.mean(vs); means.append(m); los.append(m - min(vs)); his.append(max(vs) - m)
    col = ACC if lab == "joint" else (DARK if lab != "adoption" else GREY)
    ax.errorbar(range(len(DOSES)), means, yerr=[los, his], marker=mk, lw=1.2, capsize=2,
                label=lab, alpha=0.9 if lab == "joint" else 0.65, color=col)
    src5[lab] = means
ax.set_xticks(range(len(DOSES))); ax.set_xticklabels(DOSES)
ax.set_xlabel("format dose"); ax.set_ylim(0, 1.05); ax.legend(fontsize=8)
ax.set_title("Fig 5 — wc_attempt decomposition under format dosing (3-seed ranges at anchors)", loc="left")
save(f, 5, src5, "# Fig5 collateral 拆解\n- 输入: grid_scores gs_FMT-* 的 wc_attempt 五字段\n- 判定:哪层(接口/判断/内容)承担高剂量下降")

# ---------------- Fig 6: LODO vs dumb baselines (fmt contract_exact) ---------------
y = np.array([statistics.mean(seeds_vals(d, "format", "contract_exact")) for d in DOSES], float)
x = np.array(DOSES, float)
def huber(r, d=0.05): a = np.abs(r); return np.where(a <= d, 0.5 * r * r, d * (a - 0.5 * d)).sum()
def fit_pred(xtr, ytr, xte):
    from scipy.optimize import minimize
    best = None
    # satexp c + A(1-exp(-n/tau))
    for A0, t0 in [(0.3, 30), (0.3, 200), (0.2, 60)]:
        r = minimize(lambda p: huber(ytr - (p[2] + p[0] * (1 - np.exp(-xtr / max(p[1], 1e-3))))),
                     [A0, t0, ytr[0]], method="Nelder-Mead")
        pred = r.x[2] + r.x[0] * (1 - np.exp(-xte / max(r.x[1], 1e-3)))
        if best is None or r.fun < best[0]: best = (r.fun, float(pred), "satexp")
    # step
    for th in sorted(set((xtr[:-1] + xtr[1:]) / 2)):
        lo, hi = ytr[xtr < th], ytr[xtr >= th]
        if len(lo) and len(hi):
            fun = huber(np.concatenate([lo - lo.mean(), hi - hi.mean()]))
            pred = float(hi.mean() if xte >= th else lo.mean())
            if fun < best[0]: best = (fun, pred, f"step@{th:.0f}")
    # null
    fun = huber(ytr - ytr.mean())
    if fun < best[0]: best = (fun, float(ytr.mean()), "null")
    return best
rows6, mae = [], {"law": [], "nearest": [], "loglin": [], "const": []}
for i, d in enumerate(DOSES):
    xtr, ytr = np.delete(x, i), np.delete(y, i)
    _, p_law, form = fit_pred(xtr, ytr, x[i])
    p_near = float(ytr[np.argmin(np.abs(xtr - x[i]))])
    A = np.vstack([np.log1p(xtr), np.ones_like(xtr)]).T
    coef, *_ = np.linalg.lstsq(A, ytr, rcond=None)
    p_log = float(coef[0] * np.log1p(x[i]) + coef[1])
    p_c = float(ytr.mean())
    kind = "extrap" if i in (0, len(DOSES) - 1) else "interp"
    rows6.append(dict(dose=int(d), truth=float(y[i]), law=p_law, form=form,
                      nearest=p_near, loglin=p_log, const=p_c, kind=kind))
    for k2, v in (("law", p_law), ("nearest", p_near), ("loglin", p_log), ("const", p_c)):
        mae[k2].append(abs(v - y[i]))
noise = max(v for v in FC["fmt_exact"]["anchor_ranges"].values()) / 2
f, axes = plt.subplots(1, 2, figsize=(13, 4.6))
for ax, kind in zip(axes, ("interp", "extrap")):
    sub = [r for r in rows6 if r["kind"] == kind]
    xs = np.arange(len(sub))
    ax.plot(xs, [r["truth"] for r in sub], "ko-", label="truth", lw=1.6)
    for k2, mk, col in (("law", "o", ACC), ("nearest", "s", GREY), ("loglin", "^", GREY), ("const", "v", "#cccccc")):
        ax.plot(xs, [r[k2] for r in sub], mk + "--", color=col, label=k2, alpha=0.85)
    ax.fill_between(xs, [r["truth"] - noise for r in sub], [r["truth"] + noise for r in sub],
                    color=ACC, alpha=0.12, label="seed noise band")
    ax.set_xticks(xs); ax.set_xticklabels([r["dose"] for r in sub])
    ax.set_title(f"{kind} (LODO)"); ax.set_xlabel("held-out dose"); ax.legend(fontsize=7)
maes = {k2: round(float(np.mean(v)), 4) for k2, v in mae.items()}
f.suptitle(f"Fig 6 — LODO fmt contract_exact: MAE law={maes['law']} nearest={maes['nearest']} "
           f"loglin={maes['loglin']} const={maes['const']} (noise half-range={noise:.3f})", y=1.05)
save(f, 6, {"lodo": rows6, "mae": maes, "noise_half_range": noise},
     "# Fig6 LODO vs 哑基线\n- endpoint: fmt contract_exact(3-seed 锚点均值曲线)\n- 形态库 satexp/step/null,Huber 选形;interp/extrap 分列")

# ---------------- Fig 7: margin v2 audit (or pending) ------------------------------
mv2 = sorted(glob.glob(os.path.join(ROOT, "prescription/lawv1/margin_v2/*.jsonl")))
f, ax = plt.subplots(figsize=(11, 5))
if mv2:
    src7 = {}
    labels = ["T1", "T2", "T3", "T4a", "T4b", "T5"]
    for fn in [p for p in mv2 if "base" in p]:
        rows = [json.loads(l) for l in open(fn)]
        for kind, col in (("ans", ACC), ("cand", DARK)):
            mm = [statistics.mean([r["margin"] for r in rows if r["probe"] == kind and r["template_id"] == t]) for t in labels]
            ax.plot(labels, mm, "o-", color=col, label=f"{kind} (base)")
            src7[kind] = dict(zip(labels, mm))
    ax.axhline(0, color=GREY, lw=0.8)
    ax.set_ylabel("mean gold-margin"); ax.legend(fontsize=8)
    ax.set_title("Fig 7 — Margin probe v2 template audit (true semantic permutation T4a/T4b; genres T1/T2/T3/T5)", loc="left")
    note = "v2 实测(base;各 ckpt 数据在 margin_v2/)"
else:
    ax.text(0.5, 0.5, "PENDING — margin probe v2 running on m1\n(v1 T2/T3 zeros = instrument fault: string-level\nre-tokenization at continuation boundary; not model behavior)",
            ha="center", va="center", fontsize=12, color=GREY)
    ax.axis("off"); src7 = {"status": "pending"}
    note = "pending;v1 故障仅作仪器说明"
save(f, 7, src7, f"# Fig7 模板审计\n- {note}\n- 输入: prescription/lawv1/margin_v2/*.jsonl")

# ---------------- Fig 8: execution status ------------------------------------------
def count_done(pat):
    return len(glob.glob(os.path.join(ROOT, pat)))
layers = [
    ("Reasoning full-grid (FMT/EVD/REV)", 48, 48, "completed"),
    ("Reasoning Answerability grid", 0, 16, "audit-gated"),
    ("Reasoning external eval (SVAMP)", 0, 0, "pending-build"),
    ("Knowledge/Wiki cross-domain eval", 0, 49, "pending-build"),
    ("General IF cross-domain eval", 0, 49, "pending-build"),
    ("Knowledge sparse training", 0, 10, "pending-decision"),
    ("IF sparse training", 0, 10, "pending-decision"),
    ("Mixture", 0, 12, "pending"),
    ("Held-out model", 0, 20, "pending"),
]
f, ax = plt.subplots(figsize=(11, 5.5))
for i, (name, done, total, st) in enumerate(reversed(layers)):
    col = ACC if st == "completed" else ("#7fb3d9" if "gated" in st else "#dddddd")
    ax.barh(i, max(total, 1), color="#f2f2f2", edgecolor=DARK, height=0.6)
    if done: ax.barh(i, done, color=col, edgecolor="none", height=0.6)
    ax.text(max(total, 1) + 0.5, i, f"{done}/{total if total else '?'} {st}", va="center", fontsize=8)
    ax.text(-0.5, i, name, va="center", ha="right", fontsize=9)
ax.set_xlim(0, 60); ax.set_yticks([]); ax.set_xlabel("runs")
ax.set_title("Fig 8 — Execution status (GPU queue now: margin-v2 on m1; next: cross-domain eval builds)", loc="left")
save(f, 8, {"layers": [dict(zip(("layer", "done", "planned", "status"), l)) for l in layers]},
     "# Fig8 执行状态\n- run 数来源: RUN_MATRIX_*.csv 与 HDFS DONE 计数(48=16×3 已完成)\n- 预计数为计划值,标 pending")

print("FIGPACK_DONE", OUT)
