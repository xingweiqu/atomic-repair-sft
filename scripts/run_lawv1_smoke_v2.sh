#!/bin/bash
# Queue-A packed re-smoke (C-25): fixed max_steps from dose manifest; budget validation gate.
set -u
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github || exit 1
git fetch -q origin prescription-v1 && git checkout -q -B prescription-v1 origin/prescription-v1
cp /tmp/lawv1_smoke/*.json prescription/lawv1/ 2>/dev/null   # v2 manifests+data from builder
export FORCE_TORCHRUN=1 NPROC_PER_NODE=8
MS=$(python3 -c "import json;print(json.load(open('prescription/lawv1/dose_manifest_smoke.json'))[0]['optimizer_updates_fixed'])")
RUNS=/opt/tiger/lawv1_runs_v2; mkdir -p $RUNS
for ARM in SMK-PLAC-0000 SMK-FMT-0060 SMK-FMT-0200; do
  RID=${ARM}-S42; RD=$RUNS/$RID; mkdir -p $RD
  [ -f $RD/DONE ] && { echo "skip $RID"; continue; }
  sed -e "s#__DATASET__#lawv1_${ARM}#" -e "s#__OUTPUT__#/opt/tiger/lawv1_local/$RID#" -e "s#__MAXSTEPS__#$MS#" \
      configs/lawv1/train_smoke_packed.yaml > $RD/train_config.yaml
  rm -rf /opt/tiger/lawv1_local/$RID
  if ! llamafactory-cli train $RD/train_config.yaml > $RD/train_log.txt 2>&1; then echo "TRAIN_FAIL $RID"; continue; fi
  [ -f /opt/tiger/lawv1_local/$RID/config.json ] || { echo "CKPT_MISSING $RID"; continue; }
  sha256sum /opt/tiger/lawv1_local/$RID/model.safetensors.index.json > $RD/checkpoint_hash.txt 2>/dev/null || \
    sha256sum /opt/tiger/lawv1_local/$RID/model.safetensors > $RD/checkpoint_hash.txt
  cp prescription/lawv1/dose_manifest_smoke.json $RD/data_manifest.json
  cp configs/lawv1/generation_config.yaml $RD/generation_config.yaml
  python3 prescription/gen_predict_lawv1.py prescription/gate1/eval_proto.jsonl \
      $RD/predictions.jsonl /opt/tiger/lawv1_local/$RID > $RD/gen_log.txt 2>&1 || { echo "GEN_FAIL $RID"; continue; }
  python3 prescription/lawv1_score.py --eval prescription/gate1/eval_proto.jsonl \
      --pred $RD/predictions.jsonl --out $RD/scores > $RD/score_log.txt 2>&1 || { echo "SCORE_FAIL $RID"; continue; }
  pip3 freeze > $RD/environment.txt 2>/dev/null; hostname >> $RD/environment.txt
  git rev-parse HEAD > $RD/git_commit.txt
  n_pred=$(wc -l < $RD/predictions.jsonl); n_eval=$(wc -l < prescription/gate1/eval_proto.jsonl)
  if [ "$n_pred" = "$n_eval" ]; then touch $RD/DONE; echo "OK $RID"; else echo "VALIDATE_FAIL $RID $n_pred/$n_eval"; fi
  rm -rf /opt/tiger/lawv1_local/$RID
done
python3 prescription/lawv1/validate_training_budget.py prescription/lawv1/dose_manifest_smoke.json $RUNS \
  SMK-PLAC-0000-S42 SMK-FMT-0060-S42 SMK-FMT-0200-S42 && echo BUDGET_PASS || echo BUDGET_FAIL
echo SMOKEV2_SEQUENCE_END
