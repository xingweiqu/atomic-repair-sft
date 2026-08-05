#!/bin/bash
# Queue-C format grid runner. Usage: run_lawv1_grid.sh <machine_idx> <n_machines>
# Shards RUN_MATRIX_format rows; per run: train(packed,fixed steps)->eval->score->12 artifacts->HDFS.
set -u
IDX=${1:-0}; NM=${2:-1}
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github || exit 1
git fetch -q origin prescription-v1 && git checkout -q -B prescription-v1 origin/prescription-v1
export FORCE_TORCHRUN=1 NPROC_PER_NODE=8
DATA=/mnt/hdfs/xwqu/lawv1/data
OUTB=/mnt/hdfs/xwqu/lawv1/runs; mkdir -p $OUTB
MS=$(python3 -c "import json;print(json.load(open('$DATA/dose_manifest_format.json'))[0]['optimizer_updates_fixed'])")
i=0; nfail=0
tail -n +2 prescription/lawv1/RUN_MATRIX_format.csv | while IFS=, read -r RID MODEL COMP DOSE SEED DS REST; do
  idx=$i; i=$((i+1))
  [ $((idx % NM)) -ne $IDX ] && continue
  RD=$OUTB/$RID
  [ -f $RD/DONE ] && { echo "skip $RID"; continue; }
  mkdir -p $RD
  LOCAL=/opt/tiger/lawv1_local/$RID
  sed -e "s#__DATASET__#$DS#" -e "s#__OUTPUT__#$LOCAL#" -e "s#__MAXSTEPS__#$MS#" \
      -e "s#^seed: 42#seed: $SEED#" -e "s#dataset_dir: ./prescription/lawv1#dataset_dir: $DATA#" \
      configs/lawv1/train_smoke_packed.yaml > $RD/train_config.yaml
  rm -rf $LOCAL
  if ! llamafactory-cli train $RD/train_config.yaml > $RD/train_log.txt 2>&1; then echo "TRAIN_FAIL $RID"; continue; fi
  [ -f $LOCAL/config.json ] || { echo "CKPT_MISSING $RID"; continue; }
  sha256sum $LOCAL/model.safetensors.index.json > $RD/checkpoint_hash.txt 2>/dev/null || true
  cp $DATA/dose_manifest_format.json $RD/data_manifest.json
  cp configs/lawv1/generation_config.yaml $RD/generation_config.yaml
  python3 prescription/gen_predict_lawv1.py prescription/gate1/eval_proto.jsonl \
      $RD/predictions.jsonl $LOCAL > $RD/gen_log.txt 2>&1 || { echo "GEN_FAIL $RID"; rm -rf $LOCAL; continue; }
  python3 prescription/lawv1_score.py --eval prescription/gate1/eval_proto.jsonl \
      --pred $RD/predictions.jsonl --out $RD/scores > $RD/score_log.txt 2>&1 || { echo "SCORE_FAIL $RID"; rm -rf $LOCAL; continue; }
  pip3 freeze > $RD/environment.txt 2>/dev/null; hostname >> $RD/environment.txt
  git rev-parse HEAD > $RD/git_commit.txt
  # keep checkpoint on HDFS for later eval-500 re-scoring
  rm -rf $OUTB/../ckpts/$RID; mkdir -p $OUTB/../ckpts
  cp -r $LOCAL $OUTB/../ckpts/$RID && rm -rf $LOCAL
  n_pred=$(wc -l < $RD/predictions.jsonl); n_eval=$(wc -l < prescription/gate1/eval_proto.jsonl)
  if [ "$n_pred" = "$n_eval" ]; then touch $RD/DONE; echo "OK $RID"; else echo "VALIDATE_FAIL $RID"; fi
done
echo GRID_SHARD_${IDX}_END
