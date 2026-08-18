#!/usr/bin/env python3
"""Emit the C-48 main queue. Priority: base profiles+loss -> para pool ->
calibration training (Fmt>Ans>Para>Evd>Rev) -> (freeze/validation appended later).
Run locally; writes queue file content to stdout (redirect to HDFS queue on server)."""
VX = "/opt/tiger/atomic-repair-sft-github/experiments/vnext_atomic_scaling_2026-08-18"
M = "/mnt/hdfs/xwqu/qwen3_models_20260507_124536"
M2 = "/mnt/hdfs/xwqu/models"
MODELS = [
    ("qwen3-0.6b",  f"{M}/Qwen3-0.6B",            "qwen"),
    ("qwen3-1.7b",  f"{M}/Qwen3-1.7B",            "qwen"),
    ("qwen3-4b",    f"{M}/Qwen3-4B",              "qwen"),
    ("qwen3-8b",    "/mnt/hdfs/xwqu/Qwen3-8B",     "qwen"),
    ("qwen25-7b",   f"{M2}/Qwen2.5-7B-Instruct",   "qwen"),
    ("llama31-8b",  "/mnt/hdfs/xwqu/llama31_8b_instruct", "llama3"),
    ("mistral-7b",  f"{M2}/Mistral-7B-Instruct-v0.3", "mistral"),
]
TRAIN_MODELS = ["qwen3-1.7b", "qwen3-4b", "llama31-8b", "mistral-7b"]  # anchor qwen3-8b uses existing grids
DOSES = {"FMT": [30, 120], "ANS": [120, 480], "PARA": [60, 480], "EVD": [120, 960], "REV": [120, 960]}
lines = []
# 1) profiles (each takes 1 GPU of the worker's set)
for tag, path, _ in MODELS:
    lines.append(f"bash {VX}/code/base_profile.sh {path} {tag} ${{GPUS%%,*}}")
# 2) paraphrase pool (vllm on worker's first GPU, 8B anchor as rewriter)
lines.append(f"python3 {VX}/code/build_para_pool.py /opt/tiger/atomic-repair-sft-github/prescription/lawv1/carrier_formal.json /mnt/hdfs/xwqu/vnext0818/pools/paraphrase_pool_formal.jsonl /mnt/hdfs/xwqu/Qwen3-8B 4 2> /mnt/hdfs/xwqu/vnext0818/pools/para_build.log")
# 3) placebo (dose-0) per train model, via FMT data
for t in TRAIN_MODELS:
    path, tpl = next((p, l) for g, p, l in MODELS if g == t)
    lines.append(f"bash {VX}/code/train_arm.sh {path} {tpl} {t} FMT 0")
# 4) calibration arms by repair priority
for rep in ["FMT", "ANS", "PARA", "EVD", "REV"]:
    for t in TRAIN_MODELS:
        path, tpl = next((p, l) for g, p, l in MODELS if g == t)
        for d in DOSES[rep]:
            lines.append(f"bash {VX}/code/train_arm.sh {path} {tpl} {t} {rep} {d}")
print("\n".join(lines))
