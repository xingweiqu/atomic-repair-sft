"""Validate atomic-repair v2 data. Exit 1 on failure; always write a report.

v2 contract:
  - 10 cells at expected counts (9 atomic + Clean).
  - final_answer == gold; Clean tentative==gold & should_repair False;
    non-Clean tentative != gold; Cor cells carry planted_wrong_answer==tentative.
  - diagnosis/repair_skill match CELL_SPEC_V2.
  - Knowledge coverage: every K/H repair gold fact is in inject.jsonl.
  - Inputs carry NO oracle facts EXCEPT H-Aug (Augment = provide cue, by design)
    and the bridge fact must NOT leak into K/R/H-Cor/Abl problems.
  - Reasoning is not memorised: repair_eval R operands differ from repair_train R
    operands (different number pairs).
  - Form ids disjoint train/eval.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import forms_v2 as F
import reasoning_world_v2 as R

EXPECT = {"train": {c: 200 for c in F.CELLS_9} | {"Clean": 200},
          "eval": {c: 60 for c in F.CELLS_9} | {"Clean": 60}}


def load(p):
    with p.open() as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", type=Path, default=Path("data_v2"))
    ap.add_argument("--out", type=Path, default=Path("data_v2/sanity_v2.json"))
    a = ap.parse_args()
    d = a.data_dir
    fails = []
    inj = load(d / "inject.jsonl")
    tr = load(d / "repair_train.jsonl")
    ev = load(d / "repair_eval.jsonl")

    # counts
    for split, rows in (("train", tr), ("eval", ev)):
        by = Counter(r["cell"] for r in rows)
        for c, n in EXPECT[split].items():
            if by.get(c, 0) != n:
                fails.append(f"{split} {c}: {by.get(c,0)} != {n}")

    # per-record contract
    for r in tr + ev:
        w = r["id"]
        if r["final_answer"] != r["gold_answer"]:
            fails.append(f"{w}: final != gold")
        sp = F.CELL_SPEC_V2[r["cell"]]
        if r["diagnosis"] != sp["diagnosis"] or r["repair_skill"] != sp["repair_skill"]:
            fails.append(f"{w}: diag/skill mismatch")
        if r["cell"] == "Clean":
            if r["tentative_answer"] != r["gold_answer"]:
                fails.append(f"{w}: Clean tentative != gold")
        else:
            if r["tentative_answer"] == r["gold_answer"]:
                fails.append(f"{w}: non-Clean tentative == gold")
        if r["cell"].endswith("Cor"):
            if r.get("planted_wrong_answer") != r["tentative_answer"]:
                fails.append(f"{w}: Cor planted != tentative")

    # knowledge coverage (K/H gold facts injected)
    inj_tri = {tuple(r["symbolic_fact"]) for r in inj if r["kind"] == "entity_fact"}
    need = set()
    for r in tr + ev:
        if r["domain"] in ("K", "H", "-"):
            for t in r.get("gold_symbolic_facts", []):
                if len(t) == 3 and t[1] != "applied_to":
                    need.add(tuple(t))
    miss = need - inj_tri
    if miss:
        fails.append(f"coverage: {len(miss)} K/H facts not injected")

    # rule coverage: every R item's op rule is injected
    inj_ops = {r["op"] for r in inj if r["kind"] == "rule_fact"}
    r_ops = {r["relation_family"].replace("reason_", "") for r in tr + ev if r["domain"] == "R"}
    if not r_ops <= inj_ops:
        fails.append(f"rule coverage: ops {r_ops - inj_ops} not injected")

    # no-leak: gold must not appear in problem (except H-Aug by design).
    # Skip R domain: numeric answers collide spuriously with operands/scaffold digits;
    # R has its own non-leak guarantee (operands are the inputs, not the answer).
    for r in tr + ev:
        if r["cell"] == "H-Aug" or r["domain"] == "R" or r["cell"] == "Clean":
            continue  # H-Aug provides cue by design; R numeric collisions are spurious
        if re.search(r"\b" + re.escape(r["gold_answer"]) + r"\b", r["problem"]):
            fails.append(f"{r['id']}: gold leaks into problem")

    # reasoning not memorised: train vs eval operand pairs disjoint
    def rpairs(rows):
        out = set()
        for r in rows:
            if r["domain"] == "R":
                m = re.search(r"of (\-?\d+) and (\-?\d+)", r["problem"])
                if m:
                    out.add((r["relation_family"], m.group(1), m.group(2)))
        return out
    overlap = rpairs(tr) & rpairs(ev)
    if overlap:
        fails.append(f"reasoning operand overlap train/eval: {len(overlap)} (memorisation risk)")

    # form disjointness
    def fids(rows):
        return {r["form_id"] for r in rows}
    fo = fids(tr) & fids(ev)
    if fo:
        fails.append(f"form_id train∩eval not empty: {sorted(fo)}")

    report = {"status": "PASS" if not fails else "FAIL", "failures": fails,
              "counts": {"inject": len(inj), "repair_train": len(tr), "repair_eval": len(ev),
                         "injected_entity_facts": len(inj_tri), "injected_ops": len(inj_ops),
                         "kh_facts_needed": len(need)},
              "reasoning_operand_overlap": len(overlap)}
    a.out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"status: {report['status']} ({len(fails)} failures) -> {a.out}")
    for f in fails[:30]:
        print("  FAIL:", f)
    if fails:
        raise SystemExit(1)
    print(f"coverage: {len(need)} K/H facts ⊆ {len(inj_tri)} injected; {len(inj_ops)} rules injected")
    print(f"reasoning operands train/eval disjoint; form ids disjoint")


if __name__ == "__main__":
    main()
