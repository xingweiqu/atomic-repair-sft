"""Atomic-repair v2 generator — 9 cells (K/R/H x Aug/Abl/Cor) + knowledge injection.

Three stages (see SPEC_v2.md):
  1. inject.jsonl    : ALL atomic facts (K/H entity facts + R rule statements).
                       train == eval (deliberate overfit; the knowledge floor).
  2. repair_train / repair_eval : 9-cell perturbed two-hop/one-hop items. Inputs
                       give NO oracle facts / NO bridge — the model must use the
                       injected knowledge. Held-out FORM (perturbation phrasing).
  3. (convert_v2 emits the CoT / CoT+skill / zero-shot training formats.)

Reuses v0 synthetic world (generate_repair_data) for K/H, reasoning_world_v2 for R,
forms_v2 for the 9-cell perturbation phrasings + repair_skill spec.

Pure-Python, deterministic, no API, oracle-verifiable.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

import generate_repair_data as v0
import reasoning_world_v2 as R
import forms_v2 as F

CELLS_9 = F.CELLS_9

REPAIR_TARGETS = {
    "train": {c: 200 for c in CELLS_9} | {"Clean": 200},
    "eval":  {c: 60 for c in CELLS_9} | {"Clean": 60},
}


# --------------------------------------------------------------------------- #
# Knowledge injection set (stage 1). train == eval (overfit floor).
# --------------------------------------------------------------------------- #
FACT_Q = {  # one canonical question phrasing per relation (injection = memorise)
    "written_by": "Who wrote {h}?", "nationality": "What is the nationality of {h}?",
    "located_in": "Which country is {h} located in?", "uses_currency": "What currency does {h} use?",
    "founded_by": "Who founded {h}?", "made_by": "Which company makes {h}?",
    "headquartered_in": "In which country is {h} headquartered?",
    "created_by": "Who created {h}?", "birth_country": "In which country was {h} born?",
    "known_for": "What is {h} known for?", "field": "Which scientific field does {h} belong to?",
}


def build_inject(rng: random.Random) -> list[dict]:
    rows, i = [], 0
    # K/H entity facts: all 345 single-hop facts from v0 world.
    for fam in v0.FAMILY_NAMES:
        g = v0.build_family_graph(fam)
        r1, r2 = g["relations"]
        seen1, seen2 = set(), set()
        for e in g["edges"]:
            if e["head"] not in seen1:
                seen1.add(e["head"])
                rows.append({"id": f"inj_{i:05d}", "kind": "entity_fact", "relation": r1,
                             "question": FACT_Q[r1].format(h=e["head"]), "answer": e["bridge"],
                             "symbolic_fact": [e["head"], r1, e["bridge"]]}); i += 1
            if e["bridge"] not in seen2:
                seen2.add(e["bridge"])
                rows.append({"id": f"inj_{i:05d}", "kind": "entity_fact", "relation": r2,
                             "question": FACT_Q[r2].format(h=e["bridge"]), "answer": e["tail"],
                             "symbolic_fact": [e["bridge"], r2, e["tail"]]}); i += 1
    # R rule statements: one per invented operation (memorise the rule).
    for rf in R.all_rule_facts():
        rows.append({"id": f"inj_{i:05d}", "kind": "rule_fact", "op": rf["op"],
                     "question": f"How do you compute the {rf['op']} of two numbers?",
                     "answer": rf["rule_statement"],
                     "symbolic_fact": [rf["op"], "rule_is", rf["rule_short"]]}); i += 1
    return rows


# --------------------------------------------------------------------------- #
# Repair items (stage 2). 9 cells. NO facts/bridge in the input.
# --------------------------------------------------------------------------- #
def _pick(rng, pool, banned):
    x = rng.choice(pool); t = 0
    while x == banned and t < 30:
        x = rng.choice(pool); t += 1
    return x


def _kh_base(rng, fam, edge, domain):
    """Base question + gold for a K (1-hop) or H (2-hop) item from v0 world."""
    g = v0.build_family_graph(fam)
    r1, r2 = g["relations"]
    h, b, t = edge["head"], edge["bridge"], edge["tail"]
    if domain == "H":
        q = v0.first_fact_sentence.__self__ if False else None
        # 2-hop question via v0 template natural form
        tpl = v0.FAMILIES[fam]["templates_train"][0]["natural"]
        return tpl.format(head=h), t, dict(head=h, bridge=b, tail=t, r1=r1, r2=r2,
                                           fact1=v0.first_fact_sentence(fam, h, b),
                                           fact2=v0.second_fact_sentence(fam, b, t))
    else:  # K: 1-hop, ask bridge->tail directly about the bridge entity
        q = FACT_Q[r2].format(h=b)
        return q, t, dict(head=b, bridge=b, tail=t, r1=r2, r2=r2,
                          fact1=v0.second_fact_sentence(fam, b, t),
                          fact2=v0.second_fact_sentence(fam, b, t))


def build_repair_record(*, cell, split, rng, idx, kh_graphs, r_items_pool):
    spec = F.CELL_SPEC_V2[cell]
    domain = spec["domain"]
    bank = F.CELL_BANK[cell]
    form = rng.choice(bank[split])
    common = dict(id=f"{cell}_{split}_{idx:06d}", cell=cell, domain=domain,
                  diagnosis=spec["diagnosis"], repair_skill=spec["repair_skill"],
                  should_repair=spec["should_repair"], split=split,
                  entity_split="shared", form_id=form["id"], form_split=split)

    if domain in ("K", "H", "-"):  # Clean uses K/H world too
        eff_domain = "H" if (domain == "-" and rng.random() < 0.5) else ("K" if domain == "-" else domain)
        fam = v0.FAMILY_NAMES[idx % len(v0.FAMILY_NAMES)]
        g = kh_graphs[fam]
        edge = g["edges"][idx % len(g["edges"])]
        base_q, gold, ctx = _kh_base(rng, fam, edge, eff_domain)
        common["relation_family"] = fam

        if cell == "Clean":
            problem = form["tpl"].format(q=base_q)
            trace = f"The facts support the answer: {ctx['fact1']} So the tentative answer '{gold}' is correct; no repair needed."
            # Gold chain depends on whether this Clean item is K (1-hop) or H (2-hop).
            if eff_domain == "H":
                gsf = [[ctx["head"], ctx["r1"], ctx["bridge"]], [ctx["bridge"], ctx["r2"], ctx["tail"]]]
            else:
                gsf = [[ctx["head"], ctx["r1"], ctx["tail"]]]  # head==bridge for K
            return dict(**common, problem=problem, tentative_answer=gold, gold_answer=gold,
                        planted_wrong_answer=None, repair_trace=trace, final_answer=gold,
                        oracle_facts=[ctx["fact1"]], gold_symbolic_facts=gsf)

        if cell == "K-Aug":
            problem = form["tpl"].format(q=base_q)
            wrong = _pick(rng, g["tails"], gold)
            trace = f"The tentative answer is unsupported. Surface the stored fact: {ctx['fact1']} Therefore the answer is {gold}."
            return dict(**common, problem=problem, tentative_answer=wrong, gold_answer=gold,
                        planted_wrong_answer=None, repair_trace=trace, final_answer=gold,
                        oracle_facts=[ctx["fact1"]], gold_symbolic_facts=[[ctx["head"], ctx["r1"], ctx["tail"]]])

        if cell == "K-Abl":
            problem = form["tpl"].format(q=base_q)
            wrong = _pick(rng, g["tails"], gold)
            trace = f"Despite the rephrasing, recall the same fact: {ctx['fact1']} The answer is {gold}."
            return dict(**common, problem=problem, tentative_answer=wrong, gold_answer=gold,
                        planted_wrong_answer=None, repair_trace=trace, final_answer=gold,
                        oracle_facts=[ctx["fact1"]], gold_symbolic_facts=[[ctx["head"], ctx["r1"], ctx["tail"]]])

        if cell == "K-Cor":
            wrong = _pick(rng, g["tails"], gold)
            problem = form["tpl"].format(q=base_q, wrong=wrong)
            trace = f"The claimed answer '{wrong}' contradicts the known fact: {ctx['fact1']} The correct answer is {gold}, not {wrong}."
            return dict(**common, problem=problem, tentative_answer=wrong, gold_answer=gold,
                        planted_wrong_answer=wrong, repair_trace=trace, final_answer=gold,
                        oracle_facts=[ctx["fact1"]], gold_symbolic_facts=[[ctx["head"], ctx["r1"], ctx["tail"]]])

        if cell == "H-Aug":
            problem = form["tpl"].format(q=base_q, bridge_fact=ctx["fact1"])
            wrong = _pick(rng, g["tails"], gold)
            # v2.1 fix: the bridge fact is GIVEN in the prompt; the repair is to USE it,
            # not retrieve it. Trace reflects use_provided_bridge_fact.
            trace = f"The bridge fact is given in the problem: {ctx['fact1']} Apply it directly: {ctx['fact2']} Therefore the answer is {gold}."
            return dict(**common, problem=problem, tentative_answer=wrong, gold_answer=gold,
                        planted_wrong_answer=None, repair_trace=trace, final_answer=gold,
                        oracle_facts=[ctx["fact1"], ctx["fact2"]],
                        gold_symbolic_facts=[[ctx["head"], ctx["r1"], ctx["bridge"]], [ctx["bridge"], ctx["r2"], ctx["tail"]]])

        if cell == "H-Abl":
            # v2.1 redo (plan A): KEEP the head, mask only the BRIDGE entity, so the
            # item is recoverable from injected facts (head -> bridge -> tail). The old
            # version masked the head too ("the work in question"), making it an
            # underspecified, unanswerable query.
            head_first = v0.first_fact_sentence(fam, ctx["head"], ctx["bridge"])  # "X was written by Maria Voss."
            masked_fact = head_first.replace(ctx["bridge"], "[MASK]")            # "X was written by [MASK]."
            problem = form["tpl"].format(q=f"{masked_fact} {base_q}")
            wrong = _pick(rng, g["tails"], gold)
            trace = f"The bridge entity is masked. Recover it from known facts: {ctx['fact1']} Then: {ctx['fact2']} The answer is {gold}."
            return dict(**common, problem=problem, tentative_answer=wrong, gold_answer=gold,
                        planted_wrong_answer=None, repair_trace=trace, final_answer=gold,
                        oracle_facts=[ctx["fact1"], ctx["fact2"]],
                        gold_symbolic_facts=[[ctx["head"], ctx["r1"], ctx["bridge"]], [ctx["bridge"], ctx["r2"], ctx["tail"]]])

        if cell == "H-Cor":
            wrong_bridge = _pick(rng, g["bridges"], ctx["bridge"])
            wb_edge = next((e for e in g["edges"] if e["bridge"] == wrong_bridge), None)
            wrong_tail = wb_edge["tail"] if wb_edge else _pick(rng, g["tails"], gold)
            if wrong_tail == gold:
                wrong_tail = _pick(rng, g["tails"], gold)
            clause = v0.first_fact_sentence(fam, ctx["head"], wrong_bridge).rstrip(".")
            problem = form["tpl"].format(q=base_q, wrong_bridge_clause=clause.lower())
            trace = f"The planted bridge is false: actually {ctx['fact1']} Then {ctx['fact2']} So the answer is {gold}, not {wrong_tail}."
            return dict(**common, problem=problem, tentative_answer=wrong_tail, gold_answer=gold,
                        planted_wrong_answer=wrong_tail, repair_trace=trace, final_answer=gold,
                        oracle_facts=[ctx["fact1"], ctx["fact2"]],
                        gold_symbolic_facts=[[ctx["head"], ctx["r1"], ctx["bridge"]], [ctx["bridge"], ctx["r2"], ctx["tail"]]])

    else:  # domain == "R"
        item = r_items_pool[idx % len(r_items_pool)]
        op, a, b, gold = item["op"], item["a"], item["b"], item["gold"]
        base_q = f"Compute the {op} of {a} and {b}."
        common["relation_family"] = f"reason_{op}"
        steps = item["steps"]
        rule = item["rule_statement"]

        if cell == "R-Aug":
            problem = form["tpl"].format(q=base_q)
            wrong = str(int(gold) + 1)
            trace = f"Apply the rule stepwise: {steps[0]}; {steps[1]}. The answer is {gold}."
            return dict(**common, problem=problem, tentative_answer=wrong, gold_answer=gold,
                        planted_wrong_answer=None, repair_trace=trace, final_answer=gold,
                        oracle_facts=[rule], gold_symbolic_facts=[[op, "applied_to", f"{a},{b}"]])
        if cell == "R-Abl":
            problem = form["tpl"].format(q=base_q)  # rule not restated; must recall
            wrong = str(int(gold) + 1)
            trace = f"Recall the rule: {rule} Then {steps[0]}; {steps[1]}. The answer is {gold}."
            return dict(**common, problem=problem, tentative_answer=wrong, gold_answer=gold,
                        planted_wrong_answer=None, repair_trace=trace, final_answer=gold,
                        oracle_facts=[rule], gold_symbolic_facts=[[op, "applied_to", f"{a},{b}"]])
        if cell == "R-Cor":
            # wrong intermediate: take the TRUE first-step result and perturb it by
            # a fixed offset, guaranteeing it differs from both the true mid and gold.
            import re as _re
            nums = _re.findall(r"-?\d+", steps[0])
            true_mid = int(nums[-1]) if nums else 0
            wrong_mid_val = true_mid + 7
            if wrong_mid_val == int(gold):
                wrong_mid_val += 1
            wrong_mid = str(wrong_mid_val)
            problem = form["tpl"].format(q=base_q, wrong_mid=wrong_mid)
            wrong = str(int(gold) + 3)
            trace = f"The suggested intermediate {wrong_mid} is wrong. Correctly: {steps[0]}; {steps[1]}. The answer is {gold}."
            return dict(**common, problem=problem, tentative_answer=wrong, gold_answer=gold,
                        planted_wrong_answer=wrong, repair_trace=trace, final_answer=gold,
                        oracle_facts=[rule], gold_symbolic_facts=[[op, "applied_to", f"{a},{b}"]])

    raise ValueError(cell)


def build_all_repair(rng):
    kh = {fam: v0.build_family_graph(fam) for fam in v0.FAMILY_NAMES}
    r_train, r_eval = R.build_reasoning_split(random.Random(1), n_train_per_op=40, n_eval_per_op=20)
    out = {"train": [], "eval": []}
    for split in ("train", "eval"):
        targets = REPAIR_TARGETS[split]
        r_pool = r_train if split == "train" else r_eval
        idxc = {c: 0 for c in targets}
        seen = set()
        cycle = []
        planned = {c: 0 for c in targets}
        order = CELLS_9 + ["Clean"]
        for _ in range(max(targets.values())):
            for c in order:
                if planned[c] < targets[c]:
                    cycle.append(c); planned[c] += 1
        for cell in cycle:
            rec = None
            for att in range(60):
                cand = build_repair_record(cell=cell, split=split, rng=rng,
                                           idx=idxc[cell] + att, kh_graphs=kh, r_items_pool=r_pool)
                key = (cand["problem"], cand["tentative_answer"])
                if key not in seen:
                    seen.add(key); rec = cand; break
            if rec is None:
                cand["problem"] += f"  //v{idxc[cell]}"; rec = cand
            idxc[cell] += 1
            out[split].append(rec)
    return out["train"], out["eval"]


def _w(rows, path):
    with path.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows):5d} -> {path}")


def generate(out_dir: Path, seed: int):
    rng = random.Random(seed)
    inject = build_inject(rng)
    rep_tr, rep_ev = build_all_repair(rng)

    # Coverage: every gold fact a repair item needs must be in the inject set.
    inj_triples = {tuple(r["symbolic_fact"]) for r in inject if r["kind"] == "entity_fact"}
    need = set()
    for r in rep_tr + rep_ev:
        if r["domain"] in ("K", "H", "-"):
            for t in r.get("gold_symbolic_facts", []):
                if len(t) == 3 and t[1] not in ("applied_to",):
                    need.add(tuple(t))
    missing = need - inj_triples
    if missing:
        raise SystemExit(f"COVERAGE FAIL: {len(missing)} repair facts not injected, e.g. {sorted(missing)[:5]}")
    print(f"coverage OK: {len(need)} K/H repair facts ⊆ {len(inj_triples)} injected")

    out_dir.mkdir(parents=True, exist_ok=True)
    _w(inject, out_dir / "inject.jsonl")            # train == eval (use same file)
    _w(rep_tr, out_dir / "repair_train.jsonl")
    _w(rep_ev, out_dir / "repair_eval.jsonl")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_dir", type=Path, default=Path("data_v2"))
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    generate(a.out_dir, a.seed)


if __name__ == "__main__":
    main()
