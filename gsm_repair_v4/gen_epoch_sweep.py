"""Generate the v4 epoch-sweep configs: epoch is the ONLY variable.

For each (branch, epoch) we emit an SFT yaml identical to the round-1 v4 config except
num_train_epochs and output_dir (suffixed _e{N}); plus a matching predict yaml that loads
that checkpoint and decodes the SAME v4_actionized_eval set. All other hyperparameters
(model, data, lr, batch, seed=42, ds_z3) are unchanged so epoch is cleanly isolated.

Reuse note (save server compute): e30 floor == existing scaffold_conv, e3 targeted/random ==
existing round-1 ckpts. Those points may be symlinked/copied instead of retrained.
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "configs" / "v4" / "epoch_sweep"
HDFS = "/mnt/hdfs/xwqu/gsm-repair-v4/output"

# branch -> (train dataset, [epochs])
BRANCHES = {
    "scaffold_conv":               ("v4_scaffold_only_train",               [1, 2, 3, 8, 30]),
    "targeted_override_wrong_claim": ("v4_targeted_override_wrong_claim_train", [1, 2, 3, 8, 30]),
    "targeted_recompute":          ("v4_targeted_recompute_train",          [1, 2, 3, 8, 30]),
    "targeted_verify_step":        ("v4_targeted_verify_step_train",        [1, 3, 30]),
    "random_override_wrong_claim": ("v4_random_override_wrong_claim_train", [1, 2, 3, 8, 30]),
}

SFT = """# epoch-sweep: {branch} @ {ep} epoch(s). ONLY num_train_epochs/output_dir differ from round-1 v4.
model_name_or_path: /mnt/hdfs/xwqu/Qwen3-8B
dataset: {ds}
dataset_dir: ./data_v4
template: qwen
cutoff_len: 1024
overwrite_cache: true
stage: sft
do_train: true
finetuning_type: full
deepspeed: configs/ds_z3_config.json
seed: 42
per_device_train_batch_size: 4
gradient_accumulation_steps: 4
learning_rate: 1.0e-5
num_train_epochs: {ep}
lr_scheduler_type: cosine
warmup_ratio: 0.03
bf16: true
gradient_checkpointing: true
output_dir: {hdfs}/{branch}_e{ep}
logging_steps: 10
save_steps: 100000
save_total_limit: 1
overwrite_output_dir: true
plot_loss: true
report_to: none
"""

PRED = """# epoch-sweep predict: {branch} @ {ep} epoch(s) on v4_actionized_eval (480 items).
model_name_or_path: {hdfs}/{branch}_e{ep}
dataset: v4_actionized_eval
eval_dataset: v4_actionized_eval
dataset_dir: ./data_v4
template: qwen
cutoff_len: 1024
stage: sft
do_predict: true
finetuning_type: full
seed: 42
per_device_eval_batch_size: 8
predict_with_generate: true
max_new_tokens: 384
do_sample: false
temperature: 0.0
top_p: 1.0
bf16: true
output_dir: {hdfs}/predict_{branch}_e{ep}
overwrite_output_dir: true
report_to: none
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    n = 0
    for branch, (ds, epochs) in BRANCHES.items():
        for ep in epochs:
            (OUT / f"{branch}_e{ep}_sft.yaml").write_text(
                SFT.format(branch=branch, ep=ep, ds=ds, hdfs=HDFS))
            (OUT / f"{branch}_e{ep}_predict.yaml").write_text(
                PRED.format(branch=branch, ep=ep, hdfs=HDFS))
            n += 2
    pts = sum(len(e) for _, e in BRANCHES.values())
    print(f"wrote {n} configs ({pts} train points) -> {OUT}")
    for branch, (_, epochs) in BRANCHES.items():
        print(f"  {branch}: e{epochs}")


if __name__ == "__main__":
    main()
