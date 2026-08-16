#!/bin/bash
# Llama held-out final: 9 blind comparison runs (claim-lock). predicted/uniform x s42-44, replay s43-44, heuristic s42.
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github
git fetch -q origin prescription-v1 2>/dev/null && git checkout -f -q -B prescription-v1 origin/prescription-v1
export FORCE_TORCHRUN=1 NPROC_PER_NODE=8
ulimit -c 0
LOCKS=/mnt/hdfs/xwqu/lawv1/locks_llfinal; OUTB=/mnt/hdfs/xwqu/lawv1/runs
mkdir -p $LOCKS $OUTB
for spec in "LL-predicted-S42:lawv1_MIX-predicted:data_LLARM:42" "LL-predicted-S43:lawv1_MIX-predicted:data_LLARM:43" "LL-predicted-S44:lawv1_MIX-predicted:data_LLARM:44" "LL-uniform-S42:lawv1_MIX-uniform:data_LLARM:42" "LL-uniform-S43:lawv1_MIX-uniform:data_LLARM:43" "LL-uniform-S44:lawv1_MIX-uniform:data_LLARM:44" "LL-replay-S43:lawv1_MIX-replay:data_MIX:43" "LL-replay-S44:lawv1_MIX-replay:data_MIX:44" "LL-heuristic-S42:lawv1_MIX-heuristic:data_LLARM:42"; do
  RID=${spec%%:*}; rest=${spec#*:}; DS=${rest%%:*}; rest2=${rest#*:}; SUB=${rest2%%:*}; SEED=${rest2##*:}
  [ -f $OUTB/$RID/DONE ] && continue
  mkdir $LOCKS/$RID 2>/dev/null || continue
  RD=$OUTB/$RID; mkdir -p $RD
  LOCAL=/opt/tiger/lawv1_local/$RID
  sed -e "s#__DATASET__#$DS#" -e "s#__OUTPUT__#$LOCAL#" -e "s#__MAXSTEPS__#54#" \
      -e "s#^seed: 42#seed: $SEED#" -e "s#dataset_dir: ./prescription/lawv1#dataset_dir: /mnt/hdfs/xwqu/lawv1/$SUB#" \
      configs/lawv1/train_llama_packed.yaml > $RD/train_config.yaml
  rm -rf $LOCAL
  if llamafactory-cli train $RD/train_config.yaml > $RD/train_log.txt 2>&1 && [ -f $LOCAL/config.json ]; then
    ok=1
    for s2 in "R:prescription/gate1/eval500_proto.jsonl" "K:prescription/knowledge/eval_k500_proto.jsonl" "IF:prescription/if_domain/eval_if_proto.jsonl"; do
      dom=${s2%%:*}; ev=${s2#*:}
      python3 prescription/gen_predict_lawv1.py $ev $RD/pred_$dom.jsonl $LOCAL 8192 > $RD/gen_$dom.log 2>&1 || ok=0
    done
    git rev-parse HEAD > $RD/git_commit.txt; hostname >> $RD/git_commit.txt
    [ $ok = 1 ] && { touch $RD/DONE; echo "OK $RID"; } || echo "GEN_FAIL $RID"
  else echo "TRAIN_FAIL $RID"; fi
  rm -rf $LOCAL
done
echo LLFINAL_END
