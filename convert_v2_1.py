"""Convert v2.1 data into LLaMA-Factory formats: base conditions + ablations.

Emits (all from data_v2_1/repair_{train,eval}.jsonl, knowledge inject unchanged):
  inject_lf                 knowledge floor (same as v2)
  cot_lf_{train,eval}       C  : CoT-only            {repair_trace, final_answer}
  skillcot_lf_{train,eval}  D  : Skill+CoT           {diagnosis, repair_skill, ...}
  randomskill_lf_{train,eval}     ABLATION 3: skill labels shuffled (fixed seed)
  decision_lf_{train,eval}        ABLATION 3.5: {repair_decision: keep/repair, ...}
  actionized_lf_{train,eval}      ABLATION 4: no skill field, trace starts "Action: <skill>."
  zeroshot_{direct,cot}           A baselines
  prefix_gold_eval / prefix_wrong_eval   ABLATION 5: inference-time skill prefix (eval only)

Random mapping (3) is seeded and written to randomskill_mapping.json for reproducibility.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import forms_v2 as F

INJECT_INSTRUCTION = ("Answer from memory with only the answer. For a rule question, "
                      "state the rule. No explanation.")
REPAIR_INSTRUCTION = ("You are given a problem and a tentative answer that may be wrong. "
                      "Using the facts and rules you have learned, reason about whether the "
                      "tentative answer is correct, then give the corrected final answer. "
                      "Return only valid JSON.")
ZS_DIRECT = ("Given the problem and a tentative answer that may be wrong, output ONLY the "
             "corrected final answer on a single line. No explanation.")
ZS_COT = ("Given the problem and a tentative answer that may be wrong, think step by step "
          "using facts/rules you know, then end with a line 'Final answer: <answer>'.")

# Human-readable action phrase per repair_skill (for Actionized-CoT, ablation 4).
SKILL_ACTION = {
    "retrieval_cueing": "surface the stored fact",
    "paraphrase_robust_recall": "recall the same fact despite rephrasing",
    "contradiction_check": "contradiction check",
    "decomposition_scaffold": "decompose and apply the rule stepwise",
    "rule_reinjection": "recall the rule, then apply it",
    "step_verification": "step verification",
    "use_provided_bridge_fact": "use the provided bridge fact",
    "provide_bridge_entity": "recover the masked bridge entity",
    "source_verification": "bridge source verification",
    "keep_answer": "keep the answer",
}
# keep/repair ground truth per skill (Clean keeps; everything else repairs).
def decision_of(rec):
    return "keep" if rec["cell"] == "Clean" else "repair"


def rinput(r):
    return f"Problem:\n{r['problem']}\n\nTentative answer:\n{r['tentative_answer']}"


def cot(r):
    return {"instruction": REPAIR_INSTRUCTION, "input": rinput(r),
            "output": json.dumps({"repair_trace": r["repair_trace"],
                                  "final_answer": r["final_answer"]}, ensure_ascii=False)}


def skillcot(r):
    return {"instruction": REPAIR_INSTRUCTION, "input": rinput(r),
            "output": json.dumps({"diagnosis": r["diagnosis"], "repair_skill": r["repair_skill"],
                                  "repair_trace": r["repair_trace"],
                                  "final_answer": r["final_answer"]}, ensure_ascii=False)}


def randomskill(r, mapping):
    # shuffle the (diagnosis, repair_skill) to a DIFFERENT cell's labels; trace+answer unchanged
    d2, s2 = mapping[r["cell"]]
    return {"instruction": REPAIR_INSTRUCTION, "input": rinput(r),
            "output": json.dumps({"diagnosis": d2, "repair_skill": s2,
                                  "repair_trace": r["repair_trace"],
                                  "final_answer": r["final_answer"]}, ensure_ascii=False)}


def decision(r):
    return {"instruction": REPAIR_INSTRUCTION, "input": rinput(r),
            "output": json.dumps({"repair_decision": decision_of(r),
                                  "repair_trace": r["repair_trace"],
                                  "final_answer": r["final_answer"]}, ensure_ascii=False)}


def actionized(r):
    act = SKILL_ACTION.get(r["repair_skill"], "repair")
    tr = f"Action: {act}. {r['repair_trace']}"
    return {"instruction": REPAIR_INSTRUCTION, "input": rinput(r),
            "output": json.dumps({"repair_trace": tr, "final_answer": r["final_answer"]},
                                 ensure_ascii=False)}


def zs(r, instr):
    return {"instruction": instr, "input": rinput(r), "output": ""}


# Ablation 5: inference-time prefix. We PRE-FILL the start of the assistant answer
# with the skill fields, so the model continues from a committed repair state.
# Realised as putting the prefix into the input (a "Begin your answer with:" cue),
# since LF predict has no assistant-prefill hook in the alpaca format.
def prefix_item(r, gold=True, wrong_map=None):
    if gold:
        d, s = r["diagnosis"], r["repair_skill"]
    else:
        d, s = wrong_map[r["cell"]]
    cue = (f'{REPAIR_INSTRUCTION} Begin your JSON with '
           f'"diagnosis": "{d}", "repair_skill": "{s}", then continue.')
    return {"instruction": cue, "input": rinput(r), "output": ""}


def load(p):
    with p.open() as f:
        return [json.loads(l) for l in f if l.strip()]


def write(rows, p):
    p.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
    print(f"wrote {len(rows):5d} -> {p}")


def build_random_mapping(seed=1234):
    """Map each cell's (diagnosis,skill) to a DIFFERENT cell's labels. Fixed seed."""
    cells = list(F.CELL_SPEC_V2.keys())
    rng = random.Random(seed)
    labels = {c: (F.CELL_SPEC_V2[c]["diagnosis"], F.CELL_SPEC_V2[c]["repair_skill"]) for c in cells}
    # derange: ensure no cell maps to itself
    while True:
        shuffled = cells[:]
        rng.shuffle(shuffled)
        if all(a != b for a, b in zip(cells, shuffled)):
            break
    return {c: labels[shuffled[i]] for i, c in enumerate(cells)}, {c: shuffled[i] for i, c in enumerate(cells)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", type=Path, default=Path("data_v2_1"))
    a = ap.parse_args()
    d = a.data_dir
    inj = load(d / "inject.jsonl")
    tr = load(d / "repair_train.jsonl")
    ev = load(d / "repair_eval.jsonl")

    # knowledge inject (unchanged)
    write([{"instruction": INJECT_INSTRUCTION, "input": r["question"], "output": r["answer"]}
           for r in inj], d / "inject_lf.json")

    # C / D (re-emitted from fixed data)
    for fn, builder in [("cot_lf", cot), ("skillcot_lf", skillcot), ("actionized_lf", actionized),
                        ("decision_lf", decision)]:
        write([builder(r) for r in tr], d / f"{fn}_train.json")
        write([builder(r) for r in ev], d / f"{fn}_eval.json")

    # Random skill (ablation 3) with fixed, recorded mapping
    rand_map, cell_map = build_random_mapping(seed=1234)
    (d / "randomskill_mapping.json").write_text(json.dumps(
        {"seed": 1234, "cell_to_borrowed_cell": cell_map,
         "cell_to_labels": {k: list(v) for k, v in rand_map.items()}}, indent=2))
    write([randomskill(r, rand_map) for r in tr], d / "randomskill_lf_train.json")
    write([randomskill(r, rand_map) for r in ev], d / "randomskill_lf_eval.json")
    print(f"random mapping (no fixed point): {cell_map}")

    # zero-shot
    write([zs(r, ZS_DIRECT) for r in ev], d / "zeroshot_direct.json")
    write([zs(r, ZS_COT) for r in ev], d / "zeroshot_cot.json")

    # prefix inference (ablation 5): gold + wrong. wrong uses a deliberately bad skill.
    WRONG = {  # pick a clearly-mismatched skill per cell
        "K-Aug": ("no_failure_detected", "keep_answer"),
        "K-Abl": ("no_failure_detected", "keep_answer"),
        "K-Cor": ("no_failure_detected", "keep_answer"),
        "R-Aug": ("wrong_factual_claim", "contradiction_check"),
        "R-Abl": ("wrong_factual_claim", "contradiction_check"),
        "R-Cor": ("no_failure_detected", "keep_answer"),
        "H-Aug": ("wrong_bridge_contamination", "source_verification"),
        "H-Abl": ("no_failure_detected", "keep_answer"),
        "H-Cor": ("no_failure_detected", "keep_answer"),
        "Clean": ("wrong_factual_claim", "contradiction_check"),
    }
    write([prefix_item(r, gold=True) for r in ev], d / "prefix_gold_eval.json")
    write([prefix_item(r, gold=False, wrong_map=WRONG) for r in ev], d / "prefix_wrong_eval.json")
    (d / "prefix_wrong_map.json").write_text(json.dumps(WRONG, indent=2))

    # dataset_info
    cols = {"prompt": "instruction", "query": "input", "response": "output"}
    names = {
        "inject_v21": "inject_lf.json",
        "cot_v21_train": "cot_lf_train.json", "cot_v21_eval": "cot_lf_eval.json",
        "skillcot_v21_train": "skillcot_lf_train.json", "skillcot_v21_eval": "skillcot_lf_eval.json",
        "randomskill_v21_train": "randomskill_lf_train.json", "randomskill_v21_eval": "randomskill_lf_eval.json",
        "decision_v21_train": "decision_lf_train.json", "decision_v21_eval": "decision_lf_eval.json",
        "actionized_v21_train": "actionized_lf_train.json", "actionized_v21_eval": "actionized_lf_eval.json",
        "zeroshot_direct_v21": "zeroshot_direct.json", "zeroshot_cot_v21": "zeroshot_cot.json",
        "prefix_gold_v21": "prefix_gold_eval.json", "prefix_wrong_v21": "prefix_wrong_eval.json",
    }
    (d / "dataset_info.json").write_text(json.dumps(
        {k: {"file_name": v, "columns": cols} for k, v in names.items()}, indent=2))
    print(f"wrote {d/'dataset_info.json'}")


if __name__ == "__main__":
    main()
