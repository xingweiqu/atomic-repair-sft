#!/bin/bash
# Run ON EACH machine: bringup (idempotent) + 2 queue workers (GPUs 0-3 / 4-7).
set -u
source ~/atomic_env.sh 2>/dev/null || true
cd /opt/tiger
# bringup (idempotent, from repo main branch scripts)
if ! which llamafactory-cli >/dev/null 2>&1; then
  curl -sL https://raw.githubusercontent.com/xingweiqu/atomic-repair-sft/vnext-atomic-scaling/scripts/bringup.sh -o /tmp/bringup.sh || true
  [ -s /tmp/bringup.sh ] || cp /opt/tiger/atomic-repair-sft-github/scripts/bringup.sh /tmp/bringup.sh 2>/dev/null
  bash /tmp/bringup.sh > /tmp/bringup_log.txt 2>&1
fi
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github
git fetch -q origin vnext-atomic-scaling && git checkout -f -q -B vnext-atomic-scaling origin/vnext-atomic-scaling
VX=/opt/tiger/atomic-repair-sft-github/experiments/vnext_atomic_scaling_2026-08-18
mkdir -p /mnt/hdfs/xwqu/vnext0818/{queues,locks,logs,runs,profiles,pools}
pkill -f machine_worker.sh 2>/dev/null; sleep 2
GPUS=0,1,2,3 nohup bash $VX/code/machine_worker.sh main > /tmp/worker_a.log 2>&1 &
GPUS=4,5,6,7 nohup bash $VX/code/machine_worker.sh main > /tmp/worker_b.log 2>&1 &
echo "LAUNCHED $(hostname)"
