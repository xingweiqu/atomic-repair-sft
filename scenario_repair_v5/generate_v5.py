"""v5-clean generator: counterfactual two-hop repair items over the H-column operators.

Leak-proofing is built INTO generation (not post-hoc): train/eval share a coinage `used` set so
head/bridge/tail are globally unique -> eval (head,rel,tail) triples never appear in train.
Tail entities are balanced ~50/50 as true-value vs planted-false-value so no single-entity feature
predicts the decision. All values are coined nonsense (counterfactual), so the model must read
context — it cannot default-write the answer.

Operators (H-column, separable response paths):
  use_provided_support : full context -> compose two hops          (no planted wrong)
  verify_bridge        : wrong bridge claimed + distractor chain    (resist = not the wrong tail)
  override_wrong_claim : wrong final answer claimed                 (resist = not the wrong tail)
  keep_answer          : tentative correct (incl. 50/50 TRUE claim) (keep)
  retrieve_or_abstain  : one hop deleted -> unsolvable              (final null)
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

import v5_world as W

CELL_TO_POLICY = {
    "H-Sup": "use_provided_support",
    "H-Bridge": "verify_bridge",
    "H-Cor": "override_wrong_claim",
    "H-Cor-True": "keep_answer",
    "H-Clean": "keep_answer",
    "H-Abl": "retrieve_or_abstain",
}
CELLS = list(CELL_TO_POLICY)


def decision_of(policy):
    if policy == "keep_answer":
        return "keep"
    if policy == "retrieve_or_abstain":
        return "retrieve_or_abstain"
    return "update"


class TailBalancer:
    """Keep each tail's appearances as a planted-FALSE value ~50/50 vs its true appearances."""
    def __init__(self):
        self.false_ct = Counter()

    def pick_false(self, rng, pool, true_tail):
        cand = [t for t in pool if t != true_tail]
        cand.sort(key=lambda t: self.false_ct[t])
        # bias toward the least-used-as-false among the lowest third
        k = max(1, len(cand) // 3)
        pick = rng.choice(cand[:k])
        self.false_ct[pick] += 1
        return pick


def build_record(cell, c, idx, split, rng, bal):
    policy = CELL_TO_POLICY[cell]
    f = c["fam"]
    q = W.question(c)
    gold = c["tail"]
    ctx = W.context_full(c)
    tri = W.chain_triples(c)
    common = dict(id=f"{cell}_{split}_{idx:06d}", family=c["family"], failure_type=cell,
                  policy=policy, update_decision=decision_of(policy), split=split,
                  gold_symbolic_facts=tri)

    if cell == "H-Sup":
        return dict(**common, problem=q, oracle_facts=ctx, tentative_answer=None,
                    gold_answer=gold, planted_wrong_answer=None)

    if cell == "H-Clean":
        return dict(**common, problem=q, oracle_facts=ctx, tentative_answer=gold,
                    gold_answer=gold, planted_wrong_answer=None)

    if cell == "H-Cor-True":  # planted claim is TRUE -> keep (decoupling)
        prob = f"Reportedly the answer is {gold}. {q}"
        return dict(**common, problem=prob, oracle_facts=ctx, tentative_answer=gold,
                    gold_answer=gold, planted_wrong_answer=None)

    if cell == "H-Cor":  # wrong final-answer claim
        wt = bal.pick_false(rng, c["tails"], gold)
        prob = f"Reportedly the answer is {wt}. {q}"
        return dict(**common, problem=prob, oracle_facts=ctx, tentative_answer=wt,
                    gold_answer=gold, planted_wrong_answer=wt)

    if cell == "H-Bridge":  # wrong bridge + distractor chain so naive following gives wrong tail
        wb = W.coin(rng, 2)
        wt = bal.pick_false(rng, c["tails"], gold)
        prob = f"It is claimed that the {f['bridge_role']} of {c['head']} is {wb}. {q}"
        oracle = ctx + [f"{wb} {f['rel2']} {wt}."]  # distractor: wrong bridge -> wrong tail
        return dict(**common, problem=prob, oracle_facts=oracle, tentative_answer=wt,
                    gold_answer=gold, planted_wrong_answer=wt)

    if cell == "H-Abl":  # delete the bridge->tail hop -> unsolvable
        return dict(**common, problem=q, oracle_facts=[ctx[0]], tentative_answer=None,
                    gold_answer=None, planted_wrong_answer=None)

    raise ValueError(cell)


def build_split(chains, split, rng):
    bal = TailBalancer()
    out = []
    # round-robin operators across chains; -True first so balancer sees keeps too
    order = sorted(CELLS, key=lambda c: 0 if c.endswith("-True") else 1)
    idxc = {c: 0 for c in CELLS}
    for i, c in enumerate(chains):
        cell = order[i % len(order)]
        out.append(build_record(cell, c, idxc[cell], split, rng, bal))
        idxc[cell] += 1
    rng.shuffle(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_dir", type=Path, default=Path("data_v5"))
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--train_chains_per_family", type=int, default=200)
    ap.add_argument("--eval_chains_per_family", type=int, default=75)
    ap.add_argument("--tails_per_family", type=int, default=40)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    used = set()  # shared -> global uniqueness across splits
    tr_chains = W.build_world(rng, a.train_chains_per_family, a.tails_per_family, used)
    ev_chains = W.build_world(rng, a.eval_chains_per_family, a.tails_per_family, used)
    tr = build_split(tr_chains, "train", rng)
    ev = build_split(ev_chains, "eval", rng)
    a.out_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in (("repair_train", tr), ("repair_eval", ev)):
        with (a.out_dir / f"{name}.jsonl").open("w") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(tr)} train / {len(ev)} eval -> {a.out_dir}")


if __name__ == "__main__":
    main()
