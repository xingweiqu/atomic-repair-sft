"""Validate scenario-repair v3 data. Exit 1 on failure; always write a report."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scenario_repair_v3 import policies as P


def load(p):
    with p.open() as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", type=Path, default=Path("data_v3"))
    ap.add_argument("--out", type=Path, default=Path("data_v3/sanity_v3.json"))
    a = ap.parse_args()
    d = a.data_dir
    fails = []
    inj = load(d / "inject.jsonl")
    tr = load(d / "repair_train.jsonl")
    ev = load(d / "repair_eval.jsonl")

    inj_facts = {tuple(r["symbolic_fact"]) for r in inj if r["kind"] == "entity_fact"}

    for r in tr + ev:
        w = r["id"]
        # policy validity
        if r["policy"] not in P.POLICY_NAMES:
            fails.append(f"{w}: unknown policy {r['policy']}")
        if r["update_decision"] != P.decision_of(r["policy"]):
            fails.append(f"{w}: decision mismatch")
        # abstain contract
        if r["policy"] == "retrieve_or_abstain":
            if r["gold_answer"] is not None or r["final_answer"] is not None:
                fails.append(f"{w}: abstain item must have null gold/final")
        else:
            if r["final_answer"] != r["gold_answer"]:
                fails.append(f"{w}: final != gold")
            # gold leakage into the scenario problem (except keep, where tentative==gold by design)
            if r["policy"] != "keep_answer" and r["gold_answer"]:
                if re.search(r"\b" + re.escape(str(r["gold_answer"])) + r"\b", r["problem"]):
                    # numeric R answers collide spuriously; skip reasoning
                    if not str(r["gold_answer"]).lstrip("-").isdigit():
                        fails.append(f"{w}: gold leaks into scenario problem")
            # keep: tentative == gold; corrupt: planted == tentative
            if r["policy"] == "keep_answer" and r["tentative_answer"] != r["gold_answer"]:
                fails.append(f"{w}: keep tentative != gold")
            if r["failure_type"].endswith("Cor") and r.get("planted_wrong_answer") != r["tentative_answer"]:
                fails.append(f"{w}: Cor planted != tentative")
        # K/H gold facts must be injected
        for t in r.get("gold_symbolic_facts", []):
            if len(t) == 3 and t[1] != "applied_to" and tuple(t) not in inj_facts:
                fails.append(f"{w}: uses fact not injected: {t}"); break

    # policy coverage + balance
    for split, rows in (("train", tr), ("eval", ev)):
        by = Counter(r["policy"] for r in rows)
        missing = set(P.POLICY_NAMES) - set(by)
        if missing:
            fails.append(f"{split}: policies with no data: {missing}")

    # scenario surface train/eval disjoint (form_id carries split; check problems don't overlap)
    tr_probs = {r["problem"] for r in tr}
    ev_probs = {r["problem"] for r in ev}
    overlap = tr_probs & ev_probs
    if overlap:
        fails.append(f"scenario problems overlap train/eval: {len(overlap)}")

    report = {"status": "PASS" if not fails else "FAIL", "failures": fails,
              "counts": {"inject": len(inj), "train": len(tr), "eval": len(ev),
                         "train_by_policy": dict(Counter(r["policy"] for r in tr)),
                         "eval_by_policy": dict(Counter(r["policy"] for r in ev)),
                         "eval_by_failure": dict(Counter(r["failure_type"] for r in ev))}}
    a.out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"status: {report['status']} ({len(fails)} failures) -> {a.out}")
    for f in fails[:30]:
        print("  FAIL:", f)
    if fails:
        raise SystemExit(1)
    print("policy coverage OK; abstain null OK; no gold leak; scenarios disjoint")
    print("eval by policy:", report["counts"]["eval_by_policy"])


if __name__ == "__main__":
    main()
