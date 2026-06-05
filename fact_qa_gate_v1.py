#!/usr/bin/env python3
"""Build and score the v1 single-hop fact-QA gate.

The gate checks whether the B fact-only checkpoint actually learned the atomic
facts needed by the repair eval set. The eval prompts contain only a one-hop
question and never include oracle facts.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


INSTRUCTION = (
    "Answer the one-hop factual question from memory. "
    "Return only valid JSON with final_answer."
)


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def norm_answer(value) -> str:
    return re.sub(r"[\s.]+$", "", str(value or "").strip()).lower()


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


def fact_question(subject: str, relation: str, hop: str) -> tuple[str, str]:
    """Return an eval-time paraphrase and hop label for a symbolic fact."""
    if relation == "written_by":
        return f"Name the author of {subject}.", hop
    if relation == "founded_by":
        return f"Name the founder of {subject}.", hop
    if relation == "located_in":
        return f"Which country contains {subject}?", hop
    if relation == "made_by":
        return f"Which company made {subject}?", hop
    if relation == "created_by":
        return f"Which artist created {subject}?", hop
    if relation == "known_for":
        return f"What discovery is {subject} known for?", hop
    if relation == "nationality":
        return f"Of what nationality is {subject}?", hop
    if relation == "uses_currency":
        return f"What currency is used in {subject}?", hop
    if relation == "headquartered_in":
        return f"Where is {subject} headquartered?", hop
    if relation == "birth_country":
        return f"What is the birth country of {subject}?", hop
    if relation == "field":
        return f"What field is {subject} in?", hop
    return f"Name the {relation.replace('_', ' ')} of {subject}.", hop


def needed_facts(row: dict) -> list[tuple[str, str, str, str]]:
    """Keep only the head->bridge and bridge->tail facts needed for repair.

    Some H-Cor examples also carry distractor facts such as the planted wrong
    bridge's nationality. The first two symbolic facts are the required
    head->bridge and bridge->tail facts; later facts are distractors.
    """
    facts = []
    for idx, (subject, relation, obj) in enumerate(row.get("symbolic_facts") or []):
        hop = "first" if idx == 0 else "second"
        facts.append((subject, relation, obj, hop))
        if len(facts) == 2:
            break
    return facts


def build_fact_eval(raw_path: Path, out_dir: Path) -> None:
    rows = load_jsonl(raw_path)
    dedup: dict[tuple[str, str, str], dict] = {}
    for row in rows:
        for subject, relation, obj, hop in needed_facts(row):
            question, hop = fact_question(subject, relation, hop)
            key = (subject, relation, obj)
            dedup[key] = {
                "id": f"fact_eval_{len(dedup):04d}",
                "relation_family": row.get("relation_family", "unknown"),
                "hop": hop,
                "subject": subject,
                "relation": relation,
                "final_answer": obj,
                "question": question,
            }

    meta = list(dedup.values())
    alpaca = [
        {
            "instruction": INSTRUCTION,
            "input": f"Problem:\n{item['question']}",
            "output": json.dumps({"final_answer": item["final_answer"]}, ensure_ascii=False),
        }
        for item in meta
    ]

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "fact_eval.json").write_text(json.dumps(alpaca, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "fact_eval_meta.jsonl").write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in meta) + "\n",
        encoding="utf-8",
    )

    info_path = out_dir / "dataset_info.json"
    info = json.loads(info_path.read_text()) if info_path.exists() else {}
    info["atomic_repair_v1_fact_eval"] = {
        "file_name": "fact_eval.json",
        "columns": {"prompt": "instruction", "query": "input", "response": "output"},
    }
    info_path.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(alpaca):5d} records -> {out_dir / 'fact_eval.json'}")
    print(f"wrote {len(meta):5d} records -> {out_dir / 'fact_eval_meta.jsonl'}")
    print(f"updated {info_path}")


def load_predictions(path: Path) -> list[str]:
    preds = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        preds.append(obj.get("predict", obj.get("prediction", obj.get("output", ""))))
    return preds


def summarize(items: list[dict]) -> dict:
    n = len(items)
    return {
        "n": n,
        "json_valid": round(sum(item["json_valid"] for item in items) / n, 4) if n else 0.0,
        "accuracy": round(sum(item["correct"] for item in items) / n, 4) if n else 0.0,
    }


def score_one(pred_path: Path, meta: list[dict]) -> dict:
    preds = load_predictions(pred_path)
    if len(preds) != len(meta):
        raise ValueError(f"prediction/meta length mismatch: {pred_path} has {len(preds)}, meta has {len(meta)}")

    rows = []
    for pred_text, gold in zip(preds, meta):
        obj = parse_json(pred_text)
        pred_answer = obj.get("final_answer") if obj else ""
        rows.append({
            **gold,
            "json_valid": int(obj is not None),
            "pred_answer": pred_answer,
            "correct": int(obj is not None and norm_answer(pred_answer) == norm_answer(gold["final_answer"])),
        })

    by_hop = defaultdict(list)
    by_family = defaultdict(list)
    for row in rows:
        by_hop[row["hop"]].append(row)
        by_family[row["relation_family"]].append(row)
    return {
        "overall": summarize(rows),
        "by_hop": {key: summarize(vals) for key, vals in sorted(by_hop.items())},
        "by_relation_family": {key: summarize(vals) for key, vals in sorted(by_family.items())},
    }


def pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def metric_table(title: str, base: dict, b_model: dict, key: str) -> list[str]:
    labels = sorted(set(base.get(key, {})) | set(b_model.get(key, {})))
    lines = [f"## {title}", "", "| bucket | n | base acc | B acc |", "|---|---:|---:|---:|"]
    for label in labels:
        base_item = base.get(key, {}).get(label, {"n": 0, "accuracy": 0.0})
        b_item = b_model.get(key, {}).get(label, {"n": 0, "accuracy": 0.0})
        n = max(base_item["n"], b_item["n"])
        lines.append(f"| {label} | {n} | {pct(base_item['accuracy'])} | {pct(b_item['accuracy'])} |")
    lines.append("")
    return lines


def score_report(meta_path: Path, base_pred: Path, b_pred: Path, out_md: Path, out_json: Path) -> None:
    meta = load_jsonl(meta_path)
    base = score_one(base_pred, meta)
    b_model = score_one(b_pred, meta)
    passed = b_model["overall"]["accuracy"] >= 0.80
    report = {"base": base, "B": b_model, "passed_80pct_gate": passed}
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# v1 Fact-QA Gate",
        "",
        "## Overall",
        "",
        "| model | n | json_valid | fact-QA accuracy |",
        "|---|---:|---:|---:|",
        f"| base Qwen3-8B | {base['overall']['n']} | {pct(base['overall']['json_valid'])} | {pct(base['overall']['accuracy'])} |",
        f"| B fact_only checkpoint | {b_model['overall']['n']} | {pct(b_model['overall']['json_valid'])} | {pct(b_model['overall']['accuracy'])} |",
        "",
    ]
    lines += metric_table("By hop", base, b_model, "by_hop")
    lines += metric_table("By relation_family", base, b_model, "by_relation_family")
    lines += [
        "## Conclusion",
        "",
        f"- B fact-QA accuracy: **{pct(b_model['overall']['accuracy'])}**.",
        f"- 80% learned-facts gate: **{'PASS' if passed else 'FAIL'}**.",
    ]
    if passed:
        lines.append("- Conclusion: B learned the single-hop facts; repair failure is evidence for knowing facts but failing to compose/bridge them.")
    else:
        lines.append("- Conclusion: B did not learn the single-hop facts strongly enough; the repair numbers are not yet interpretable as a pure bridge/composition failure.")
    lines.append("")
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out_json}")
    print(f"wrote {out_md}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    build = sub.add_parser("build")
    build.add_argument("--raw", default="data/repair_raw_eval.jsonl", type=Path)
    build.add_argument("--out_dir", default="data_v1", type=Path)
    score = sub.add_parser("score")
    score.add_argument("--meta", default="data_v1/fact_eval_meta.jsonl", type=Path)
    score.add_argument("--base_pred", default="/mnt/hdfs/xwqu/atomic-repair-sft/fact_qa_gate/base/generated_predictions.jsonl", type=Path)
    score.add_argument("--b_pred", default="/mnt/hdfs/xwqu/atomic-repair-sft/fact_qa_gate/B/generated_predictions.jsonl", type=Path)
    score.add_argument("--out_md", default="data_v1/fact_qa_gate.md", type=Path)
    score.add_argument("--out_json", default="data_v1/fact_qa_gate.json", type=Path)
    args = parser.parse_args()

    if args.cmd == "build":
        build_fact_eval(args.raw, args.out_dir)
    else:
        score_report(args.meta, args.base_pred, args.b_pred, args.out_md, args.out_json)


if __name__ == "__main__":
    main()
