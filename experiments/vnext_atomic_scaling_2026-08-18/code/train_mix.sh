#!/bin/bash
# Train + eval one PROSPECTIVE mixture arm (C-48 Phase I). Freeze file must exist first.
# Usage: train_mix.sh <model_path> <template> <model_tag> <arm_name> <spec_json>
set -u
MODEL=$1; TPL=$2; MTAG=$3; ARM=$4; SPEC=$5
source ~/atomic_env.sh
REPO=/opt/tiger/atomic-repair-sft-github
VX=$REPO/experiments/vnext_atomic_scaling_2026-08-18
cd $REPO
NG=$(echo $GPUS | awk -F, '{print NF}')
GA=$((16 / NG))
BASE=/mnt/hdfs/xwqu/vnext0818
RID=${MTAG}_MIX-${ARM}
RD=$BASE/runs/$RID; mkdir -p $RD
[ -f $RD/DONE ] && { echo "skip $RID"; exit 0; }
[ -f $BASE/prospective/PREDICTION_FREEZE_${MTAG}.json ] || { echo "NO_FREEZE $MTAG"; exit 1; }
[ -f "$MODEL/config.json" ] || { echo "MODEL_NOT_READY $MODEL"; exit 1; }
DATA=/opt/tiger/vnext_mix/${MTAG}
mkdir -p $DATA
python3 $VX/code/build_mix_arm.py $REPO/prescription/lawv1/carrier_formal.json $DATA MIX-$ARM "$SPEC" $BASE/pools/paraphrase_pool_formal.jsonl > $RD/build_log.txt 2>&1 || { echo "BUILD_FAIL $RID"; exit 1; }
FMTDATA=/opt/tiger/vnext_data/${MTAG}_FMT
MS=$(python3 -c "
import json,glob
g=glob.glob('$FMTDATA/dose_manifest_*.json') or glob.glob('/opt/tiger/vnext_data/${MTAG}_*/dose_manifest_*.json')
d=json.load(open(g[0])); rows=d if isinstance(d,list) else [d]
print(max(r['optimizer_updates_fixed'] for r in rows))")
LOCAL=/opt/tiger/vnext_ckpt/$RID
rm -rf $LOCAL
sed -e "s#^model_name_or_path: .*#model_name_or_path: $MODEL#" \
    -e "s#^template: .*#template: $TPL#" \
    -e "s#__DATASET__#lawv1_MIX-${ARM}#" \
    -e "s#__OUTPUT__#$LOCAL#" \
    -e "s#__MAXSTEPS__#$MS#" \
    -e "s#dataset_dir: ./prescription/lawv1#dataset_dir: $DATA#" \
    -e "s#gradient_accumulation_steps: 2#gradient_accumulation_steps: $GA#" \
    configs/lawv1/train_smoke_packed.yaml > $RD/train_config.yaml
export FORCE_TORCHRUN=1 NPROC_PER_NODE=$NG CUDA_VISIBLE_DEVICES=$GPUS DISABLE_VERSION_CHECK=1
ulimit -c 0
llamafactory-cli train $RD/train_config.yaml > $RD/train_log.txt 2>&1 || { echo "TRAIN_FAIL $RID"; rm -rf $LOCAL; exit 1; }
[ -f $LOCAL/config.json ] || { echo "CKPT_MISSING $RID"; rm -rf $LOCAL; exit 1; }
EV=$REPO/prescription/gate1/eval500_proto.jsonl
python3 $VX/code/gen_predict_vnext.py $EV $RD/pred.jsonl $LOCAL 8192 $NG > $RD/gen_log.txt 2>&1 || { echo "GEN_FAIL $RID"; rm -rf $LOCAL; exit 1; }
python3 prescription/lawv1_score.py --eval $EV --pred $RD/pred.jsonl --out $RD/score > $RD/score_log.txt 2>&1 || { echo "SCORE_FAIL $RID"; rm -rf $LOCAL; exit 1; }
FIRSTGPU=$(echo $GPUS | cut -d, -f1)
CUDA_VISIBLE_DEVICES=$FIRSTGPU python3 $VX/code/loss_extract.py $EV $LOCAL $RD/loss.jsonl > $RD/loss_log.txt 2>&1 || { echo "LOSS_FAIL $RID"; rm -rf $LOCAL; exit 1; }
rm -rf $LOCAL
touch $RD/DONE
echo "MIX_DONE $RID"
