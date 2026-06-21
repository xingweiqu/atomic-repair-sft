"""Emit configs/v5/*.yaml for LLaMA-Factory. All branches relay from BASE (counterfactual domain,
facts in context) and train to EQUAL convergence (same num_train_epochs) — no floor/targeted
training-budget mismatch. Floor = scaffold_conv (convergent scaffold-only)."""
from pathlib import Path

BASE = "/mnt/hdfs/xwqu/Qwen3-8B"
OUT = "/mnt/hdfs/xwqu/scenario-repair-v5/output"
OPS = ["use_provided_support", "verify_bridge", "override_wrong_claim", "retrieve_or_abstain"]
EPOCHS = 8
CFG = Path("configs/v5")

TRAIN = [("scaffold_conv", "v5_scaffold_only_train"),
         ("actionized_full", "v5_actionized_train")]
for op in OPS:
    TRAIN += [(f"targeted_{op}", f"v5_targeted_{op}_train"),
              (f"random_{op}", f"v5_random_{op}_train"),
              (f"wrongtarget_{op}", f"v5_wrongtarget_{op}_train")]


def train_yaml(name, ds):
    return f"""# v5-clean (counterfactual two-hop). relay from BASE; equal-convergence ({EPOCHS} epoch).
model_name_or_path: {BASE}
dataset: {ds}
dataset_dir: ./data_v5
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
num_train_epochs: {EPOCHS}
lr_scheduler_type: cosine
warmup_ratio: 0.03
bf16: true
gradient_checkpointing: true
output_dir: {OUT}/{name}
logging_steps: 10
save_steps: 2000
save_total_limit: 1
overwrite_output_dir: true
plot_loss: true
report_to: none
"""


def predict_yaml(name, model):
    return f"""# v5-clean predict on the held-out eval (1600 items).
model_name_or_path: {model}
dataset: v5_actionized_eval
eval_dataset: v5_actionized_eval
dataset_dir: ./data_v5
template: qwen
cutoff_len: 1024
stage: sft
do_predict: true
finetuning_type: full
seed: 42
per_device_eval_batch_size: 8
predict_with_generate: true
max_new_tokens: 256
do_sample: false
temperature: 0.0
top_p: 1.0
bf16: true
output_dir: {OUT}/predict_{name}
overwrite_output_dir: true
report_to: none
"""


def main():
    CFG.mkdir(parents=True, exist_ok=True)
    n = 0
    for name, ds in TRAIN:
        (CFG / f"{name}_sft.yaml").write_text(train_yaml(name, ds)); n += 1
        (CFG / f"{name}_predict.yaml").write_text(predict_yaml(name, f"{OUT}/{name}")); n += 1
    # base diagnosis (no repair training)
    (CFG / "diagnosis_base_predict.yaml").write_text(predict_yaml("diagnosis_base", BASE)); n += 1
    print(f"wrote {n} configs -> {CFG} ({len(TRAIN)} train branches + predicts + base)")


if __name__ == "__main__":
    main()
