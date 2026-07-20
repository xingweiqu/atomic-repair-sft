#!/bin/bash
# C-16 G1: Mistral-7B-v0.3 — profile + 8 trains + dual-genre eval.
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github || exit 1
export HF_HUB_DISABLE_XET=1
if [ ! -f /opt/tiger/models_mm/Mistral-7B-Instruct-v0.3/config.json ]; then
  huggingface-cli download mistralai/Mistral-7B-Instruct-v0.3 --local-dir /opt/tiger/models_mm/Mistral-7B-Instruct-v0.3 --exclude "consolidated.safetensors" "original/*" > /tmp/dl_mistral.log 2>&1 || { echo "G1_DL_FAIL"; exit 1; }
fi
echo "G1_DL_OK"
unset FORCE_TORCHRUN NPROC_PER_NODE
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 probes/run_probes_mm.py gen --model /opt/tiger/models_mm/Mistral-7B-Instruct-v0.3 --tag mistral7b --shard $g:8 >> /tmp/g1_prof_$g.log 2>&1 &
done
wait
python3 probes/run_probes_mm.py score --tag mistral7b >> /tmp/g1_prof_score.log 2>&1
echo "G1_PROFILE_DONE"
export FORCE_TORCHRUN=1 NPROC_PER_NODE=8
for spec in "l3_cleanreplay" "l3_B" "l3_fmt10" "l3_drl25"; do
  for e in 2 4; do
    tag=g1_${spec#l3_}_s42_e${e}
    if [ -f "/mnt/hdfs/xwqu/g1/output/$tag/config.json" ]; then echo "OK $tag (skip)"; continue; fi
    python3 - << PYEOF
import re
from pathlib import Path
tpl = Path('configs/loop3/l3_cleanreplay_s42_e4_sft.yaml').read_text()
c = re.sub(r'(?m)^model_name_or_path: .*$', 'model_name_or_path: /opt/tiger/models_mm/Mistral-7B-Instruct-v0.3', tpl)
c = re.sub(r'(?m)^template: .*$', 'template: mistral', c)
c = re.sub(r'(?m)^dataset: .*$', 'dataset: $spec', c)
c = re.sub(r'(?m)^num_train_epochs: .*$', 'num_train_epochs: $e', c)
c = re.sub(r'(?m)^output_dir: .*$', 'output_dir: /mnt/hdfs/xwqu/g1/output/$tag', c)
Path('/tmp/g1_$tag.yaml').write_text(c)
PYEOF
    if llamafactory-cli train /tmp/g1_$tag.yaml > /tmp/g1train_$tag.log 2>&1; then echo "OK $tag"; else echo "FAIL $tag"; fi
  done
done
echo "G1_TRAIN_DONE"
unset FORCE_TORCHRUN NPROC_PER_NODE
export M2_HDFS=/mnt/hdfs/xwqu/g1/output M2_BASE=/opt/tiger/models_mm/Mistral-7B-Instruct-v0.3 M2_OUT=loop3/eval_g1 M2_PREFIX=g1
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 loop3/m2_eval.py gen --shard $g:8 >> /tmp/g1eval_$g.log 2>&1 &
done
wait
python3 loop3/m2_eval.py score > /tmp/g1_score.log 2>&1
echo "G1_DONE"
