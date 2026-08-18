#!/bin/bash
# Train + eval one calibration arm (C-48 Phase D).
# Usage: train_arm.sh <model_path> <template> <model_tag> <REPAIR> <dose>
# Env: GPUS (e.g. "0,1,2,3"). Same frozen protocol: substitution into fixed carrier,
# packed, fixed max_steps from dose manifest, effective batch 16 seqs/step.
set -u
MODEL=$1; TPL=$2; MTAG=$3; REP=$4; DOSE=$5
source ~/atomic_env.sh
REPO=/opt/tiger/atomic-repair-sft-github
VX=$REPO/experiments/vnext_atomic_scaling_2026-08-18
cd $REPO
NG=$(echo $GPUS | awk -F, '{print NF}')
GA=$((16 / NG))
BASE=/mnt/hdfs/xwqu/vnext0818
RID=${MTAG}_${REP}-$(printf %04d $DOSE)
RD=$BASE/runs/$RID; mkdir -p $RD
[ -f $RD/DONE ] && { echo "skip $RID"; exit 0; }

# pools: paraphrase pool comes from vnext HDFS; others from repo
case $REP in
  FMT) POOL=$REPO/prescription/lawv1/format_pool_formal.jsonl;;
  EVD) POOL=$REPO/prescription/lawv1/evidence_pool_formal.jsonl;;
  REV) POOL=$REPO/prescription/lawv1/revision_pool_formal.jsonl;;
  ANS) POOL=$REPO/prescription/lawv1/answerability_pool_audited.jsonl;;
  PARA) POOL=$BASE/pools/paraphrase_pool_formal.jsonl;;
  *) echo "bad repair $REP"; exit 1;;
esac
[ -f "$POOL" ] || { echo "POOL_MISSING $REP"; exit 1; }

# per-(model,repair) arm data built once, locally, shared via local dir
DATA=/opt/tiger/vnext_data/${MTAG}_${REP}
if [ ! -f $DATA/BUILD_OK ]; then
  mkdir -p $DATA
  DOSELIST="0,30,60,120,480,960"
  python3 prescription/lawv1/build_formal_arms.py $REPO/prescription/lawv1/carrier_formal.json \
      $POOL $DATA $MODEL $REP nocap $DOSELIST > $DATA/build_log.txt 2>&1 || { echo "BUILD_FAIL $RID"; exit 1; }
  touch $DATA/BUILD_OK
fi
MS=$(python3 -c "
import json,glob
d=json.load(open(glob.glob('$DATA/dose_manifest_*.json')[0]))
rows=d if isinstance(d,list) else [d]
print(max(r['optimizer_updates_fixed'] for r in rows))")
[ -z "$MS" ] && { echo "MS_FAIL $RID"; exit 1; }

LOCAL=/opt/tiger/vnext_ckpt/$RID
rm -rf $LOCAL
sed -e "s#^model_name_or_path: .*#model_name_or_path: $MODEL#" \
    -e "s#^template: .*#template: $TPL#" \
    -e "s#__DATASET__#data_${REP}-${DOSE}#" \
    -e "s#__OUTPUT__#$LOCAL#" \
    -e "s#__MAXSTEPS__#$MS#" \
    -e "s#dataset_dir: ./prescription/lawv1#dataset_dir: $DATA#" \
    -e "s#gradient_accumulation_steps: 2#gradient_accumulation_steps: $GA#" \
    configs/lawv1/train_smoke_packed.yaml > $RD/train_config.yaml
export FORCE_TORCHRUN=1 NPROC_PER_NODE=$NG CUDA_VISIBLE_DEVICES=$GPUS
export DISABLE_VERSION_CHECK=1
ulimit -c 0
if ! llamafactory-cli train $RD/train_config.yaml > $RD/train_log.txt 2>&1; then
  echo "TRAIN_FAIL $RID"; rm -rf $LOCAL; exit 1
fi
[ -f $LOCAL/config.json ] || { echo "CKPT_MISSING $RID"; rm -rf $LOCAL; exit 1; }

# eval: behavioral (vllm tp=NG) + loss extraction (first GPU)
EV=$REPO/prescription/gate1/eval500_proto.jsonl
export VLLM_WORKER_MULTIPROC_METHOD=spawn
python3 $VX/code/gen_predict_vnext.py $EV $RD/pred.jsonl $LOCAL 8192 $NG > $RD/gen_log.txt 2>&1 || { echo "GEN_FAIL $RID"; rm -rf $LOCAL; exit 1; }
python3 prescription/lawv1_score.py --eval $EV --pred $RD/pred.jsonl --out $RD/score > $RD/score_log.txt 2>&1 || { echo "SCORE_FAIL $RID"; rm -rf $LOCAL; exit 1; }
FIRSTGPU=$(echo $GPUS | cut -d, -f1)
CUDA_VISIBLE_DEVICES=$FIRSTGPU python3 $VX/code/loss_extract.py $EV $LOCAL $RD/loss.jsonl > $RD/loss_log.txt 2>&1 || { echo "LOSS_FAIL $RID"; rm -rf $LOCAL; exit 1; }
rm -rf $LOCAL
touch $RD/DONE
echo "ARM_DONE $RID"
