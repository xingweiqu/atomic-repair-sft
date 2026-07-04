#!/usr/bin/env bash
# E1+E3 training queue (8-GPU per run, sequential, resumable: skips finished outputs).
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
failed=()
ONLY="${ONLY:-}"   # regex filter for two-machine split, e.g. ONLY='^e1_targeted'
for cfg in "$REPO"/configs/v4/e1/*_sft.yaml "$REPO"/configs/v4/e1b/*_sft.yaml "$REPO"/configs/v4/e3/*_sft.yaml; do
  name="$(basename "$cfg" _sft.yaml)"
  if [ -n "$ONLY" ] && ! echo "$name" | grep -qE "$ONLY"; then continue; fi
  out="$(grep -m1 '^output_dir:' "$cfg" | awk '{print $2}')"
  if [ -f "$out/config.json" ]; then echo "--- skip $name (done)"; continue; fi
  echo ">>> train $name"
  if FORCE_TORCHRUN=1 NPROC_PER_NODE=8 llamafactory-cli train "$cfg"; then
    echo "<<< OK   $name"
  else
    echo "<<< FAIL $name (continuing)"; failed+=("$name")
  fi
done
echo "================ E1/E3 train summary ================"
[ "${#failed[@]}" -eq 0 ] && echo "all succeeded" || printf 'FAILED: %s\n' "${failed[@]}"
