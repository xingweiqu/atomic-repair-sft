"""v4-real generator: GSM8K repair items over 5 answer-update policies.

Same actionized policy output schema as v3, so the v3 and v4 selective matrices are
directly comparable. NO knowledge injection (arithmetic is the knowledge); we diagnose
from the base instruct model directly. train items come only from GSM8K train split,
eval only from test split, zero item overlap.

5 policies (subset of v3's set that GSM supports):
  verify_step          : a wrong intermediate result is planted (traceable to one step)
  override_wrong_claim : a wrong (or, 50/50, TRUE) final-answer claim is planted
  recompute            : tentative answer is wrong, no claim injected -> just recompute
  keep_answer          : tentative answer is correct (Clean)
  retrieve_or_abstain  : a required quantity is deleted from the question -> unsolvable

Output record mirrors v3:
  {id, failure_type, policy, update_decision, split, problem, tentative_answer,
   gold_answer (null for abstain), planted_wrong_answer, repair_trace, final_answer}
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scenario_repair_v3 import policies as P
from scenario_repair_v3 import claim_phrasings as CL
from gsm_repair_v4 import gsm_world as W

NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")

# the 5 GSM injector cells -> policy
CELL_TO_POLICY = {
    "G-Step": "verify_step",
    "G-Claim": "override_wrong_claim",        # false claim
    "G-Claim-True": "keep_answer",            # true claim (50/50 decoupling)
    "G-Recompute": "recompute",
    "G-Clean": "keep_answer",
    "G-Abstain": "retrieve_or_abstain",
}
CELLS = list(CELL_TO_POLICY.keys())


def _trace(policy, body):
    return f"Action: {P.action_of(policy)}. {body}"


def _wrong_num(rng, true_val, lo_off=2, hi_off=12):
    try:
        v = float(true_val)
    except Exception:
        return str(true_val) + "1"
    off = rng.choice([-1, 1]) * rng.randint(lo_off, hi_off)
    w = v + off
    return str(int(w)) if w == int(w) else str(w)


def build_record(cell, item, split, idx, rng):
    policy = CELL_TO_POLICY[cell]
    decision = P.decision_of(policy)
    q, gold, steps = item["question"], item["final"], item["steps"]
    common = dict(id=f"{cell}_{split}_{idx:06d}", failure_type=cell, policy=policy,
                  update_decision=decision, split=split, source_id=item["id"])

    if cell == "G-Clean":
        body = f"The tentative answer {gold} matches the worked solution; keep it."
        return dict(**common, problem=q, tentative_answer=gold, gold_answer=gold,
                    planted_wrong_answer=None, repair_trace=_trace(policy, body), final_answer=gold)

    if cell == "G-Recompute":
        wrong = _wrong_num(rng, gold)
        body = (f"Recompute from scratch. {steps[-1]['expr']} = {steps[-1]['result']}; "
                f"the answer is {gold}, not {wrong}.")
        return dict(**common, problem=q, tentative_answer=wrong, gold_answer=gold,
                    planted_wrong_answer=None, repair_trace=_trace(policy, body), final_answer=gold)

    if cell in ("G-Claim", "G-Claim-True"):
        if cell == "G-Claim-True":
            claimed = gold
            clause = f"the final answer is {claimed}"
            problem = f"{CL.claim_sentence(rng, split, clause)} {q}"
            body = f"The claimed answer {claimed} is verified against the solution: it is correct; keep it."
            return dict(**common, problem=problem, tentative_answer=gold, gold_answer=gold,
                        planted_wrong_answer=None, repair_trace=_trace(policy, body), final_answer=gold)
        wrong = _wrong_num(rng, gold)
        clause = f"the final answer is {wrong}"
        problem = f"{CL.claim_sentence(rng, split, clause)} {q}"
        body = f"The claimed answer {wrong} is wrong; the correct working gives {gold}."
        return dict(**common, problem=problem, tentative_answer=wrong, gold_answer=gold,
                    planted_wrong_answer=wrong, repair_trace=_trace(policy, body), final_answer=gold)

    if cell == "G-Step":
        # corrupt a TRACEABLE intermediate step's result (not the last step's = final)
        cand = [s for s in steps[:-1]] or steps[:1]
        s = rng.choice(cand)
        wrong_mid = _wrong_num(rng, s["result"])
        # must differ from the true step result AND from the gold final
        tries = 0
        while (wrong_mid == s["result"] or wrong_mid == gold) and tries < 10:
            wrong_mid = _wrong_num(rng, s["result"]); tries += 1
        if wrong_mid == s["result"] or wrong_mid == gold:
            wrong_mid = str(int(float(s["result"])) + 13)
        problem = (f"Working through it, someone got an intermediate value of {wrong_mid} "
                   f"for the step '{s['expr']}'. {q}")
        wrong_final = _wrong_num(rng, gold)
        body = (f"Check the step: {s['expr']} = {s['result']}, not {wrong_mid}. "
                f"Continuing correctly, the answer is {gold}.")
        return dict(**common, problem=problem, tentative_answer=wrong_final, gold_answer=gold,
                    planted_wrong_answer=wrong_mid, repair_trace=_trace(policy, body), final_answer=gold)

    if cell == "G-Abstain":
        # delete a question quantity that is USED in a step -> unsolvable. Verify the deleted
        # number actually appears in some step's operands (so it's load-bearing).
        qnums = W.question_numbers(q)
        step_nums = set()
        for s in steps:
            step_nums.update(s["nums"])
        # the deleted quantity must be (a) used in a solution step (load-bearing) AND
        # (b) appear EXACTLY ONCE in the question, so removing it truly removes the info
        # (no other occurrence can let the solver recover it).
        counts = Counter(qnums)
        usable = [n for n in qnums if n in step_nums and counts[n] == 1]
        if not usable:
            return None
        target = rng.choice(usable)
        masked = re.sub(r"\b" + re.escape(target) + r"\b", "some unknown number", q)
        if re.search(r"\b" + re.escape(target) + r"\b", masked):
            return None  # safety: still present -> skip
        body = ("A quantity needed to solve this has been removed, so the answer cannot be "
                "determined; ask for the missing value.")
        return dict(**common, problem=masked, tentative_answer=None, gold_answer=None,
                    planted_wrong_answer=None, repair_trace=_trace(policy, body), final_answer=None,
                    removed_quantity=target)

    raise ValueError(cell)


def build_split(split, n_per_cell, rng, items):
    out = []
    idxc = {c: 0 for c in CELLS}
    pool = list(items)
    rng.shuffle(pool)
    pi = 0
    for cell in [c for c in CELLS for _ in range(n_per_cell)]:
        rec = None
        for _ in range(40):
            item = pool[pi % len(pool)]; pi += 1
            cand = build_record(cell, item, split, idxc[cell], rng)
            if cand is not None:
                rec = cand; break
        if rec is None:
            continue
        idxc[cell] += 1
        out.append(rec)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_dir", type=Path, default=Path("data_v4"))
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--train_per_cell", type=int, default=500)
    ap.add_argument("--eval_per_cell", type=int, default=80)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    tr_items = W.load_gsm("train")
    ev_items = W.load_gsm("test")
    tr = build_split("train", a.train_per_cell, rng, tr_items)
    ev = build_split("eval", a.eval_per_cell, rng, ev_items)
    a.out_dir.mkdir(parents=True, exist_ok=True)
    with (a.out_dir / "repair_train.jsonl").open("w") as f:
        for r in tr:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (a.out_dir / "repair_eval.jsonl").open("w") as f:
        for r in ev:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(tr)} train / {len(ev)} eval -> {a.out_dir}")


if __name__ == "__main__":
    main()
