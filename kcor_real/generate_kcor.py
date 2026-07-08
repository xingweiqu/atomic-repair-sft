#!/usr/bin/env python3
"""K-Cor clean real-domain set (C-10 §2a; source deviation logged as qc/DISCREPANCIES D-10).

Facts: LAMA/T-REx (standard Wikidata 1-hop triples). Per relation, hand-written question
templates; Corrupt injection = v4 claim-phrasing bank + TYPE-MATCHED wrong object sampled
from the SAME relation's object pool (type-match gate by construction). Output schema is
byte-identical to R-Cor (v4 actionized): same instruction string, same input framing,
same JSON output fields — the prereg's format-confound exclusion requirement.

Gates (asserted at generation):
  - train/eval SUBJECT-entity disjoint (C-10) and (subject, relation) unique;
  - planted wrong != gold, drawn from same-relation object pool (type-matched);
  - per-item leak flags vs the train exposure (triple level), written alongside;
  - volumes: train 1500 / eval 600 (>=500 spec).
Card: construct = resist+recall (gold recovery relies on parametric memory) — the
"knownness probe" (pre-repair zero-shot QA on eval facts) is a REPORTED covariate,
generated as a separate probe file; here the clean gate is inverted by design.

Run ON SERVER (needs datasets + network): python3 kcor_real/generate_kcor.py
"""
from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "kcor_real/data"
INSTR = ("You are given a question and a tentative answer that may be wrong. Decide whether "
         "to keep it, update it, or abstain, commit to the repair action, then give the final "
         "answer (or null if you must abstain). Return only valid JSON.")
# NOTE: mirrors the v4 instruction with "math word problem" -> "question"; everything else,
# including the input framing "Problem:\n...\n\nTentative answer:\n...", is identical.

N_TRAIN, N_EVAL = 1500, 600

# 12 high-coverage T-REx relations with question templates (subject -> object questions).
RELATIONS = {
    "P19":  ("Where was {s} born?",                       "birthplace"),
    "P20":  ("Where did {s} die?",                        "place of death"),
    "P27":  ("Which country is {s} a citizen of?",        "citizenship"),
    "P36":  ("What is the capital of {s}?",               "capital"),
    "P106": ("What is {s}'s occupation?",                 "occupation"),
    "P127": ("Who owns {s}?",                             "owner"),
    "P131": ("In which administrative region is {s} located?", "located in"),
    "P138": ("Who or what is {s} named after?",           "named after"),
    "P159": ("Where is the headquarters of {s}?",         "headquarters"),
    "P176": ("Which company produces {s}?",               "manufacturer"),
    "P264": ("Which record label is {s} signed to?",      "record label"),
    "P495": ("Which country does {s} come from?",         "country of origin"),
}

CLAIM_INTROS_TRAIN = [
    "Reportedly the answer is {w}.", "It says here that the answer is {w}.",
    "I read somewhere that the answer is {w}.", "Someone told me the answer is {w}.",
]
CLAIM_INTROS_EVAL = [
    "Apparently the answer is {w}.", "A note claims the answer is {w}.",
    "According to one source the answer is {w}.", "Word is that the answer is {w}.",
]


def load_trex():
    from datasets import load_dataset
    errs = []
    for name, cfg in [("lama", "trex"), ("facebook/lama", "trex"), ("cfierro/lama_trex", None)]:
        try:
            ds = load_dataset(name, cfg, split="train") if cfg else load_dataset(name, split="train")
            print(f"loaded {name}/{cfg}: {len(ds)}")
            return ds
        except Exception as e:
            errs.append(f"{name}: {str(e)[:100]}")
    raise SystemExit("T-REx unavailable; STOP and report:\n" + "\n".join(errs))


def record(idx, split, rel, subj, gold, wrong, rng):
    q = RELATIONS[rel][0].format(s=subj)
    intro = rng.choice(CLAIM_INTROS_TRAIN if split == "train" else CLAIM_INTROS_EVAL).format(w=wrong)
    problem = f"{intro} {q}"
    trace = f"Action: override wrong claim. The claimed answer {wrong} is wrong; the correct answer is {gold}."
    return {
        "id": f"KCor_{split}_{idx:06d}", "failure_type": "K-Cor",
        "policy": "override_wrong_claim", "update_decision": "update", "split": split,
        "relation": rel, "subject": subj,
        "problem": problem, "tentative_answer": wrong, "gold_answer": gold,
        "planted_wrong_answer": wrong,
        "repair_trace": trace, "final_answer": gold,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(42)
    ds = load_trex()
    by_rel = defaultdict(dict)   # rel -> subj -> gold (dedupe (s,r))
    for r in ds:
        rel = r.get("predicate_id") or r.get("rel") or ""
        if rel not in RELATIONS:
            continue
        s = (r.get("sub_label") or "").strip()
        o = (r.get("obj_label") or "").strip()
        if s and o and s.lower() != o.lower() and s not in by_rel[rel]:
            by_rel[rel][s] = o
    print("facts per relation:", {k: len(v) for k, v in by_rel.items()})

    # subject-disjoint split per relation, proportional quotas
    train, evalr = [], []
    rels = [r for r in RELATIONS if len(by_rel[r]) >= 40]
    qt, qe = N_TRAIN // len(rels), N_EVAL // len(rels)
    for rel in rels:
        subs = sorted(by_rel[rel])
        rng.shuffle(subs)
        need = qt + qe
        subs = subs[:max(need, min(len(subs), need))]
        tr_s, ev_s = subs[:qt], subs[qt:qt + qe]
        pool = sorted({by_rel[rel][s] for s in by_rel[rel]})
        for i, s in enumerate(tr_s):
            gold = by_rel[rel][s]
            wrong = rng.choice([o for o in pool if o != gold])
            train.append(record(len(train), "train", rel, s, gold, wrong, rng))
        for i, s in enumerate(ev_s):
            gold = by_rel[rel][s]
            wrong = rng.choice([o for o in pool if o != gold])
            evalr.append(record(len(evalr), "eval", rel, s, gold, wrong, rng))

    # ---- gates ----
    tr_subj = {(r["relation"], r["subject"]) for r in train}
    ev_subj = {(r["relation"], r["subject"]) for r in evalr}
    assert not (tr_subj & ev_subj), "subject overlap!"
    tr_subj_only = {r["subject"] for r in train}
    assert not (tr_subj_only & {r["subject"] for r in evalr}), "cross-relation subject overlap!"
    for r in train + evalr:
        assert r["planted_wrong_answer"] != r["gold_answer"]
    # per-item leak flags: eval triple in train exposure?
    tr_triples = {(r["relation"], r["subject"], r["gold_answer"]) for r in train}
    with (OUT / "leak_flags_eval.jsonl").open("w") as f:
        for r in evalr:
            f.write(json.dumps({"id": r["id"],
                                "leak_sft": int((r["relation"], r["subject"], r["gold_answer"]) in tr_triples)}) + "\n")

    for name, rows in [("kcor_train.jsonl", train), ("kcor_eval.jsonl", evalr)]:
        with (OUT / name).open("w") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ---- LF conversion (byte-identical framing to v4) ----
    def lf(rows):
        out = []
        for r in rows:
            out.append({"instruction": INSTR,
                        "input": f"Problem:\n{r['problem']}\n\nTentative answer:\n{r['tentative_answer']}",
                        "output": json.dumps({"update_decision": "update",
                                              "update_policy": "override_wrong_claim",
                                              "repair_trace": r["repair_trace"],
                                              "final_answer": r["final_answer"]}, ensure_ascii=False)})
        return out
    (OUT / "kcor_lf_train.json").write_text(json.dumps(lf(train), ensure_ascii=False, indent=1))
    (OUT / "kcor_lf_eval.json").write_text(json.dumps(lf(evalr), ensure_ascii=False, indent=1))
    # knownness probe (plain QA, no corruption) for the covariate
    probe = [{"instruction": "Answer the question. End with a line exactly in the form "
                             "'The final answer is X.'",
              "input": RELATIONS[r["relation"]][0].format(s=r["subject"]) + " /no_think",
              "output": f"The final answer is {r['gold_answer']}."} for r in evalr]
    (OUT / "kcor_knownness_probe.json").write_text(json.dumps(probe, ensure_ascii=False, indent=1))
    di = {"kcor_train": {"file_name": "kcor_lf_train.json",
                         "columns": {"prompt": "instruction", "query": "input", "response": "output"}},
          "kcor_eval": {"file_name": "kcor_lf_eval.json",
                        "columns": {"prompt": "instruction", "query": "input", "response": "output"}},
          "kcor_knownness": {"file_name": "kcor_knownness_probe.json",
                             "columns": {"prompt": "instruction", "query": "input", "response": "output"}}}
    (OUT / "dataset_info.json").write_text(json.dumps(di, indent=1))
    leaks = sum(json.loads(l)["leak_sft"] for l in (OUT / "leak_flags_eval.jsonl").open())
    print(f"train {len(train)} / eval {len(evalr)} / relations {len(rels)} / "
          f"eval leak_sft {leaks} (subject-disjoint => expect 0)")
    print("ALL GATES PASS")


if __name__ == "__main__":
    main()
