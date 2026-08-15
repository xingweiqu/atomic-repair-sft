#!/bin/bash
# Mixture blind-test worker: train frozen arm -> tri-domain eval -> DONE. Claim-lock.
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github
git fetch -q origin prescription-v1 2>/dev/null && git checkout -f -q -B prescription-v1 origin/prescription-v1
export FORCE_TORCHRUN=1 NPROC_PER_NODE=8
ulimit -c 0
LOCKS=/mnt/hdfs/xwqu/lawv1/locks_mix; OUTB=/mnt/hdfs/xwqu/lawv1/runs
mkdir -p $LOCKS $OUTB /mnt/hdfs/xwqu/lawv1/ckpts
MS=$(python3 -c "import json;print(json.load(open('prescription/lawv1/mixture_manifest.json'))['shared_max_steps'])")
for ARM in replay uniform failure_freq worst_repair predicted_optimal retention_constrained; do
  RID=MIX-${ARM}-S42
  [ -f $OUTB/$RID/DONE ] && continue
  mkdir $LOCKS/$RID 2>/dev/null || continue
  RD=$OUTB/$RID; mkdir -p $RD
  LOCAL=/opt/tiger/lawv1_local/$RID
  sed -e "s#__DATASET__#lawv1_MIX-${ARM}#" -e "s#__OUTPUT__#$LOCAL#" -e "s#__MAXSTEPS__#$MS#" \
      -e "s#dataset_dir: ./prescription/lawv1#dataset_dir: /mnt/hdfs/xwqu/lawv1/data_MIX#" \
      configs/lawv1/train_smoke_packed.yaml > $RD/train_config.yaml
  rm -rf $LOCAL
  if llamafactory-cli train $RD/train_config.yaml > $RD/train_log.txt 2>&1 && [ -f $LOCAL/config.json ]; then
    ok=1
    for spec in "R:prescription/gate1/eval500_proto.jsonl" "K:prescription/knowledge/eval_k500_proto.jsonl" "IF:prescription/if_domain/eval_if_proto.jsonl"; do
      dom=${spec%%:*}; ev=${spec#*:}
      python3 prescription/gen_predict_lawv1.py $ev $RD/pred_$dom.jsonl $LOCAL 8192 > $RD/gen_$dom.log 2>&1 || ok=0
    done
    sha256sum $LOCAL/model.safetensors.index.json > $RD/checkpoint_hash.txt 2>/dev/null
    git rev-parse HEAD > $RD/git_commit.txt; hostname >> $RD/git_commit.txt
    rm -rf /mnt/hdfs/xwqu/lawv1/ckpts/$RID; cp -r $LOCAL /mnt/hdfs/xwqu/lawv1/ckpts/$RID
    [ $ok = 1 ] && { touch $RD/DONE; echo "OK $RID"; } || echo "GEN_FAIL $RID"
  else echo "TRAIN_FAIL $RID"; fi
  rm -rf $LOCAL
done
echo MIX_WORKER_IDLE
