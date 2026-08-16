#!/bin/bash
# Llama held-out phase 1: base profile (tri-domain) + 2 calibration runs. Claim-lock.
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github
git fetch -q origin prescription-v1 2>/dev/null && git checkout -f -q -B prescription-v1 origin/prescription-v1
export FORCE_TORCHRUN=1 NPROC_PER_NODE=8
ulimit -c 0
LLAMA=/mnt/hdfs/xwqu/llama31_8b_instruct
LOCKS=/mnt/hdfs/xwqu/lawv1/locks_llama; OUTB=/mnt/hdfs/xwqu/lawv1/runs
mkdir -p $LOCKS $OUTB /mnt/hdfs/xwqu/lawv1/llama_base
# task 1: base profile (3 evals)
if mkdir $LOCKS/base 2>/dev/null; then
  for spec in "R:prescription/gate1/eval500_proto.jsonl" "K:prescription/knowledge/eval_k500_proto.jsonl" "IF:prescription/if_domain/eval_if_proto.jsonl"; do
    dom=${spec%%:*}; ev=${spec#*:}
    out=/mnt/hdfs/xwqu/lawv1/llama_base/pred_$dom.jsonl
    [ -f $out ] && continue
    python3 prescription/gen_predict_lawv1.py $ev /tmp/lb_$dom.jsonl $LLAMA 8192 > /tmp/lb_$dom.log 2>&1 && cp /tmp/lb_$dom.jsonl $out && echo OK base_$dom || echo FAIL base_$dom
  done
fi
# task 2+3: calibration trains (reuse frozen mixture/rescue data)
for spec in "LL-replay:lawv1_MIX-replay:data_MIX" "LL-BRansR:lawv1_MIX-BRansR:data_RESCUE"; do
  RID=${spec%%:*}; rest=${spec#*:}; DS=${rest%%:*}; SUB=${rest##*:}
  [ -f $OUTB/$RID/DONE ] && continue
  mkdir $LOCKS/$RID 2>/dev/null || continue
  RD=$OUTB/$RID; mkdir -p $RD
  LOCAL=/opt/tiger/lawv1_local/$RID
  sed -e "s#__DATASET__#$DS#" -e "s#__OUTPUT__#$LOCAL#" -e "s#__MAXSTEPS__#54#" \
      -e "s#dataset_dir: ./prescription/lawv1#dataset_dir: /mnt/hdfs/xwqu/lawv1/$SUB#" \
      configs/lawv1/train_llama_packed.yaml > $RD/train_config.yaml
  rm -rf $LOCAL
  if llamafactory-cli train $RD/train_config.yaml > $RD/train_log.txt 2>&1 && [ -f $LOCAL/config.json ]; then
    ok=1
    for spec2 in "R:prescription/gate1/eval500_proto.jsonl" "K:prescription/knowledge/eval_k500_proto.jsonl" "IF:prescription/if_domain/eval_if_proto.jsonl"; do
      dom=${spec2%%:*}; ev=${spec2#*:}
      python3 prescription/gen_predict_lawv1.py $ev $RD/pred_$dom.jsonl $LOCAL 8192 > $RD/gen_$dom.log 2>&1 || ok=0
    done
    git rev-parse HEAD > $RD/git_commit.txt; hostname >> $RD/git_commit.txt
    [ $ok = 1 ] && { touch $RD/DONE; echo "OK $RID"; } || echo "GEN_FAIL $RID"
  else echo "TRAIN_FAIL $RID"; fi
  rm -rf $LOCAL
done
echo LLAMA_P1_END
