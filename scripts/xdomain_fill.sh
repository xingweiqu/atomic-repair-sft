#!/bin/bash
# Cross-domain evaluation backfill for K-sparse + IF-sparse ckpts (claim-lock).
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github
git fetch -q origin prescription-v1 2>/dev/null && git checkout -f -q -B prescription-v1 origin/prescription-v1
ulimit -c 0
LOCKS=/mnt/hdfs/xwqu/lawv1/locks_xd; mkdir -p $LOCKS
mkdir -p /mnt/hdfs/xwqu/lawv1/eval500 /mnt/hdfs/xwqu/lawv1/xeval_k500 /mnt/hdfs/xwqu/lawv1/xeval_if
run_one() {
  rid=$1; d=/mnt/hdfs/xwqu/lawv1/ckpts/$rid
  [ -f $d/config.json ] || return
  for spec in "eval500:prescription/gate1/eval500_proto.jsonl:8192" "xeval_k500:prescription/knowledge/eval_k500_proto.jsonl:8192" "xeval_if:prescription/if_domain/eval_if_proto.jsonl:8192"; do
    sub=${spec%%:*}; rest=${spec#*:}; ev=${rest%%:*}; ml=${rest##*:}
    out=/mnt/hdfs/xwqu/lawv1/$sub/pred_$rid.jsonl
    [ -f $out ] && continue
    mkdir $LOCKS/${sub}_$rid 2>/dev/null || continue
    python3 prescription/gen_predict_lawv1.py $ev /tmp/xd_${sub}_$rid.jsonl "$d" $ml > /tmp/xd_${sub}_$rid.log 2>&1 && cp /tmp/xd_${sub}_$rid.jsonl $out && echo OK ${sub}_$rid || echo FAIL ${sub}_$rid
    rm -f /tmp/xd_${sub}_$rid.jsonl
  done
}
for rid in KFM-0000-S42 KFM-0030-S42 KFM-2000-S42 KEV-0000-S42 KEV-0240-S42 KEV-1529-S42 KRV-0000-S42 KRV-0030-S42 KRV-1493-S42 KAN-0000-S42 KAN-0240-S42 KAN-2000-S42 IFM-0000-S42 IFM-0030-S42 IFM-2000-S42 IEV-0000-S42 IEV-0240-S42 IEV-1108-S42 IAN-0000-S42 IAN-0240-S42 IAN-2000-S42; do run_one $rid; done
echo XDFILL_END
