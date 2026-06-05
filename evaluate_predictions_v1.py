#!/usr/bin/env python3
"""Evaluate v1 A/B/C/D predictions and write data_v1/comparison_v1.md."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


CONDITIONS = {
    "A": {"name": "zero_shot", "fields": ("final_answer",)},
    "B": {"name": "fact_only", "fields": ("final_answer",)},
    "C": {"name": "fact_cot", "fields": ("repair_trace", "final_answer")},
    "D": {"name": "fact_skill_cot", "fields": ("diagnosis", "repair_skill", "repair_trace", "final_answer")},
}
CELLS = ["H-Aug", "H-Abl", "H-Cor", "K-Cor", "Clean"]


def load_raw(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_pred(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        rows.append({
            "pred_text": obj.get("predict", obj.get("prediction", obj.get("output", ""))),
            "gold_text": obj.get("label", obj.get("reference", obj.get("response", ""))),
            "raw": obj,
        })
    return rows


def parse_json(text: str) -> dict | None:
    if not text:
        return None
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    while start != -1:
        depth = 0
        for end in range(start, len(text)):
            if text[end] == "{":
                depth += 1
            elif text[end] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(text[start : end + 1])
                        return obj if isinstance(obj, dict) else None
                    except json.JSONDecodeError:
                        break
        start = text.find("{", start + 1)
    return None


def norm_answer(value) -> str:
    return re.sub(r"[\s.]+$", "", str(value or "").strip()).lower()


def trace_grounded(trace, facts: list[str]) -> int:
    text = str(trace or "").lower()
    for fact in facts:
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", fact):
            if token.lower() in text:
                return 1
    return 0


def mean(xs: list[int]) -> float:
    return round(sum(xs) / len(xs), 4) if xs else 0.0


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def evaluate_condition(condition: str, pred_path: Path, raws: list[dict]) -> dict:
    preds = load_pred(pred_path)
    pairs = list(zip(preds, raws))
    by_cell = {cell: defaultdict(list) for cell in CELLS}
    overall = defaultdict(list)
    skill_confusion = Counter()

    for pred, raw in pairs:
        cell = raw["cell"]
        obj = parse_json(pred["pred_text"])
        valid = obj is not None
        for bucket in (overall, by_cell[cell]):
            bucket["json_valid"].append(int(valid))
        final_ok = int(valid and norm_answer(obj.get("final_answer")) == norm_answer(raw["final_answer"]))
        for bucket in (overall, by_cell[cell]):
            bucket["final_answer"].append(final_ok)
        if condition in {"C", "D"}:
            grounded = int(valid and trace_grounded(obj.get("repair_trace"), raw.get("oracle_facts") or []))
            for bucket in (overall, by_cell[cell]):
                bucket["trace_grounded"].append(grounded)
        if condition == "D":
            diag_ok = int(valid and str(obj.get("diagnosis", "")).strip() == str(raw["diagnosis"]).strip())
            skill_ok = int(valid and str(obj.get("repair_skill", "")).strip() == str(raw["repair_skill"]).strip())
            exact_all = int(final_ok and diag_ok and skill_ok)
            for bucket in (overall, by_cell[cell]):
                bucket["diagnosis"].append(diag_ok)
                bucket["repair_skill"].append(skill_ok)
                bucket["exact_all3"].append(exact_all)
            if valid:
                skill_confusion[(raw["repair_skill"], str(obj.get("repair_skill", "")).strip())] += 1

    def summarize(bucket: dict[str, list[int]]) -> dict:
        return {key: {"n": len(values), "acc": mean(values)} for key, values in bucket.items()}

    return {
        "condition": condition,
        "name": CONDITIONS[condition]["name"],
        "pred_path": str(pred_path),
        "n_pred": len(preds),
        "n_raw": len(raws),
        "overall": summarize(overall),
        "per_cell": {cell: summarize(vals) for cell, vals in by_cell.items()},
        "skill_confusion": {f"{g} -> {p}": n for (g, p), n in skill_confusion.most_common()},
    }


def write_report(report: dict, out_path: Path) -> None:
    lines = ["# Atomic Repair v1 Comparison", ""]
    lines += ["## Conditions", ""]
    lines += ["| condition | name | train | oracle facts in input | output schema |", "|---|---|---:|---:|---|"]
    rows = [
        ("A", "zero-shot", "no", "no", "final_answer"),
        ("B", "Fact-only", "yes", "no", "final_answer"),
        ("C", "Fact→CoT", "yes", "no", "repair_trace, final_answer"),
        ("D", "Fact→Skill+CoT", "yes", "no", "diagnosis, repair_skill, repair_trace, final_answer"),
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    lines += ["", "## Overall", ""]
    lines += ["| condition | n_pred/raw | json_valid | final_answer | trace_grounded | diagnosis | repair_skill | exact_all3 |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for condition in "ABCD":
        item = report["conditions"][condition]
        overall = item["overall"]
        def get(metric: str) -> str:
            return pct(overall[metric]["acc"]) if metric in overall else "-"
        lines.append(
            f"| {condition} {item['name']} | {item['n_pred']}/{item['n_raw']} | {get('json_valid')} | {get('final_answer')} | "
            f"{get('trace_grounded')} | {get('diagnosis')} | {get('repair_skill')} | {get('exact_all3')} |"
        )
    lines += ["", "## Per-cell final_answer accuracy", ""]
    lines += ["| cell | A | B | C | D |", "|---|---:|---:|---:|---:|"]
    for cell in CELLS:
        vals = []
        for condition in "ABCD":
            metric = report["conditions"][condition]["per_cell"][cell].get("final_answer", {"acc": 0.0})
            vals.append(pct(metric["acc"]))
        lines.append(f"| {cell} | " + " | ".join(vals) + " |")
    lines += ["", "## D skill confusion", ""]
    confusion = report["conditions"]["D"].get("skill_confusion", {})
    if confusion:
        lines += ["| gold -> pred | n |", "|---|---:|"]
        for key, value in confusion.items():
            lines.append(f"| {key} | {value} |")
    else:
        lines.append("No D skill confusion entries.")
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", default="data/repair_raw_eval.jsonl", type=Path)
    parser.add_argument("--out_dir", default="data_v1", type=Path)
    parser.add_argument("--pred_A", default="output/qwen3_8b_repair_v1_A_predict/generated_predictions.jsonl", type=Path)
    parser.add_argument("--pred_B", default="output/qwen3_8b_repair_v1_B_predict/generated_predictions.jsonl", type=Path)
    parser.add_argument("--pred_C", default="output/qwen3_8b_repair_v1_C_predict/generated_predictions.jsonl", type=Path)
    parser.add_argument("--pred_D", default="output/qwen3_8b_repair_v1_D_predict/generated_predictions.jsonl", type=Path)
    args = parser.parse_args()

    raws = load_raw(args.raw)
    preds = {"A": args.pred_A, "B": args.pred_B, "C": args.pred_C, "D": args.pred_D}
    report = {"conditions": {}}
    for condition, path in preds.items():
        if not path.exists():
            raise FileNotFoundError(f"missing predictions for condition {condition}: {path}")
        report["conditions"][condition] = evaluate_condition(condition, path, raws)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / "comparison_v1.json"
    md_path = args.out_dir / "comparison_v1.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(report, md_path)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")


if __name__ == "__main__":
    main()
