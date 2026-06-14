"""Decision-level vs arithmetic-level decomposition of the v4 repair matrix.

Motivation (reviewer): final-answer accuracy on GSM COUPLES two things — (a) the repair DECISION
(resist the planted wrong value / don't keep a wrong tentative) and (b) re-COMPUTING the right
answer (real arithmetic, capped by base ability). A negative final-answer diagonal can therefore
hide a successful decision induction. This script separates them per cell:

  parse_rate       : fraction with valid JSON (exposes format collapse, e.g. the underfit floor)
  committed_rate   : produced a concrete final_answer (in-domain there is ~no abstention drift)
  resist_wrong     : among committed, fraction NOT equal to tentative/planted (= decision works)
  arith_given_ok   : among committed AND resisted, fraction equal to gold (= pure arithmetic)
  final_acc        : the original coupled metric, for reference

It also prints a decision-level selective matrix (rows = trained operator, cols = eval cell,
value = resist_wrong) and treats abstain separately (it is a format/decision skill, not an
ability — see report note).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from gsm_repair_v4.evaluate_gsm import load_jsonl, parse, numkey, final_field, is_abstain_strict

UPD_CELLS = ["verify_step", "recompute", "override_wrong_claim"]


def preds_of(pred_dir, name):
    p = Path(pred_dir) / f"predict_{name}" / "generated_predictions.jsonl"
    return [r.get("predict", "") for r in load_jsonl(p)] if p.exists() else None


def cell_stats(preds, src, cell):
    idx = [i for i, r in enumerate(src) if r["policy"] == cell]
    n = len(idx)
    parse_ok = committed = resisted = resisted_correct = correct = 0
    for i in idx:
        r, raw = src[i], preds[i]
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
        g = numkey(r["gold_answer"])
        if fa == g:
            correct += 1
        if fa not in bad:
            resisted += 1
            if fa == g:
                resisted_correct += 1
    rt = lambda a, b: round(a / b, 3) if b else None
    return {"n": n, "parse_rate": rt(parse_ok, n), "committed_rate": rt(committed, n),
            "no_answer_rate": rt(n - committed, n), "resist_wrong": rt(resisted, committed),
            "arith_given_ok": rt(resisted_correct, resisted), "final_acc": rt(correct, n)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred", type=Path, default=Path("data_v4/predict_outputs"))
    ap.add_argument("--eval", type=Path, default=Path("data_v4/repair_eval.jsonl"))
    ap.add_argument("--floor", default="scaffold_only", help="floor run name (use scaffold_conv once trained)")
    ap.add_argument("--out", type=Path, default=Path("data_v4/results/decision_analysis"))
    a = ap.parse_args()
    src = load_jsonl(a.eval)

    runs = {"floor": a.floor, "full": "actionized_full"}
    for op in UPD_CELLS:
        runs[f"tgt_{op}"] = f"targeted_{op}"
    P = {k: preds_of(a.pred, v) for k, v in runs.items()}

    L = [f"# v4 decision-level analysis (floor = {a.floor})", "",
         "`final_acc` couples decision + arithmetic. `resist_wrong` = decision only "
         "(committed answers not equal to the planted/tentative wrong value). "
         "`arith_given_ok` = arithmetic on the resisted subset.", ""]
    for cell in UPD_CELLS:
        L += [f"## cell: {cell}", "",
              "| run | parse | committed | no-answer | resist_wrong (decision) | arith_given_ok | final_acc |",
              "|---|---|---|---|---|---|---|"]
        for k in ["floor", f"tgt_{cell}", "full"]:
            if P.get(k) is None:
                continue
            s = cell_stats(P[k], src, cell)
            L.append(f"| {runs[k]} | {s['parse_rate']} | {s['committed_rate']} | {s['no_answer_rate']} | "
                     f"**{s['resist_wrong']}** | {s['arith_given_ok']} | {s['final_acc']} |")
        L.append("")

    # decision-level selective matrix: rows trained op, cols eval cell, value = resist_wrong
    L += ["## Decision-level selective matrix — resist_wrong (rows=trained op, cols=eval cell)", "",
          "| trained \\ eval | " + " | ".join(c[:10] for c in UPD_CELLS) + " |",
          "|" + "---|" * (len(UPD_CELLS) + 1)]
    dump = {"floor_run": a.floor, "cells": {}, "matrix": {}}
    for top in UPD_CELLS:
        row = []
        for ec in UPD_CELLS:
            pr = P.get(f"tgt_{top}")
            v = cell_stats(pr, src, ec)["resist_wrong"] if pr else None
            row.append("n/a" if v is None else f"{v:.2f}")
            dump["matrix"][f"{top}->{ec}"] = v
        L.append(f"| {top[:14]} | " + " | ".join(row) + " |")
    for k in P:
        dump["cells"][runs[k]] = {c: cell_stats(P[k], src, c) for c in UPD_CELLS} if P[k] else None

    # abstain treated separately
    ab_idx = [i for i, r in enumerate(src) if r["policy"] == "retrieve_or_abstain"]
    L += ["", "## abstain (treated SEPARATELY — a decision/format skill, not an ability)", "",
          "Reported as abstain-correct (strict). Not comparable to the compute cells above; it is "
          "a positive control showing the loop fires on a capacity the base lacks.", "",
          "| run | abstain-correct |", "|---|---|"]
    for k, name in [("floor", a.floor), ("full", "actionized_full"),
                    ("tgt_abstain", "targeted_retrieve_or_abstain"),
                    ("rand_abstain", "random_retrieve_or_abstain"),
                    ("wrong_abstain", "wrongtarget_retrieve_or_abstain")]:
        pr = preds_of(a.pred, name)
        if pr is None:
            continue
        ok = sum(is_abstain_strict(parse(pr[i]), pr[i]) for i in ab_idx)
        L.append(f"| {name} | {round(ok/len(ab_idx),3)} |")

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.with_suffix(".md").write_text("\n".join(L))
    a.out.with_suffix(".json").write_text(json.dumps(dump, indent=2, ensure_ascii=False))
    print("wrote", a.out.with_suffix(".md"))
    print("\n".join(L))


if __name__ == "__main__":
    main()
