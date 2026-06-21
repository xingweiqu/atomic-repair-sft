"""Convert v5-clean data to LLaMA-Factory + experiment splits. Mirrors convert_gsm (v4) so the
two domains are scored identically. Counterfactual domain -> relay from BASE (facts in context).

Input to the model includes the CONTEXT (the model must read it; values are counterfactual).
Output is the same actionized schema as v3/v4.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

REPAIR_INSTRUCTION = (
    "You are given context facts, a question, and a tentative answer that may be wrong. Use ONLY "
    "the context. Decide whether to keep it, update it, or abstain, commit to the repair action, "
    "then give the final answer (or null if the context is insufficient). Return only valid JSON.")
V5_POLICIES = ["use_provided_support", "verify_bridge", "override_wrong_claim", "retrieve_or_abstain"]
ALL_POLICIES = V5_POLICIES + ["keep_answer"]
SCAFFOLD_PER_POLICY = 200


def decision_of(p):
    return {"keep_answer": "keep", "retrieve_or_abstain": "retrieve_or_abstain"}.get(p, "update")


def action_of(p):
    return p.replace("_", " ")


def rinput(r):
    ctx = "\n".join(r["oracle_facts"])
    tent = "(none)" if r["tentative_answer"] is None else r["tentative_answer"]
    return f"Context:\n{ctx}\n\nQuestion:\n{r['problem']}\n\nTentative answer:\n{tent}"


def actionized_out(r):
    return json.dumps({"update_decision": r["update_decision"], "update_policy": r["policy"],
                       "repair_trace": r["repair_trace"], "final_answer": r["final_answer"]},
                      ensure_ascii=False)


def lf(r):
    return {"instruction": REPAIR_INSTRUCTION, "input": rinput(r), "output": actionized_out(r)}


def load(p):
    return [json.loads(l) for l in p.open() if l.strip()]


def write(rows, p):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
    print(f"wrote {len(rows):5d} -> {p}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", type=Path, default=Path("data_v5"))
    a = ap.parse_args()
    d = a.data_dir
    tr, ev = load(d / "repair_train.jsonl"), load(d / "repair_eval.jsonl")
    rng = random.Random(99)

    write([lf(r) for r in tr], d / "actionized_full_train.json")
    write([lf(r) for r in ev], d / "actionized_full_eval.json")

    rsc = random.Random(2024)
    scaffold = []
    for p in ALL_POLICIES:
        pool = [r for r in tr if r["policy"] == p]
        scaffold += rsc.sample(pool, min(SCAFFOLD_PER_POLICY, len(pool)))
    sids = {r["id"] for r in scaffold}
    write([lf(r) for r in scaffold], d / "scaffold_only_train.json")

    by = {p: [r for r in tr if r["policy"] == p] for p in V5_POLICIES}
    for pol, rows in by.items():
        extra = [r for r in rows if r["id"] not in sids]
        write([lf(r) for r in scaffold + extra], d / "per_policy" / f"{pol}_train.json")
    for pol, rows in by.items():
        n_extra = len([r for r in rows if r["id"] not in sids])
        pool = [r for r in tr if r["id"] not in sids]
        write([lf(r) for r in scaffold + rng.sample(pool, min(n_extra, len(pool)))],
              d / "controls" / f"random_{pol}_train.json")
    wrong_map = {V5_POLICIES[i]: V5_POLICIES[(i + 1) % len(V5_POLICIES)] for i in range(len(V5_POLICIES))}
    for pol, rows in by.items():
        wp = wrong_map[pol]
        rel = []
        for r in [x for x in rows if x["id"] not in sids]:
            r2 = dict(r); r2["policy"] = wp; r2["update_decision"] = decision_of(wp)
            body = r["repair_trace"].split(". ", 1)[1] if ". " in r["repair_trace"] else r["repair_trace"]
            r2["repair_trace"] = f"Action: {action_of(wp)}. {body}"
            rel.append(r2)
        write([lf(r) for r in scaffold + rel], d / "controls" / f"wrongtarget_{pol}_train.json")

    cols = {"prompt": "instruction", "query": "input", "response": "output"}
    info = {"v5_actionized_train": "actionized_full_train.json",
            "v5_actionized_eval": "actionized_full_eval.json",
            "v5_scaffold_only_train": "scaffold_only_train.json"}
    for pol in by:
        info[f"v5_targeted_{pol}_train"] = f"per_policy/{pol}_train.json"
        info[f"v5_random_{pol}_train"] = f"controls/random_{pol}_train.json"
        info[f"v5_wrongtarget_{pol}_train"] = f"controls/wrongtarget_{pol}_train.json"
    (d / "dataset_info.json").write_text(json.dumps(
        {k: {"file_name": v, "columns": cols} for k, v in info.items()}, indent=2))
    print(f"registered {len(info)} datasets")


if __name__ == "__main__":
    main()
