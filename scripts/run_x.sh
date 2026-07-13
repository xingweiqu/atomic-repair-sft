#!/bin/bash
# X: 2wiki reinforcement — U/cleanreplay seeds 43,44 (16 trains) + conduct-only (4) + eval.
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github || exit 1
python3 wiki2/build_2wiki.py armx > /tmp/x_armx.log 2>&1 || { echo "X_ARMX_FAIL"; exit 1; }
export FORCE_TORCHRUN=1 NPROC_PER_NODE=8
for spec in "w2_U:43" "w2_U:44" "w2_cleanreplay:43" "w2_cleanreplay:44" "w2_conduct:42"; do
  arm="${spec%%:*}"; s="${spec#*:}"
  for e in 2 4 8 16; do
    tag=${arm}_s${s}_e${e}
    if [ -f "/mnt/hdfs/xwqu/wiki2/output/$tag/config.json" ]; then echo "OK $tag (skip)"; continue; fi
    python3 - << PYEOF
import re
from pathlib import Path
tpl = Path('configs/loop3/l3_cleanreplay_s42_e4_sft.yaml').read_text()
c = re.sub(r'(?m)^dataset: .*$', 'dataset: $arm', tpl)
c = re.sub(r'(?m)^dataset_dir: .*$', 'dataset_dir: ./wiki2/data', c)
c = re.sub(r'(?m)^seed: .*$', 'seed: $s', c)
c = re.sub(r'(?m)^num_train_epochs: .*$', 'num_train_epochs: $e', c)
c = re.sub(r'(?m)^output_dir: .*$', 'output_dir: /mnt/hdfs/xwqu/wiki2/output/$tag', c)
Path('/tmp/x_$tag.yaml').write_text(c)
PYEOF
    if llamafactory-cli train /tmp/x_$tag.yaml > /tmp/xtrain_$tag.log 2>&1; then echo "OK $tag"; else echo "FAIL $tag"; fi
  done
done
echo "X_TRAIN_DONE"
unset FORCE_TORCHRUN NPROC_PER_NODE
export CKPTS="/mnt/hdfs/xwqu/wiki2/output/w2_*_s4[234]_*"
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 wiki2/build_2wiki.py probes --shard $g:8 >> /tmp/xprobe_$g.log 2>&1 &
done
wait
python3 wiki2/build_2wiki.py score > /tmp/x_score.log 2>&1
echo "X_EVAL_DONE"
