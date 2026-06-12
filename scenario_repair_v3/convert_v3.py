"""Convert v3 data to LLaMA-Factory + build the experiment-specific training splits.

Produces:
  inject_lf.json                  knowledge floor (relay base)
  actionized_full_{train,eval}    Exp 1: all policies, actionized output
  cot_{train,eval}                Exp 1: plain CoT (no policy field) baseline
  per_policy/<policy>_train.json  Exp 2: targeted operator data (one policy only)
  cumulative/M<k>_train.json      Exp 3: cumulative curriculum stages
  control_random_train.json       Control 1: same-size random repair examples
  control_wrongtarget_train.json  Control 2: policies deliberately mismatched
  dataset_info.json               registers everything

Output schema (actionized policy format, v2.1-proven):
  {"update_decision","update_policy","repair_trace","final_answer"}
Abstain items emit final_answer: null.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scenario_repair_v3 import policies as P

REPAIR_INSTRUCTION = (
    "You are given a user's problem and a tentative answer that may be wrong. Decide whether to "
    "keep it, update it, or abstain, commit to the repair action, then give the final answer "
    "(or null if you must abstain). Return only valid JSON."
)
INJECT_INSTRUCTION = ("Answer from memory with only the answer. For a rule question, state the rule. "
                      "No explanation.")

# Cumulative curriculum order (M1..M6). M0 = inject only (no repair data).
CURRICULUM = [
    ("M1", ["keep_answer", "recompute"]),                 # decision + basic recall/recompute
    ("M2", ["override_wrong_claim"]),                     # + wrong-claim
    ("M3", ["verify_step"]),                              # + step verification
    ("M4", ["verify_bridge"]),                            # + bridge verification
    ("M5", ["use_provided_support"]),                     # + support use
    ("M6", ["retrieve_or_abstain"]),                      # + retrieve/abstain
]


def rinput(r):
    tent = "(none)" if r["tentative_answer"] is None else r["tentative_answer"]
    return f"Problem:\n{r['problem']}\n\nTentative answer:\n{tent}"


def actionized_out(r):
    return json.dumps({"update_decision": r["update_decision"],
                       "update_policy": r["policy"],
                       "repair_trace": r["repair_trace"],
                       "final_answer": r["final_answer"]}, ensure_ascii=False)


def cot_out(r):
    # plain CoT: strip the policy fields and the "Action: <p>." prefix
    trace = r["repair_trace"]
    if trace.startswith("Action:"):
        trace = trace.split(". ", 1)[1] if ". " in trace else trace
    return json.dumps({"repair_trace": trace, "final_answer": r["final_answer"]}, ensure_ascii=False)


def lf(r, out_fn, instr=REPAIR_INSTRUCTION):
    return {"instruction": instr, "input": rinput(r), "output": out_fn(r)}


def load(p):
    with p.open() as f:
        return [json.loads(l) for l in f if l.strip()]


def write(rows, p):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
    print(f"wrote {len(rows):5d} -> {p}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", type=Path, default=Path("data_v3"))
    ap.add_argument("--scaffold_per_policy", type=int, default=30,
                    help="fixed format-scaffold examples per policy mixed into every "
                         "targeted/control set (removes the format-learning confound)")
    args = ap.parse_args()
    a = args
    d = a.data_dir
    inj = load(d / "inject.jsonl")
    tr = load(d / "repair_train.jsonl")
    ev = load(d / "repair_eval.jsonl")
    rng = random.Random(99)

    # inject
    write([{"instruction": INJECT_INSTRUCTION, "input": r["question"], "output": r["answer"]}
           for r in inj], d / "inject_lf.json")

    # Exp 1: actionized full + cot baseline (train + eval)
    write([lf(r, actionized_out) for r in tr], d / "actionized_full_train.json")
    write([lf(r, actionized_out) for r in ev], d / "actionized_full_eval.json")
    write([lf(r, cot_out) for r in tr], d / "cot_train.json")
    write([lf(r, cot_out) for r in ev], d / "cot_eval.json")

    # ---- Format scaffold (v3 fix) ----
    # A single FIXED, policy-balanced base mixed into every targeted/control set so all
    # branches reach a trainable size and learn the JSON output format. It is IDENTICAL
    # across sets, so the differential signal between targeted sets is purely the target
    # policy's extra data — selectivity is preserved while the format confound is removed.
    # (Diagnosis: <=220-row single-policy sets produced 0-34% valid JSON; >=440 were fine.)
    by_policy = {p: [r for r in tr if r["policy"] == p] for p in P.OPERATOR_POLICIES}
    rng_sc = random.Random(2024)
    scaffold = []
    for p in P.POLICY_NAMES:
        pool = [r for r in tr if r["policy"] == p]
        scaffold += rng_sc.sample(pool, min(args.scaffold_per_policy, len(pool)))
    scaffold_ids = {r["id"] for r in scaffold}
    write([lf(r, actionized_out) for r in scaffold], d / "format_scaffold_train.json")
    print(f"format scaffold: {len(scaffold)} rows ({args.scaffold_per_policy}/policy), fixed across sets")

    # Exp 2: per-policy targeted = scaffold + that policy's data NOT already in scaffold.
    for pol, rows in by_policy.items():
        extra = [r for r in rows if r["id"] not in scaffold_ids]
        combined = scaffold + extra
        write([lf(r, actionized_out) for r in combined], d / "per_policy" / f"{pol}_train.json")
    # keep-only set (over-repair control operator), also scaffolded
    keep_rows = [r for r in tr if r["policy"] == "keep_answer" and r["id"] not in scaffold_ids]
    write([lf(r, actionized_out) for r in scaffold + keep_rows], d / "per_policy" / "keep_answer_train.json")

    # Exp 3: cumulative curriculum (accumulate policies)
    acc = []
    for tag, pols in CURRICULUM:
        acc = acc + [r for r in tr if r["policy"] in pols]
        write([lf(r, actionized_out) for r in acc], d / "cumulative" / f"{tag}_train.json")

    # Control 1: scaffold + same-COUNT random extra (ignoring policy) as the targeted extra.
    for pol, rows in by_policy.items():
        n_extra = len([r for r in rows if r["id"] not in scaffold_ids])
        pool = [r for r in tr if r["id"] not in scaffold_ids]
        sample = rng.sample(pool, min(n_extra, len(pool)))
        write([lf(r, actionized_out) for r in scaffold + sample], d / "controls" / f"random_{pol}_train.json")

    # Control 2: scaffold + wrong-target extra (that policy's data relabeled to a DIFFERENT policy).
    wrong_map = {P.OPERATOR_POLICIES[i]: P.OPERATOR_POLICIES[(i + 1) % len(P.OPERATOR_POLICIES)]
                 for i in range(len(P.OPERATOR_POLICIES))}
    for pol, rows in by_policy.items():
        wp = wrong_map[pol]
        relabeled = []
        for r in [x for x in rows if x["id"] not in scaffold_ids]:
            r2 = dict(r); r2["policy"] = wp; r2["update_decision"] = P.decision_of(wp)
            # rewrite the action prefix to the wrong action
            body = r["repair_trace"].split(". ", 1)[1] if ". " in r["repair_trace"] else r["repair_trace"]
            r2["repair_trace"] = f"Action: {P.action_of(wp)}. {body}"
            relabeled.append(r2)
        write([lf(r, actionized_out) for r in scaffold + relabeled],
              d / "controls" / f"wrongtarget_{pol}_train.json")
    (d / "controls" / "wrongtarget_map.json").write_text(json.dumps(wrong_map, indent=2))

    # dataset_info: register all train/eval files LF will load
    cols = {"prompt": "instruction", "query": "input", "response": "output"}
    info = {
        "v3_inject": "inject_lf.json",
        "v3_actionized_train": "actionized_full_train.json",
        "v3_actionized_eval": "actionized_full_eval.json",
        "v3_cot_train": "cot_train.json", "v3_cot_eval": "cot_eval.json",
        "v3_format_scaffold_train": "format_scaffold_train.json",
        # scaffold-only control: train on the 210-row balanced scaffold ALONE. This is
        # the true floor baseline for the selective matrix (every targeted set contains it).
        "v3_scaffold_only_train": "format_scaffold_train.json",
    }
    for pol in by_policy:
        info[f"v3_targeted_{pol}_train"] = f"per_policy/{pol}_train.json"
        info[f"v3_random_{pol}_train"] = f"controls/random_{pol}_train.json"
        info[f"v3_wrongtarget_{pol}_train"] = f"controls/wrongtarget_{pol}_train.json"
    info["v3_targeted_keep_answer_train"] = "per_policy/keep_answer_train.json"
    for tag, _ in CURRICULUM:
        info[f"v3_cumulative_{tag}_train"] = f"cumulative/{tag}_train.json"
    (d / "dataset_info.json").write_text(json.dumps(
        {k: {"file_name": v, "columns": cols} for k, v in info.items()}, indent=2))
    print(f"registered {len(info)} datasets -> {d/'dataset_info.json'}")


if __name__ == "__main__":
    main()
