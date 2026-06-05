#!/usr/bin/env python3
"""Build v1 LLaMA-Factory datasets for A/B/C/D atomic-repair conditions.

Critical v1 contract:
  * repair/eval inputs never contain oracle facts;
  * B is an independent single-hop fact-injection stage;
  * C/D add repair demonstrations after the same fact-injection stage.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


CONDITIONS = {
    "A": {
        "name": "zero_shot",
        "train": False,
        "facts": False,
        "instruction": (
            "You are an atomic repair evaluator. Given a problem and a tentative answer, "
            "return only valid JSON with the corrected final_answer."
        ),
        "fields": ("final_answer",),
    },
    "B": {
        "name": "fact_only",
        "train": True,
        "instruction": (
            "You are an atomic repair evaluator. Given a problem and a tentative answer, "
            "use your learned facts to return only valid JSON with the corrected final_answer."
        ),
        "fields": ("final_answer",),
    },
    "C": {
        "name": "fact_cot",
        "train": True,
        "instruction": (
            "You are an atomic repair evaluator. Given a problem and a tentative answer, "
            "use your learned facts, write a concise repair_trace, then give the corrected "
            "final_answer. Return only valid JSON."
        ),
        "fields": ("repair_trace", "final_answer"),
    },
    "D": {
        "name": "fact_skill_cot",
        "train": True,
        "instruction": (
            "You are an atomic repair agent. Given a problem and a tentative answer, "
            "diagnose whether there is an atomic-capacity failure. If there is a failure, choose "
            "the correct repair skill and repair the answer. If there is no failure, do not "
            "over-repair. Return only valid JSON."
        ),
        "fields": ("diagnosis", "repair_skill", "repair_trace", "final_answer"),
    },
}

FACT_INSTRUCTION = (
    "You are learning atomic one-hop facts. Answer the one-hop question from memory. "
    "Return only valid JSON with final_answer."
)


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def convert_record(row: dict, condition: str) -> dict:
    spec = CONDITIONS[condition]
    parts = [f"Problem:\n{row['problem']}", f"Tentative answer:\n{row['tentative_answer']}"]
    output = {field: row[field] for field in spec["fields"]}
    return {
        "instruction": spec["instruction"],
        "input": "\n\n".join(parts),
        "output": json.dumps(output, ensure_ascii=False),
    }


def fact_questions(row: dict) -> list[dict]:
    """Turn symbolic one-hop facts into memory-injection QA records.

    These records may include eval entities because they are the intended knowledge
    injection stage. They are not bridge repair examples and never include the
    original multi-hop task or its tentative answer.
    """
    records = []
    for subj, rel, obj in row.get("symbolic_facts") or []:
        if rel == "written_by":
            question = f"Who wrote {subj}?"
        elif rel == "nationality":
            question = f"What is the nationality of {subj}?"
        else:
            question = f"What is the {rel.replace('_', ' ')} of {subj}?"
        records.append({
            "instruction": FACT_INSTRUCTION,
            "input": f"Problem:\n{question}",
            "output": json.dumps({"final_answer": obj}, ensure_ascii=False),
        })
    return records


def build_fact_injection(rows: list[dict]) -> list[dict]:
    dedup = {}
    for row in rows:
        for record in fact_questions(row):
            key = (record["input"], record["output"])
            dedup[key] = record
    return list(dedup.values())


def write_dataset(records: list[dict], out_path: Path, condition: str) -> None:
    converted = [convert_record(row, condition) for row in records]
    out_path.write_text(json.dumps(converted, indent=2, ensure_ascii=False))
    print(f"wrote {len(converted):5d} records -> {out_path}")


def write_mixed_dataset(fact_records: list[dict], repair_rows: list[dict], out_path: Path, condition: str) -> None:
    converted = list(fact_records)
    if condition in {"C", "D"}:
        converted.extend(convert_record(row, condition) for row in repair_rows)
    out_path.write_text(json.dumps(converted, indent=2, ensure_ascii=False))
    print(f"wrote {len(converted):5d} records -> {out_path}")


def write_dataset_info(out_dir: Path) -> None:
    info = {}
    for condition, spec in CONDITIONS.items():
        prefix = f"atomic_repair_v1_{condition}"
        if spec["train"]:
            info[f"{prefix}_train"] = {
                "file_name": f"repair_v1_{condition}_train.json",
                "columns": {"prompt": "instruction", "query": "input", "response": "output"},
            }
        info[f"{prefix}_eval"] = {
            "file_name": f"repair_v1_{condition}_eval.json",
            "columns": {"prompt": "instruction", "query": "input", "response": "output"},
        }
    path = out_dir / "dataset_info.json"
    path.write_text(json.dumps(info, indent=2, ensure_ascii=False))
    print(f"wrote {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", required=True, type=Path)
    parser.add_argument("--eval", required=True, type=Path)
    parser.add_argument("--out_dir", required=True, type=Path)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    train_rows = load_jsonl(args.train)
    eval_rows = load_jsonl(args.eval)

    for condition, spec in CONDITIONS.items():
        if spec["train"]:
            fact_records = build_fact_injection(train_rows + eval_rows)
            write_mixed_dataset(fact_records, train_rows, args.out_dir / f"repair_v1_{condition}_train.json", condition)
        write_dataset(eval_rows, args.out_dir / f"repair_v1_{condition}_eval.json", condition)
    write_dataset_info(args.out_dir)


if __name__ == "__main__":
    main()
