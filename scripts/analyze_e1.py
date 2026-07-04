#!/usr/bin/env python3
"""E1 data-size sweep + E3 seed analysis (C-8 Batch-3 harvest).

Per run (cond, N, seed) x epoch{2,4,8,16}:
  repair-mode : parse rate, resist (w-items, strict-parsed, C-1), strict overall acc
  plain-mode  : genre split (ledger.genre), json_bleed, plain acc (marker-based)
  ridge point : min epoch with parse>=0.95 AND json_bleed<=5% AND mute<=12%
                (C-9 per LOOP_E1_RULINGS R-19: excess-mute<=5pp over the 7% base noise)
Report point per run = its ridge. Prereg gates (prereg/PREREG_datasize.md):
  P1 targeted N<=300 -> ridge resist >= 0.95 and json_bleed <= 5%
  P2 random any N    -> ridge resist in 0.4..0.95 (unstable)
  P3 ability flat    -> plain acc ~= 92% (+-5pp) and no systematic rise with N

Outputs: notes/NOTES_datasize.md, notes/fig_e1_datasize.png, notes/NOTES_seeds.md
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ledger.judge import load_items, load_preds, score_run  # noqa: E402
from ledger.genre import classify  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PRED = ROOT / "data_v4/epoch_sweep_predict"
EPOCHS = [2, 4, 8, 16]
NS = [100, 300, 1000, 3000]

items = load_items(ROOT / "data_v4/repair_eval.jsonl")
tref = [json.loads(l) for l in
        (ROOT / "data_v4/predict_outputs/predict_transfer_base/generated_predictions.jsonl").open()]


def plain_final(t):
    m = re.findall(r"final answer is\s*(-?[\d,\.]+)", t or "", re.I)
    return m[-1].replace(",", "").rstrip(".") if m else None


TGOLD = [plain_final(r["label"]) for r in tref]


def repair_metrics(tag):
    p = PRED / f"predict_{tag}/generated_predictions.jsonl"
    if not p.exists():
        return None
    v = score_run(items, load_preds(p), "v4")
    parse = sum(x["parsed_strict"] for x in v) / len(v)
    W = [x for x in v if x["resist"] is not None]
    resist = sum(x["resist"] for x in W) / len(W) if W else None
    overall = sum(x["correct_strict"] for x in v) / len(v)
    return dict(parse=parse, resist=resist, overall=overall, n_w=len(W))


def plain_metrics(tag):
    p = PRED / f"predict_transfer_{tag}/generated_predictions.jsonl"
    if not p.exists():
        return None
    preds = load_preds(p)
    n = len(preds)
    genres = [classify(t) for t in preds]
    bleed = sum(g == "json_bleed" for g in genres) / n
    mute = sum(g == "mute" for g in genres) / n
    acc = sum(1 for t, g in zip(preds, TGOLD) if plain_final(t) == g) / n
    return dict(json_bleed=bleed, mute=mute, plain_acc=acc)


def series(cond, n, s):
    rows = []
    for e in EPOCHS:
        tag = f"e1_{cond}_n{n}_s{s}_e{e}"
        r, t = repair_metrics(tag), plain_metrics(tag)
        if r and t:
            rows.append(dict(epoch=e, **r, **t))
    ridge = next((x for x in rows if x["parse"] >= 0.95 and x["json_bleed"] <= 0.05
                  and x["mute"] <= 0.12), None)   # C-9 third condition
    return rows, ridge


def pct(x):
    return f"{100*x:.0f}%" if x is not None else "—"


def main():
    # floor reference (canonical e8)
    fl = repair_metrics("scaffold_conv_e8")
    L = ["# NOTES_datasize (E1) — 原始数字 + 一句话读法", "",
         f"_judge=账本冻结口径;resist 在 w∩parsed 上(C-1);报告点=各 run 脊点(parse≥0.95∧json_bleed≤5%)。_",
         f"_floor 参照 scaffold_conv_e8:resist={pct(fl['resist'])}, overall={pct(fl['overall'])}._", "",
         "| cond | N | seed | 脊点 | resist@脊 | Δresist vs floor | bleed@脊 | 素题acc@脊 | overall@脊 |",
         "|---|---|---|---|---|---|---|---|---|"]
    fig_data = {}
    prereg = {"P1": [], "P2": [], "P3": []}
    for cond in ["targeted", "random"]:
        for n in NS:
            for s in ([42, 43, 44] if n == 300 else [42]):
                rows, ridge = series(cond, n, s)
                if ridge is None:
                    L.append(f"| {cond} | {n} | {s} | **无脊点** | — | — | — | — | — |")
                    detail = "; ".join(f"e{r['epoch']}:parse={pct(r['parse'])},bleed={pct(r['json_bleed'])}" for r in rows)
                    L.append(f"|  |  |  | ({detail}) |  |  |  |  |  |")
                    continue
                dr = ridge["resist"] - fl["resist"]
                L.append(f"| {cond} | {n} | {s} | e{ridge['epoch']} | {pct(ridge['resist'])} | "
                         f"{100*dr:+.0f}pp | {pct(ridge['json_bleed'])} | {pct(ridge['plain_acc'])} | {pct(ridge['overall'])} |")
                fig_data.setdefault((cond, s), []).append((n, ridge["resist"], ridge["plain_acc"]))
                if cond == "targeted" and n <= 300:
                    prereg["P1"].append((n, s, ridge["resist"] >= 0.95 and ridge["json_bleed"] <= 0.05,
                                         ridge["resist"], ridge["json_bleed"]))
                if cond == "random":
                    prereg["P2"].append((n, s, 0.4 <= ridge["resist"] <= 0.95, ridge["resist"]))
                prereg["P3"].append((cond, n, s, abs(ridge["plain_acc"] - 0.92) <= 0.05, ridge["plain_acc"]))

    L += ["", "## 预注册核对(prereg/PREREG_datasize.md)", ""]
    p1ok = all(ok for (_, _, ok, _, _) in prereg["P1"])
    L.append(f"- **P1 targeted N≤300 到位**: {'✅' if p1ok else '❌ 硬停'} — " +
             "; ".join(f"n{n}/s{s}: resist={pct(r)},bleed={pct(b)}" for (n, s, _, r, b) in prereg["P1"]))
    p2ok = all(ok for (_, _, ok, _) in prereg["P2"])
    L.append(f"- **P2 random 不稳定(0.4–0.95)**: {'✅' if p2ok else '❌ 与预注册矛盾 → 硬停报告'} — " +
             "; ".join(f"n{n}/s{s}: {pct(r)}" for (n, s, _, r) in prereg["P2"]))
    p3ok = all(ok for (*_, ok, _) in prereg["P3"])
    bad3 = [f"{c}/n{n}/s{s}:{pct(a)}" for (c, n, s, ok, a) in prereg["P3"] if not ok]
    L.append(f"- **P3 素题 acc 平(92±5pp)**: {'✅' if p3ok else '⚠️ 例外: ' + '; '.join(bad3)}")

    (ROOT / "notes/NOTES_datasize.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[-6:]))

    # fig
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    for (cond, s), pts in sorted(fig_data.items()):
        if s != 42:
            continue
        xs, rs, ps = zip(*sorted(pts))
        c = "#2a9d8f" if cond == "targeted" else "#f4a261"
        a1.plot(xs, rs, "o-", color=c, label=cond)
        a2.plot(xs, ps, "o-", color=c, label=cond)
    # seed spread at N=300
    for cond in ["targeted", "random"]:
        vals = [fig_data[(cond, s)] for s in [42, 43, 44] if (cond, s) in fig_data]
        r300 = [dict((n, r) for n, r, _ in v).get(300) for v in vals]
        r300 = [x for x in r300 if x is not None]
        if len(r300) > 1:
            c = "#2a9d8f" if cond == "targeted" else "#f4a261"
            a1.errorbar([300], [sum(r300)/len(r300)],
                        yerr=[[sum(r300)/len(r300)-min(r300)], [max(r300)-sum(r300)/len(r300)]],
                        color=c, capsize=4, fmt="none")
    a1.axhline(fl["resist"], color="grey", ls=":", label="floor e8")
    a1.set_xscale("log"); a1.set_xlabel("N (train examples)"); a1.set_title("resist @ ridge point")
    a2.axhline(0.92, color="grey", ls=":", label="pre-repair 92%")
    a2.set_xscale("log"); a2.set_xlabel("N"); a2.set_title("plain-genre acc @ ridge (no-bad-case check)")
    for a in (a1, a2):
        a.set_xticks(NS); a.set_xticklabels(NS); a.legend(fontsize=8); a.set_ylim(0, 1.05)
    fig.tight_layout(); fig.savefig(ROOT / "notes/fig_e1_datasize.png", dpi=150)

    # ---- E3 seeds ----
    L3 = ["# NOTES_seeds (E3) — headline 3-seed", "",
          "| cell (ridge pt) | seed | resist | overall strict |", "|---|---|---|---|"]
    for branch, e in [("scaffold_conv", 8), ("targeted_override_wrong_claim", 2), ("targeted_recompute", 3)]:
        for s, tag in [(42, f"{branch}_e{e}"), (43, f"e3_{branch}_e{e}_s43"), (44, f"e3_{branch}_e{e}_s44")]:
            m = repair_metrics(tag)
            if m:
                L3.append(f"| {branch}@e{e} | {s} | {pct(m['resist'])} | {pct(m['overall'])} |")
    (ROOT / "notes/NOTES_seeds.md").write_text("\n".join(L3) + "\n")
    print("notes + fig written")


if __name__ == "__main__":
    main()
