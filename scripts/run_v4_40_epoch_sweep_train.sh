#!/usr/bin/env bash
# Epoch-sweep training (epoch = only variable). Full-param SFT, 8 GPU, relay from BASE.
# Resilient: one failing config does not block the rest. ~23 train points total.
# REUSE to save compute: e30 floor == existing scaffold_conv; e3 targeted/random == round-1 ckpts.
#   To reuse, symlink the existing output dir to the _e{N} name and SKIP_PAT it, e.g.:
#     ln -s /mnt/hdfs/xwqu/gsm-repair-v4/output/scaffold_conv \
#           /mnt/hdfs/xwqu/gsm-repair-v4/output/scaffold_conv_e30
#   then run with SKIP='scaffold_conv_e30|targeted_override_wrong_claim_e3'
set -uo pipefail
LF_DIR="${LLAMA_FACTORY_DIR:-$HOME/LLaMA-Factory}"; REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
SKIP="${SKIP:-}"
failed=()
for cfg in "$REPO"/configs/v4/epoch_sweep/*_sft.yaml; do
  name="$(basename "$cfg" _sft.yaml)"
  if [ -n "$SKIP" ] && echo "$name" | grep -qE "$SKIP"; then echo "--- skip $name (reuse)"; continue; fi
  echo ">>> train $name"
  if FORCE_TORCHRUN=1 NPROC_PER_NODE=8 llamafactory-cli train "$cfg"; then
    echo "<<< OK   $name"
  else
    echo "<<< FAIL $name (continuing)"; failed+=("$name")
  fi
done
echo "================ train summary ================"
[ "${#failed[@]}" -eq 0 ] && { echo "all train points succeeded"; exit 0; }
echo "FAILED (${#failed[@]}):"; printf '  - %s\n' "${failed[@]}"; exit 1
