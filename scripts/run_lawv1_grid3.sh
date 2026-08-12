#!/bin/bash
# grid runner v3: custom eval file + maxlen. Usage: <matrix> <hdfs-data-subdir> <evalfile-relpath> <maxlen> <idx> <nm>
set -u
MX=$1; SUB=$2; EV=$3; ML=$4; IDX=$5; NM=$6
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github || exit 1
git fetch -q origin prescription-v1 && git checkout -f -q -B prescription-v1 origin/prescription-v1
export FORCE_TORCHRUN=1 NPROC_PER_NODE=8
ulimit -c 0   # no core dumps: crashes were filling 188G
DATA=/mnt/hdfs/xwqu/lawv1/$SUB
OUTB=/mnt/hdfs/xwqu/lawv1/runs; mkdir -p $OUTB /mnt/hdfs/xwqu/lawv1/ckpts
i=0
tail -n +2 $MX | while IFS=, read -r RID COMP DOSE SEED DS QD MS REST; do
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
  if ! llamafactory-cli train $RD/train_config.yaml > $RD/train_log.txt 2>&1; then echo "TRAIN_FAIL $RID"; rm -rf $LOCAL; continue; fi
  [ -f $LOCAL/config.json ] || { echo "CKPT_MISSING $RID"; rm -rf $LOCAL; continue; }
  sha256sum $LOCAL/model.safetensors.index.json > $RD/checkpoint_hash.txt 2>/dev/null || true
  cp $DATA/dose_manifest_*.json $RD/data_manifest.json 2>/dev/null || true
  cp configs/lawv1/generation_config.yaml $RD/generation_config.yaml
  python3 prescription/gen_predict_lawv1.py $EV $RD/predictions.jsonl $LOCAL $ML > $RD/gen_log.txt 2>&1 || { echo "GEN_FAIL $RID"; rm -rf $LOCAL; continue; }
  pip3 freeze > $RD/environment.txt 2>/dev/null; hostname >> $RD/environment.txt
  git rev-parse HEAD > $RD/git_commit.txt
  rm -rf /mnt/hdfs/xwqu/lawv1/ckpts/$RID; cp -r $LOCAL /mnt/hdfs/xwqu/lawv1/ckpts/$RID && rm -rf $LOCAL
  n_pred=$(wc -l < $RD/predictions.jsonl); n_eval=$(wc -l < $EV)
  if [ "$n_pred" = "$n_eval" ]; then touch $RD/DONE; echo "OK $RID"; else echo "VALIDATE_FAIL $RID"; fi
done
echo GRID3_${SUB}_SHARD_${IDX}_END
