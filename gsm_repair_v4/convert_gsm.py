"""Convert v4-real GSM data to LLaMA-Factory + experiment splits.

Mirrors scenario_repair_v3.convert_v3 but for the GSM domain and the 5 GSM policies.
No knowledge injection (arithmetic is the knowledge), so targeted/control sets relay from
the BASE instruct model, not an inject checkpoint. Uses the same actionized output schema
as v3 for cross-domain comparison.

Outputs: actionized_full / cot / per-policy targeted / same-size random / wrong-target /
format scaffold + scaffold_only, plus an un-perturbed GSM transfer eval (clean test items).
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scenario_repair_v3 import policies as P
from gsm_repair_v4 import gsm_world as W

REPAIR_INSTRUCTION = (
    "You are given a math word problem and a tentative answer that may be wrong. Decide "
    "whether to keep it, update it, or abstain, commit to the repair action, then give the "
    "final answer (or null if you must abstain). Return only valid JSON."
)
GSM_POLICIES = ["verify_step", "override_wrong_claim", "recompute", "retrieve_or_abstain"]  # operators
ALL_POLICIES = GSM_POLICIES + ["keep_answer"]
SCAFFOLD_PER_POLICY = 40


def rinput(r):
    tent = "(none)" if r["tentative_answer"] is None else r["tentative_answer"]
    return f"Problem:\n{r['problem']}\n\nTentative answer:\n{tent}"


def actionized_out(r):
    return json.dumps({"update_decision": r["update_decision"], "update_policy": r["policy"],
                       "repair_trace": r["repair_trace"], "final_answer": r["final_answer"]},
                      ensure_ascii=False)


def cot_out(r):
    tr = r["repair_trace"]
    if tr.startswith("Action:"):
        tr = tr.split(". ", 1)[1] if ". " in tr else tr
    return json.dumps({"repair_trace": tr, "final_answer": r["final_answer"]}, ensure_ascii=False)


def lf(r, out_fn):
    return {"instruction": REPAIR_INSTRUCTION, "input": rinput(r), "output": out_fn(r)}


def load(p):
    with p.open() as f:
        return [json.loads(l) for l in f if l.strip()]


def write(rows, p):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
    print(f"wrote {len(rows):5d} -> {p}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", type=Path, default=Path("data_v4"))
    a = ap.parse_args()
    d = a.data_dir
    tr = load(d / "repair_train.jsonl")
    ev = load(d / "repair_eval.jsonl")
    rng = random.Random(99)

    write([lf(r, actionized_out) for r in tr], d / "actionized_full_train.json")
    write([lf(r, actionized_out) for r in ev], d / "actionized_full_eval.json")
    write([lf(r, cot_out) for r in tr], d / "cot_train.json")
    write([lf(r, cot_out) for r in ev], d / "cot_eval.json")

    # format scaffold (fixed, policy-balanced)
    rsc = random.Random(2024)
    scaffold = []
    for p in ALL_POLICIES:
        pool = [r for r in tr if r["policy"] == p]
        scaffold += rsc.sample(pool, min(SCAFFOLD_PER_POLICY, len(pool)))
    scaffold_ids = {r["id"] for r in scaffold}
    write([lf(r, actionized_out) for r in scaffold], d / "format_scaffold_train.json")

    by_policy = {p: [r for r in tr if r["policy"] == p] for p in GSM_POLICIES}
    for pol, rows in by_policy.items():
        extra = [r for r in rows if r["id"] not in scaffold_ids]
        write([lf(r, actionized_out) for r in scaffold + extra], d / "per_policy" / f"{pol}_train.json")
    # controls
    for pol, rows in by_policy.items():
        n_extra = len([r for r in rows if r["id"] not in scaffold_ids])
        pool = [r for r in tr if r["id"] not in scaffold_ids]
        samp = rng.sample(pool, min(n_extra, len(pool)))
        write([lf(r, actionized_out) for r in scaffold + samp], d / "controls" / f"random_{pol}_train.json")
    wrong_map = {GSM_POLICIES[i]: GSM_POLICIES[(i + 1) % len(GSM_POLICIES)] for i in range(len(GSM_POLICIES))}
    for pol, rows in by_policy.items():
        wp = wrong_map[pol]
        rel = []
        for r in [x for x in rows if x["id"] not in scaffold_ids]:
            r2 = dict(r); r2["policy"] = wp; r2["update_decision"] = P.decision_of(wp)
            body = r["repair_trace"].split(". ", 1)[1] if ". " in r["repair_trace"] else r["repair_trace"]
            r2["repair_trace"] = f"Action: {P.action_of(wp)}. {body}"
            rel.append(r2)
        write([lf(r, actionized_out) for r in scaffold + rel], d / "controls" / f"wrongtarget_{pol}_train.json")

    # transfer eval: un-perturbed GSM test items. We allow step-by-step reasoning (GSM needs
    # CoT; suppressing it would tank BOTH base and repaired models and make the "did repair
    # hurt the base task" comparison meaningless) and require a fixed final-answer line so the
    # numeric answer is recoverable from free-form generations. The reference output is the
    # gold reasoning trajectory + that final line: a normal, non-trivial SFT reference (a bare
    # numeric reference was being dropped by LLaMA-Factory's supervised processor as invalid).
    clean = W.load_gsm("test", limit=300)
    transfer = [{"instruction": ("Solve the math word problem. Reason step by step, then end "
                                 "with a line exactly in the form 'The final answer is N.'"),
                 "input": r["question"],
                 "output": f"{r['reasoning'].strip()}\nThe final answer is {r['final']}."}
                for r in clean]
    write(transfer, d / "transfer_eval.json")

    # dataset_info
    cols = {"prompt": "instruction", "query": "input", "response": "output"}
    info = {"v4_actionized_train": "actionized_full_train.json",
            "v4_actionized_eval": "actionized_full_eval.json",
            "v4_cot_train": "cot_train.json", "v4_cot_eval": "cot_eval.json",
            "v4_scaffold_only_train": "format_scaffold_train.json",
            "v4_transfer_eval": "transfer_eval.json"}
    for pol in by_policy:
        info[f"v4_targeted_{pol}_train"] = f"per_policy/{pol}_train.json"
        info[f"v4_random_{pol}_train"] = f"controls/random_{pol}_train.json"
        info[f"v4_wrongtarget_{pol}_train"] = f"controls/wrongtarget_{pol}_train.json"
    (d / "dataset_info.json").write_text(json.dumps(
        {k: {"file_name": v, "columns": cols} for k, v in info.items()}, indent=2))
    print(f"registered {len(info)} datasets")


if __name__ == "__main__":
    main()
