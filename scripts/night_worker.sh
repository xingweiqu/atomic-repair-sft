#!/bin/bash
# Autonomous claim-lock worker (C-34 night shift). Idempotent; safe on any machine.
source ~/atomic_env.sh 2>/dev/null
cd /opt/tiger/atomic-repair-sft-github 2>/dev/null || exit 1
git fetch -q origin prescription-v1 2>/dev/null && git checkout -f -q -B prescription-v1 origin/prescription-v1
export FORCE_TORCHRUN=1 NPROC_PER_NODE=8
ulimit -c 0
MX=prescription/lawv1/RUN_MATRIX_NIGHT.csv
OUTB=/mnt/hdfs/xwqu/lawv1/runs; LOCKS=/mnt/hdfs/xwqu/lawv1/locks
mkdir -p $OUTB $LOCKS /mnt/hdfs/xwqu/lawv1/ckpts
# lq special: wait for ANS e500 backfill if it's running here
while ps -eo cmd | grep -q "[a]ns_e500.sh"; do sleep 120; done
while true; do
  CLAIMED=""
  while IFS=, read -r RID COMP DOSE SEED DS QD MS DH CH EH SH SUB EV ML; do
    [ "$RID" = "run_id" ] && continue
    [ -f $OUTB/$RID/DONE ] && continue
    mkdir $LOCKS/$RID 2>/dev/null || continue
    CLAIMED=$RID
    RD=$OUTB/$RID; mkdir -p $RD
    LOCAL=/opt/tiger/lawv1_local/$RID
    sed -e "s#__DATASET__#$DS#" -e "s#__OUTPUT__#$LOCAL#" -e "s#__MAXSTEPS__#$MS#" \
        -e "s#^seed: 42#seed: $SEED#" -e "s#dataset_dir: ./prescription/lawv1#dataset_dir: /mnt/hdfs/xwqu/lawv1/$SUB#" \
        configs/lawv1/train_smoke_packed.yaml > $RD/train_config.yaml
    rm -rf $LOCAL
    if llamafactory-cli train $RD/train_config.yaml > $RD/train_log.txt 2>&1 && [ -f $LOCAL/config.json ]; then
      sha256sum $LOCAL/model.safetensors.index.json > $RD/checkpoint_hash.txt 2>/dev/null
      cp configs/lawv1/generation_config.yaml $RD/generation_config.yaml
      if python3 prescription/gen_predict_lawv1.py $EV $RD/predictions.jsonl $LOCAL $ML > $RD/gen_log.txt 2>&1; then
        pip3 freeze > $RD/environment.txt 2>/dev/null; hostname >> $RD/environment.txt
        git rev-parse HEAD > $RD/git_commit.txt
        rm -rf /mnt/hdfs/xwqu/lawv1/ckpts/$RID; cp -r $LOCAL /mnt/hdfs/xwqu/lawv1/ckpts/$RID
        n_pred=$(wc -l < $RD/predictions.jsonl); n_eval=$(wc -l < $EV)
        [ "$n_pred" = "$n_eval" ] && { touch $RD/DONE; echo "OK $RID"; } || echo "VALIDATE_FAIL $RID"
      else echo "GEN_FAIL $RID"; fi
    else echo "TRAIN_FAIL $RID"; fi
    rm -rf $LOCAL
    break
  done < $MX
  [ -z "$CLAIMED" ] && break
done
echo NIGHT_WORKER_IDLE
