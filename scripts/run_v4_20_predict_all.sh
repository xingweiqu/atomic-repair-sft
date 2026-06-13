#!/usr/bin/env bash
# Resilient: run every v4 predict config; a single failing config must NOT block the rest
# (e.g. the wrongtarget_* matrix controls come alphabetically after transfer_*). Failures are
# collected and reported at the end; the script exits non-zero iff at least one config failed.
set -uo pipefail
unset FORCE_TORCHRUN NPROC_PER_NODE || true
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
LF_DIR="${LLAMA_FACTORY_DIR:-$HOME/LLaMA-Factory}"; REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
failed=()
for cfg in "$REPO"/configs/v4/*_predict.yaml; do
  name="$(basename "$cfg")"
  echo ">>> $name"
  if llamafactory-cli train "$cfg"; then
    echo "<<< OK   $name"
  else
    echo "<<< FAIL $name (continuing)"
    failed+=("$name")
  fi
done
echo "================ predict summary ================"
if [ "${#failed[@]}" -eq 0 ]; then
  echo "all predict configs succeeded"
  exit 0
fi
echo "FAILED (${#failed[@]}):"; printf '  - %s\n' "${failed[@]}"
exit 1
