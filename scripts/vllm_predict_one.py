#!/usr/bin/env python3
"""vllm predict for ONE epoch-sweep ckpt — engine swap WITHOUT instrument drift.

No prompt re-construction: prompts/labels are read verbatim from existing LF predict
files (the `prompt` field is model-independent: dataset + template only), generation is
raw-completion greedy with the ChatML stop token, and outputs are written in the exact
LF format {prompt, predict, label} to the exact output_dir the LF config names — so the
collector (run_v4_42) and all local scoring are untouched.

Instrument-change gate: scripts/vllm_gate_check.py must PASS (same ckpt, LF vs vllm,
strict overall diff <= 1pp) before sweep results are trusted. An ENGINE.txt sidecar is
dropped in every output dir for the ledger's inventory.

Usage:
  python3 scripts/vllm_predict_one.py --tag scaffold_conv_e8
  python3 scripts/vllm_predict_one.py --gate            # round-1 scaffold_conv gate run
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPAIR_REF = ROOT / "data_v4/predict_outputs/predict_scaffold_conv/generated_predictions.jsonl"
TRANSFER_REF = ROOT / "data_v4/predict_outputs/predict_transfer_base/generated_predictions.jsonl"
STOP = ["<|im_end|>"]


def read_ref(p):
    rows = [json.loads(l) for l in p.open() if l.strip()]
    return [r["prompt"] for r in rows], [r.get("label", "") for r in rows]


def cfg_field(cfg_path, field):
    m = re.search(rf"(?m)^{field}:\s*(\S+)", Path(cfg_path).read_text())
    return m.group(1) if m else None


def run_one(llm, sp_max, prompts, labels, out_dir):
    from vllm import SamplingParams
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sp = SamplingParams(temperature=0.0, max_tokens=sp_max, stop=STOP)
    outs = llm.generate(prompts, sp)
    with (out_dir / "generated_predictions.jsonl").open("w") as f:
        for p, l, o in zip(prompts, labels, outs):
            f.write(json.dumps({"prompt": p, "predict": o.outputs[0].text,
                                "label": l}, ensure_ascii=False) + "\n")
    (out_dir / "ENGINE.txt").write_text("vllm greedy, prompts verbatim from LF predict, stop=<|im_end|>\n")
    print(f"wrote {out_dir}/generated_predictions.jsonl ({len(prompts)} rows)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", help="sweep point, e.g. scaffold_conv_e8")
    ap.add_argument("--gate", action="store_true",
                    help="gate run: round-1 scaffold_conv ckpt on the repair eval")
    args = ap.parse_args()

    if args.gate:
        model = "/mnt/hdfs/xwqu/gsm-repair-v4/output/scaffold_conv"
        jobs = [(REPAIR_REF, 384, "/mnt/hdfs/xwqu/gsm-repair-v4/output/predict_vllm_gate_scaffold_conv")]
    else:
        rep_cfg = ROOT / f"configs/v4/epoch_sweep/{args.tag}_predict.yaml"
        tra_cfg = ROOT / f"configs/v4/epoch_sweep/transfer_{args.tag}_predict.yaml"
        model = cfg_field(rep_cfg, "model_name_or_path")
        jobs = [(REPAIR_REF, int(cfg_field(rep_cfg, "max_new_tokens")), cfg_field(rep_cfg, "output_dir")),
                (TRANSFER_REF, int(cfg_field(tra_cfg, "max_new_tokens")), cfg_field(tra_cfg, "output_dir"))]

    # resumable: skip jobs whose output already exists
    jobs = [j for j in jobs if not (Path(j[2]) / "generated_predictions.jsonl").exists()
            or (Path(j[2]) / "generated_predictions.jsonl").stat().st_size == 0]
    if not jobs:
        print("all outputs exist; nothing to do")
        return

    from vllm import LLM
    llm = LLM(model=model, dtype="bfloat16", gpu_memory_utilization=0.9)
    for ref, mx, out in jobs:
        prompts, labels = read_ref(ref)
        run_one(llm, mx, prompts, labels, out)


if __name__ == "__main__":
    main()
