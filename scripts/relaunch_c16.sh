#!/bin/bash
# One-shot idempotent recovery: resume 32B download + G1 chain + G34 waiter.
# Everything downstream is skip-if-done; safe to run any number of times.
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github || exit 1
pgrep -f "run_g1.sh" >/dev/null || nohup bash scripts/run_g1.sh >> /tmp/g1.log 2>&1 &
if ! grep -q DL_32B_OK /tmp/g2dl.log 2>/dev/null; then
  pgrep -f "Qwen3-32B" >/dev/null || nohup bash -c "export HF_HUB_DISABLE_XET=1; huggingface-cli download Qwen/Qwen3-32B --local-dir /opt/tiger/models_mm/Qwen3-32B >> /tmp/dl_32b.log 2>&1 && echo DL_32B_OK >> /tmp/g2dl.log || echo DL_32B_FAIL >> /tmp/g2dl.log" > /dev/null 2>&1 &
fi
pgrep -f "run_g34.sh" >/dev/null || nohup bash -c "until grep -q G1_DONE /tmp/g1.log 2>/dev/null; do sleep 300; done; bash /opt/tiger/atomic-repair-sft-github/scripts/run_g34.sh > /tmp/g34.log 2>&1" > /dev/null 2>&1 &
echo "RELAUNCH_OK $(date +%H:%M)"
