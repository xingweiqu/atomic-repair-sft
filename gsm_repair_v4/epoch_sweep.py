"""Epoch-sweep analysis for v4 (GSM). Epoch is the only variable.

Question: are the v4 conclusions (decision induced, ability not) real at LOW epoch (~single pass,
extrapolable to realistic training), or artifacts of the convergent high-epoch setting?

For every (branch, epoch) ckpt decoded on v4_actionized_eval we report, on the branch's OWN cell:
  parse_rate     : valid-JSON fraction (separates "format not learned" from "learned but unable")
  resist_wrong   : among committed, final != tentative/planted wrong  (DECISION layer)
  final_acc      : final == gold over the whole cell (coupled metric)
  ability_fixed  : final == gold on a FIXED same-difficulty subset S (constant denominator across
                   all epochs/branches on that cell -> the §6.1 denominator-bias fix). S = cell
                   items COMMITTED by every plotted ckpt; ability_fixed isolates arithmetic from
                   the shifting resisted set.

Headline figure (fig_epoch_sweep.png): override_wrong_claim cell. Solid = targeted_override
(resist / ability_fixed / final_acc vs epoch); dashed = random_override (resist / final_acc).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from gsm_repair_v4.evaluate_gsm import load_jsonl, parse, numkey, final_field

# branch -> own cell. scaffold_conv is the floor; we read it on the override cell for reference.
BRANCH_CELL = {
    "scaffold_conv": "override_wrong_claim",
    "targeted_override_wrong_claim": "override_wrong_claim",
    "targeted_recompute": "recompute",
    "targeted_verify_step": "verify_step",
    "random_override_wrong_claim": "override_wrong_claim",
}
EPOCHS = [1, 2, 3, 8, 30]


def preds(pred_root, branch, ep):
    p = Path(pred_root) / f"predict_{branch}_e{ep}" / "generated_predictions.jsonl"
    return [r.get("predict", "") for r in load_jsonl(p)] if p.exists() else None


def resisted_set(P, src, cell):
    """Indices in `cell` the model RESISTED (committed a value != tentative/planted wrong).

    The fixed same-difficulty subset is the intersection of these across all ckpts, so the
    decision is held SUCCESSFUL for every ckpt on that subset -> differences there are pure
    arithmetic, not decision. (Committed-but-not-resisted items would re-couple the decision,
    because on these cells gold != the wrong value.)"""
    s = set()
    for i, r in enumerate(src):
        if r["policy"] != cell:
            continue
        fa = numkey(final_field(parse(P[i]), P[i]))
        if fa is None:
            continue
        bad = {numkey(r["tentative_answer"])}
        if r.get("planted_wrong_answer"):
            bad.add(numkey(r["planted_wrong_answer"]))
        if fa not in bad:
            s.add(i)
    return s


def cell_metrics(P, src, cell, fixed):
    """resist_wrong (committed denom), final_acc (full cell), ability_fixed (on `fixed` subset)."""
    idx = [i for i, r in enumerate(src) if r["policy"] == cell]
    parse_ok = committed = resisted = correct = 0
    for i in idx:
        r, raw = src[i], P[i]
        o = parse(raw)
        if o is not None:
            parse_ok += 1
        fa = numkey(final_field(o, raw))
        if fa is None:
            continue
        committed += 1
        bad = {numkey(r["tentative_answer"])}
        if r.get("planted_wrong_answer"):
            bad.add(numkey(r["planted_wrong_answer"]))
        if fa == numkey(r["gold_answer"]):
            correct += 1
        if fa not in bad:
            resisted += 1
    fix_ok = fix_n = 0
    for i in fixed:
        fa = numkey(final_field(parse(P[i]), P[i]))
        fix_n += 1
        if fa == numkey(src[i]["gold_answer"]):
            fix_ok += 1
    rt = lambda a, b: round(a / b, 4) if b else None
    return {"n": len(idx), "parse_rate": rt(parse_ok, len(idx)), "committed": committed,
            "resist_wrong": rt(resisted, committed), "final_acc": rt(correct, len(idx)),
            "ability_fixed": rt(fix_ok, fix_n), "fixed_n": fix_n}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred", type=Path, default=Path("data_v4/epoch_sweep_predict"))
    ap.add_argument("--eval", type=Path, default=Path("data_v4/repair_eval.jsonl"))
    ap.add_argument("--out", type=Path, default=Path("data_v4/results"))
    a = ap.parse_args()
    src = load_jsonl(a.eval)
    a.out.mkdir(parents=True, exist_ok=True)

    # load all available (branch, epoch) predictions
    loaded = {}
    for b in BRANCH_CELL:
        for ep in EPOCHS:
            P = preds(a.pred, b, ep)
            if P is not None:
                loaded[(b, ep)] = P

    # FIXED same-difficulty subset per cell = items RESISTED by EVERY loaded ckpt touching that
    # cell (decision held successful for all -> ability there is pure arithmetic, constant denom).
    fixed_by_cell = {}
    for cell in set(BRANCH_CELL.values()):
        sets = [resisted_set(P, src, cell) for (b, ep), P in loaded.items() if BRANCH_CELL[b] == cell]
        fixed_by_cell[cell] = set.intersection(*sets) if sets else set()

    rows = {}
    for (b, ep), P in sorted(loaded.items()):
        cell = BRANCH_CELL[b]
        rows[f"{b}_e{ep}"] = {"branch": b, "epoch": ep, "cell": cell,
                              **cell_metrics(P, src, cell, fixed_by_cell[cell])}
    (a.out / "epoch_sweep_v4.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False))

    # ---- headline figure: override_wrong_claim cell ----
    def series(branch, key):
        xs, ys = [], []
        for ep in EPOCHS:
            r = rows.get(f"{branch}_e{ep}")
            if r and r[key] is not None:
                xs.append(ep); ys.append(r[key])
        return xs, ys

    fig, ax = plt.subplots(figsize=(7, 4.6))
    tg = "targeted_override_wrong_claim"; rn = "random_override_wrong_claim"
    specs = [(tg, "resist_wrong", "o-", "#1f77b4", "targeted: resist_wrong (decision)"),
             (tg, "ability_fixed", "s-", "#d62728", "targeted: ability|resist, fixed subset (arithmetic)"),
             (tg, "final_acc", "^-", "#2ca02c", "targeted: final_acc (coupled)"),
             (rn, "resist_wrong", "o--", "#1f77b4", "random: resist_wrong"),
             (rn, "final_acc", "^--", "#2ca02c", "random: final_acc")]
    for branch, key, style, color, label in specs:
        xs, ys = series(branch, key)
        if xs:
            ax.plot(xs, ys, style, color=color, label=label, alpha=0.9, markersize=6)
    ax.set_xscale("log"); ax.set_xticks(EPOCHS); ax.set_xticklabels([str(e) for e in EPOCHS])
    ax.set_xlabel("training epochs (log scale)"); ax.set_ylabel("rate")
    ax.set_ylim(-0.02, 1.02); ax.grid(True, alpha=0.3)
    ax.set_title("v4 epoch sweep — override_wrong_claim cell\ndecision vs arithmetic vs coupled")
    ax.legend(fontsize=8, loc="center right")
    fig.tight_layout(); fig.savefig(a.out / "fig_epoch_sweep.png", dpi=150)
    print("wrote", a.out / "fig_epoch_sweep.png")

    # ---- report ----
    L = ["# v4 epoch sweep — extrapolability of the decision-vs-ability split", "",
         "Epoch is the only variable (full-param SFT, seed 42, all else == round-1 v4). "
         "Each ckpt decoded on v4_actionized_eval (480). `ability|resist fixed` = final==gold on a "
         "FIXED subset S = items RESISTED by every ckpt on that cell (decision held successful for "
         "all -> pure arithmetic, constant denominator; the §6.1 denominator-bias fix).", "",
         "## Per-branch, per-epoch (branch's OWN cell)", "",
         "| branch | epoch | cell | parse | resist_wrong | ability\\|resist fixed (n) | final_acc |",
         "|---|---|---|---|---|---|---|"]
    for k, r in sorted(rows.items(), key=lambda kv: (kv[1]["branch"], kv[1]["epoch"])):
        L.append(f"| {r['branch']} | {r['epoch']} | {r['cell']} | {r['parse_rate']} | "
                 f"**{r['resist_wrong']}** | {r['ability_fixed']} ({r['fixed_n']}) | {r['final_acc']} |")
    L += ["", "![epoch sweep](fig_epoch_sweep.png)", "",
          "## Conclusion (fill from the curve)", "",
          "- decision (resist_wrong) appears at epoch: __",
          "- ability_fixed across epochs: __ (expected ~flat ≈ base arithmetic ceiling)",
          "- overfit / non-extrapolable region begins at epoch: __",
          "- targeted vs random at low epoch (1–2): __ (specificity present? or only at high epoch?)",
          "", "## Extrapolability statement", "",
          "_Based on the curve: which conclusions hold at low epoch (extrapolate to near-single-pass "
          "real training) vs which are convergent-setting artifacts (controlled diagnosis only)._"]
    (a.out / "epoch_sweep_v4.md").write_text("\n".join(L) + "\n")
    print("wrote", a.out / "epoch_sweep_v4.md")


if __name__ == "__main__":
    main()
