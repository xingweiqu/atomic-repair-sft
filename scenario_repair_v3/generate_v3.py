"""Scenario-repair v3 generator.

Reuses the v2 synthetic world (entities + invented reasoning ops) and the failure-
injection idioms, but: (a) wraps each problem in a natural user SCENARIO surface, and
(b) emits an answer-update POLICY instead of a 9-cell skill label. The 9 cells survive
only as `failure_type` (how the item was broken). Adds a new injector U-Abl
(underspecified / missing anchor) whose correct policy is retrieve_or_abstain.

Output record (per item):
  id, failure_type (cell), policy, update_decision, scenario_family, split, form_id,
  problem (scenario-wrapped), tentative_answer, gold_answer (null for abstain),
  planted_wrong_answer, repair_trace (actionized), final_answer, oracle_facts,
  gold_symbolic_facts

No API needed (seed scenarios); --use-api adds cached LLM paraphrase of the surface only.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root for v2 imports
import generate_repair_data as v0
import reasoning_world_v2 as R

from . import policies as P
from . import scenario_templates as S
from . import claim_phrasings as CL
from .scenario_api import ScenarioRewriter

FACT_Q = {
    "written_by": "Who wrote {h}?", "nationality": "What is the nationality of {h}?",
    "located_in": "Which country is {h} located in?", "uses_currency": "What currency does {h} use?",
    "founded_by": "Who founded {h}?", "made_by": "Which company makes {h}?",
    "headquartered_in": "In which country is {h} headquartered?",
    "created_by": "Who created {h}?", "birth_country": "In which country was {h} born?",
    "known_for": "What is {h} known for?", "field": "Which scientific field does {h} belong to?",
}

# Injectors. 9 v2 cells + U-Abl (abstain) + v3.1 Cor-True variants (claim is TRUE -> keep).
# Cor-True get the SAME count as their Cor-False counterpart, so within the marked-claim
# population true:false is exactly 50/50 (220 K-Cor-True : 220 K-Cor), decoupling the
# surface marker from the truth value.
INJECTORS = ["K-Aug", "K-Abl", "K-Cor", "K-Cor-True", "R-Aug", "R-Abl", "R-Cor",
             "H-Aug", "H-Cor", "H-Cor-True", "U-Abl", "Clean"]

# per-(split) target counts per injector (balanced across the 7 policies downstream)
TARGETS = {
    "train": {c: 220 for c in INJECTORS},
    "eval":  {c: 60 for c in INJECTORS},
}


def _pick(rng, pool, banned):
    x = rng.choice(pool); t = 0
    while x == banned and t < 30:
        x = rng.choice(pool); t += 1
    return x


def _kh_base(fam, edge, domain):
    g = v0.build_family_graph(fam)
    r1, r2 = g["relations"]
    h, b, t = edge["head"], edge["bridge"], edge["tail"]
    if domain == "H":
        tpl = v0.FAMILIES[fam]["templates_train"][0]["natural"]
        return tpl.format(head=h), t, dict(head=h, bridge=b, tail=t, r1=r1, r2=r2,
                                           fact1=v0.first_fact_sentence(fam, h, b),
                                           fact2=v0.second_fact_sentence(fam, b, t))
    q = FACT_Q[r2].format(h=b)
    return q, t, dict(head=b, bridge=b, tail=t, r1=r2, r2=r2,
                      fact1=v0.second_fact_sentence(fam, b, t),
                      fact2=v0.second_fact_sentence(fam, b, t))


def _scenario(rw, family, split, bare_q, banned, rng):
    seed = rng.choice(S.family_scenarios(family, split)).format(q=bare_q)
    return rw.rewrite(seed, banned)


def _trace(policy, body):
    return f"Action: {P.action_of(policy)}. {body}"


def build_record(*, cell, split, rng, idx, kh_graphs, r_pool, rw):
    policy = P.CELL_TO_POLICY[cell]
    decision = P.decision_of(policy)
    common = dict(id=f"{cell}_{split}_{idx:06d}", failure_type=cell, policy=policy,
                  update_decision=decision, split=split, form_split=split)

    # ---- U-Abl: underspecified, no anchor -> abstain ----
    if cell == "U-Abl":
        seed = rng.choice(S.underspecified_scenarios(split))
        problem = rw.rewrite(seed, banned=[])
        body = ("The problem does not identify which specific entity is meant, so the "
                "answer cannot be produced from internal knowledge; ask for clarification.")
        return dict(**common, scenario_family="underspecified", form_id=f"uabl_{split}",
                    problem=problem, tentative_answer=None, gold_answer=None,
                    planted_wrong_answer=None, repair_trace=_trace(policy, body),
                    final_answer=None, oracle_facts=[], gold_symbolic_facts=[])

    # ---- Reasoning injectors (R-Aug/R-Abl/R-Cor) ----
    if cell.startswith("R-"):
        item = r_pool[idx % len(r_pool)]
        op, a, b, gold = item["op"], item["a"], item["b"], item["gold"]
        bare = f"Compute the {op} of {a} and {b}."
        rule = item["rule_statement"]; steps = item["steps"]
        banned = [gold]
        problem_core = bare
        if cell == "R-Cor":
            import re as _re
            nums = _re.findall(r"-?\d+", steps[0]); true_mid = int(nums[-1]) if nums else 0
            wmid = true_mid + 7
            if wmid == int(gold): wmid += 1
            problem_core = f"Someone got an intermediate value of {wmid} here. {bare}"
            wrong = str(int(gold) + 3)
            body = f"The intermediate {wmid} is wrong. Correctly: {steps[0]}; {steps[1]}. The answer is {gold}."
        else:  # R-Aug / R-Abl -> recompute
            wrong = str(int(gold) + 1)
            body = (f"Recall the rule: {rule} Then {steps[0]}; {steps[1]}. The answer is {gold}.")
        problem = rng.choice(S.reasoning_scenarios(split)).format(q=problem_core)
        problem = rw.rewrite(problem, banned)
        return dict(**common, scenario_family=f"reason_{op}", form_id=f"{cell}_{split}",
                    problem=problem, tentative_answer=wrong, gold_answer=gold,
                    planted_wrong_answer=(wrong if cell == "R-Cor" else None),
                    repair_trace=_trace(policy, body), final_answer=gold,
                    oracle_facts=[rule], gold_symbolic_facts=[[op, "applied_to", f"{a},{b}"]])

    # ---- Knowledge / Hybrid injectors ----
    eff = "H" if cell.startswith("H-") else "K"
    if cell == "Clean":
        eff = "H" if rng.random() < 0.5 else "K"
    fam = v0.FAMILY_NAMES[idx % len(v0.FAMILY_NAMES)]
    g = kh_graphs[fam]
    edge = g["edges"][idx % len(g["edges"])]
    base_q, gold, ctx = _kh_base(fam, edge, eff)
    banned = [gold]

    if cell == "Clean":
        problem = _scenario(rw, fam, split, base_q, banned, rng)
        body = f"The tentative answer is already supported: {ctx['fact1']} Keep it."
        gsf = ([[ctx["head"], ctx["r1"], ctx["bridge"]], [ctx["bridge"], ctx["r2"], ctx["tail"]]]
               if eff == "H" else [[ctx["head"], ctx["r1"], ctx["tail"]]])
        return dict(**common, scenario_family=fam, form_id=f"clean_{split}",
                    problem=problem, tentative_answer=gold, gold_answer=gold,
                    planted_wrong_answer=None, repair_trace=_trace(policy, body),
                    final_answer=gold, oracle_facts=[ctx["fact1"]], gold_symbolic_facts=gsf)

    if cell in ("K-Aug", "K-Abl"):
        problem = _scenario(rw, fam, split, base_q, banned, rng)
        wrong = _pick(rng, g["tails"], gold)
        body = f"Recall the stored fact: {ctx['fact1']} Therefore the answer is {gold}."
        return dict(**common, scenario_family=fam, form_id=f"{cell}_{split}",
                    problem=problem, tentative_answer=wrong, gold_answer=gold,
                    planted_wrong_answer=None, repair_trace=_trace(policy, body),
                    final_answer=gold, oracle_facts=[ctx["fact1"]],
                    gold_symbolic_facts=[[ctx["head"], ctx["r1"], ctx["tail"]]])

    if cell in ("K-Cor", "K-Cor-True"):
        if cell == "K-Cor-True":
            # planted claim is TRUE (== gold); correct action is verify + keep.
            claimed = gold
            clause = f"the answer is {claimed}"
            core = f"{CL.claim_sentence(rng, split, clause)} {base_q}"
            problem = _scenario(rw, fam, split, core, banned=[], rng=rng)  # gold may appear (it's the claim)
            body = f"The claim '{claimed}' is verified against the known fact: {ctx['fact1']} It is correct, so keep it."
            return dict(**common, scenario_family=fam, form_id=f"{cell}_{split}",
                        problem=problem, tentative_answer=gold, gold_answer=gold,
                        planted_wrong_answer=None, repair_trace=_trace(policy, body),
                        final_answer=gold, oracle_facts=[ctx["fact1"]],
                        gold_symbolic_facts=[[ctx["head"], ctx["r1"], ctx["tail"]]])
        wrong = _pick(rng, g["tails"], gold)
        clause = f"the answer is {wrong}"
        core = f"{CL.claim_sentence(rng, split, clause)} {base_q}"
        problem = _scenario(rw, fam, split, core, banned, rng)
        body = f"The claim '{wrong}' contradicts the known fact: {ctx['fact1']} The answer is {gold}, not {wrong}."
        return dict(**common, scenario_family=fam, form_id=f"{cell}_{split}",
                    problem=problem, tentative_answer=wrong, gold_answer=gold,
                    planted_wrong_answer=wrong, repair_trace=_trace(policy, body),
                    final_answer=gold, oracle_facts=[ctx["fact1"]],
                    gold_symbolic_facts=[[ctx["head"], ctx["r1"], ctx["tail"]]])

    if cell == "H-Aug":  # bridge fact provided -> use_provided_support
        core = f"{ctx['fact1']} {base_q}"
        problem = _scenario(rw, fam, split, core, banned, rng)
        wrong = _pick(rng, g["tails"], gold)
        body = f"The bridge fact is given: {ctx['fact1']} Apply it: {ctx['fact2']} The answer is {gold}."
        return dict(**common, scenario_family=fam, form_id=f"{cell}_{split}",
                    problem=problem, tentative_answer=wrong, gold_answer=gold,
                    planted_wrong_answer=None, repair_trace=_trace(policy, body),
                    final_answer=gold, oracle_facts=[ctx["fact1"], ctx["fact2"]],
                    gold_symbolic_facts=[[ctx["head"], ctx["r1"], ctx["bridge"]],
                                         [ctx["bridge"], ctx["r2"], ctx["tail"]]])

    if cell in ("H-Cor", "H-Cor-True"):  # planted bridge -> verify_bridge (false) / keep (true)
        if cell == "H-Cor-True":
            # planted bridge is the TRUE bridge; verify and keep.
            clause = v0.first_fact_sentence(fam, ctx["head"], ctx["bridge"]).rstrip(".")
            core = f"{CL.claim_sentence(rng, split, clause)} {base_q}"
            problem = _scenario(rw, fam, split, core, banned=[gold], rng=rng)
            body = (f"The stated bridge is verified: {ctx['fact1']} Then {ctx['fact2']} "
                    f"It is correct, so the answer is {gold}; keep it.")
            return dict(**common, scenario_family=fam, form_id=f"{cell}_{split}",
                        problem=problem, tentative_answer=gold, gold_answer=gold,
                        planted_wrong_answer=None, repair_trace=_trace(policy, body),
                        final_answer=gold, oracle_facts=[ctx["fact1"], ctx["fact2"]],
                        gold_symbolic_facts=[[ctx["head"], ctx["r1"], ctx["bridge"]],
                                             [ctx["bridge"], ctx["r2"], ctx["tail"]]])
        wrong_bridge = _pick(rng, g["bridges"], ctx["bridge"])
        wb_edge = next((e for e in g["edges"] if e["bridge"] == wrong_bridge), None)
        wrong_tail = wb_edge["tail"] if wb_edge else _pick(rng, g["tails"], gold)
        if wrong_tail == gold:
            wrong_tail = _pick(rng, g["tails"], gold)
        # v3.1: keep normal case (NO .lower()), varied intro -> marker != falsity.
        clause = v0.first_fact_sentence(fam, ctx["head"], wrong_bridge).rstrip(".")
        core = f"{CL.claim_sentence(rng, split, clause)} {base_q}"
        problem = _scenario(rw, fam, split, core, [gold], rng)
        body = f"The planted bridge is false: actually {ctx['fact1']} Then {ctx['fact2']} So the answer is {gold}, not {wrong_tail}."
        return dict(**common, scenario_family=fam, form_id=f"{cell}_{split}",
                    problem=problem, tentative_answer=wrong_tail, gold_answer=gold,
                    planted_wrong_answer=wrong_tail, repair_trace=_trace(policy, body),
                    final_answer=gold, oracle_facts=[ctx["fact1"], ctx["fact2"]],
                    gold_symbolic_facts=[[ctx["head"], ctx["r1"], ctx["bridge"]],
                                         [ctx["bridge"], ctx["r2"], ctx["tail"]]])

    raise ValueError(cell)


def build_inject():
    """Knowledge floor (identical to v2): 345 entity facts + 6 rules."""
    rows, i = [], 0
    for fam in v0.FAMILY_NAMES:
        g = v0.build_family_graph(fam); r1, r2 = g["relations"]
        s1, s2 = set(), set()
        for e in g["edges"]:
            if e["head"] not in s1:
                s1.add(e["head"])
                rows.append({"id": f"inj_{i:05d}", "kind": "entity_fact", "relation": r1,
                             "question": FACT_Q[r1].format(h=e["head"]), "answer": e["bridge"],
                             "symbolic_fact": [e["head"], r1, e["bridge"]]}); i += 1
            if e["bridge"] not in s2:
                s2.add(e["bridge"])
                rows.append({"id": f"inj_{i:05d}", "kind": "entity_fact", "relation": r2,
                             "question": FACT_Q[r2].format(h=e["bridge"]), "answer": e["tail"],
                             "symbolic_fact": [e["bridge"], r2, e["tail"]]}); i += 1
    for rf in R.all_rule_facts():
        rows.append({"id": f"inj_{i:05d}", "kind": "rule_fact", "op": rf["op"],
                     "question": f"How do you compute the {rf['op']} of two numbers?",
                     "answer": rf["rule_statement"],
                     "symbolic_fact": [rf["op"], "rule_is", rf["rule_short"]]}); i += 1
    return rows


def build_all(rng, rw):
    kh = {fam: v0.build_family_graph(fam) for fam in v0.FAMILY_NAMES}
    r_tr, r_ev = R.build_reasoning_split(random.Random(7), n_train_per_op=60, n_eval_per_op=30)
    out = {"train": [], "eval": []}
    for split in ("train", "eval"):
        r_pool = r_tr if split == "train" else r_ev
        idxc = {c: 0 for c in INJECTORS}
        seen = set()
        order = []
        planned = {c: 0 for c in INJECTORS}
        for _ in range(max(TARGETS[split].values())):
            for c in INJECTORS:
                if planned[c] < TARGETS[split][c]:
                    order.append(c); planned[c] += 1
        for cell in order:
            rec = None
            for att in range(60):
                cand = build_record(cell=cell, split=split, rng=rng, idx=idxc[cell] + att,
                                    kh_graphs=kh, r_pool=r_pool, rw=rw)
                key = (cand["problem"], str(cand["tentative_answer"]))
                if key not in seen:
                    seen.add(key); rec = cand; break
            if rec is None:
                cand["problem"] += f"  (#{idxc[cell]})"; rec = cand
            idxc[cell] += 1
            out[split].append(rec)
    return out["train"], out["eval"]


def _w(rows, path):
    with path.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows):5d} -> {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_dir", type=Path, default=Path("data_v3"))
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--use-api", action="store_true", help="paraphrase scenario surface via claude CLI")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    rw = ScenarioRewriter(use_api=a.use_api)

    inject = build_inject()
    tr, ev = build_all(rng, rw)
    rw.flush()
    print("scenario rewrite stats:", rw.stats)

    a.out_dir.mkdir(parents=True, exist_ok=True)
    _w(inject, a.out_dir / "inject.jsonl")
    _w(tr, a.out_dir / "repair_train.jsonl")
    _w(ev, a.out_dir / "repair_eval.jsonl")


if __name__ == "__main__":
    main()
