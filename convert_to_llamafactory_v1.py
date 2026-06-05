#!/usr/bin/env python3
"""Build v1 LLaMA-Factory datasets for A/B/C/D atomic-repair conditions."""
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
        "facts": True,
        "instruction": (
            "You are an atomic repair evaluator. Use the provided oracle facts to answer. "
            "Return only valid JSON with final_answer."
        ),
        "fields": ("final_answer",),
    },
    "C": {
        "name": "fact_cot",
        "train": True,
        "facts": True,
        "instruction": (
            "You are an atomic repair evaluator. Use the provided oracle facts, write a concise "
            "repair_trace, then give the corrected final_answer. Return only valid JSON."
        ),
        "fields": ("repair_trace", "final_answer"),
    },
    "D": {
        "name": "fact_skill_cot",
        "train": True,
        "facts": True,
        "instruction": (
            "You are an atomic repair agent. Given a problem, a tentative answer, and oracle facts, "
            "diagnose whether there is an atomic-capacity failure. If there is a failure, choose "
            "the correct repair skill and repair the answer. If there is no failure, do not "
            "over-repair. Return only valid JSON."
        ),
        "fields": ("diagnosis", "repair_skill", "repair_trace", "final_answer"),
    },
}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def format_facts(row: dict) -> str:
    facts = row.get("oracle_facts") or []
    return "\n".join(f"- {fact}" for fact in facts)


def convert_record(row: dict, condition: str) -> dict:
    spec = CONDITIONS[condition]
    parts = [f"Problem:\n{row['problem']}", f"Tentative answer:\n{row['tentative_answer']}"]
    if spec["facts"]:
        parts.append(f"Oracle facts:\n{format_facts(row)}")
    output = {field: row[field] for field in spec["fields"]}
    return {
        "instruction": spec["instruction"],
        "input": "\n\n".join(parts),
        "output": json.dumps(output, ensure_ascii=False),
    }


def write_dataset(records: list[dict], out_path: Path, condition: str) -> None:
    converted = [convert_record(row, condition) for row in records]
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
            write_dataset(train_rows, args.out_dir / f"repair_v1_{condition}_train.json", condition)
        write_dataset(eval_rows, args.out_dir / f"repair_v1_{condition}_eval.json", condition)
    write_dataset_info(args.out_dir)


if __name__ == "__main__":
    main()
