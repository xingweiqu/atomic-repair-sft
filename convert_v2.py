"""Convert v2 data into LLaMA-Factory alpaca formats + dataset_info.

Emits:
  inject (knowledge floor):  input = fact/rule question,  output = answer
  cot   (condition C):       input = Problem+Tentative,    output = {repair_trace, final_answer}
  skillcot (condition D):    input = same,                 output = {diagnosis, repair_skill,
                                                                     repair_trace, final_answer}
  zeroshot (condition A):    input = Problem+Tentative,    output = "" (eval prompts)

CoT and Skill+CoT inputs are built by ONE helper and asserted identical per row.

Usage: python convert_v2.py --data_dir data_v2
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

INJECT_INSTRUCTION = (
    "Answer from memory with only the answer. For a rule question, state the rule. "
    "No explanation."
)
REPAIR_INSTRUCTION = (
    "You are given a problem and a tentative answer that may be wrong. Using the facts "
    "and rules you have learned, reason about whether the tentative answer is correct, "
    "then give the corrected final answer. Return only valid JSON."
)
ZS_DIRECT = ("Given the problem and a tentative answer that may be wrong, output ONLY the "
             "corrected final answer on a single line. No explanation.")
ZS_COT = ("Given the problem and a tentative answer that may be wrong, think step by step "
          "using facts/rules you know, then end with a line 'Final answer: <answer>'.")


def repair_input(r):
    return f"Problem:\n{r['problem']}\n\nTentative answer:\n{r['tentative_answer']}"


def inj_alpaca(r):
    return {"instruction": INJECT_INSTRUCTION, "input": r["question"], "output": r["answer"]}


def cot_alpaca(r):
    return {"instruction": REPAIR_INSTRUCTION, "input": repair_input(r),
            "output": json.dumps({"repair_trace": r["repair_trace"],
                                  "final_answer": r["final_answer"]}, ensure_ascii=False)}


def skillcot_alpaca(r):
    return {"instruction": REPAIR_INSTRUCTION, "input": repair_input(r),
            "output": json.dumps({"diagnosis": r["diagnosis"], "repair_skill": r["repair_skill"],
                                  "repair_trace": r["repair_trace"],
                                  "final_answer": r["final_answer"]}, ensure_ascii=False)}


def zs_direct(r):
    return {"instruction": ZS_DIRECT, "input": repair_input(r), "output": ""}


def zs_cot(r):
    return {"instruction": ZS_COT, "input": repair_input(r), "output": ""}


def load(p):
    with p.open() as f:
        return [json.loads(l) for l in f if l.strip()]


def write(rows, p):
    p.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
    print(f"wrote {len(rows):5d} -> {p}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", type=Path, default=Path("data_v2"))
    a = ap.parse_args()
    d = a.data_dir
    inj = load(d / "inject.jsonl")
    tr = load(d / "repair_train.jsonl")
    ev = load(d / "repair_eval.jsonl")

    # knowledge injection: train == eval (same file, overfit floor)
    write([inj_alpaca(r) for r in inj], d / "inject_lf.json")

    cot_tr, sk_tr = [], []
    for r in tr:
        c, s = cot_alpaca(r), skillcot_alpaca(r)
        assert c["input"] == s["input"], f"input drift {r['id']}"
        cot_tr.append(c); sk_tr.append(s)
    cot_ev, sk_ev = [], []
    for r in ev:
        c, s = cot_alpaca(r), skillcot_alpaca(r)
        assert c["input"] == s["input"], f"input drift {r['id']}"
        cot_ev.append(c); sk_ev.append(s)
    write(cot_tr, d / "cot_lf_train.json"); write(cot_ev, d / "cot_lf_eval.json")
    write(sk_tr, d / "skillcot_lf_train.json"); write(sk_ev, d / "skillcot_lf_eval.json")
    print("OK: cot_input == skillcot_input for every repair row")

    write([zs_direct(r) for r in ev], d / "zeroshot_direct.json")
    write([zs_cot(r) for r in ev], d / "zeroshot_cot.json")

    cols = {"prompt": "instruction", "query": "input", "response": "output"}
    info = {
        "inject_v2": {"file_name": "inject_lf.json", "columns": cols},
        "repair_cot_v2_train": {"file_name": "cot_lf_train.json", "columns": cols},
        "repair_cot_v2_eval": {"file_name": "cot_lf_eval.json", "columns": cols},
        "repair_skillcot_v2_train": {"file_name": "skillcot_lf_train.json", "columns": cols},
        "repair_skillcot_v2_eval": {"file_name": "skillcot_lf_eval.json", "columns": cols},
        "repair_zeroshot_direct_v2": {"file_name": "zeroshot_direct.json", "columns": cols},
        "repair_zeroshot_cot_v2": {"file_name": "zeroshot_cot.json", "columns": cols},
    }
    (d / "dataset_info.json").write_text(json.dumps(info, indent=2))
    print(f"wrote {d / 'dataset_info.json'}")


if __name__ == "__main__":
    main()
