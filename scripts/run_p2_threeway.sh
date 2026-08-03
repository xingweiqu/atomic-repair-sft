#!/bin/bash
# P2-1 three-way conditional: 12 trains -> p1_eval score + v2.
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github || exit 1
git fetch -q origin prescription-v1 && git checkout -q -B prescription-v1 origin/prescription-v1
export FORCE_TORCHRUN=1 NPROC_PER_NODE=8
for spec in "d4_3way_600:42" "d4_3way_600:43" "d4_3way_600:44" "d4_3way_1998:42"; do
  ds="${spec%%:*}"; s="${spec#*:}"
  for e in 2 4 8; do
    tag=${ds}_s${s}_e${e}
    if [ -f "/mnt/hdfs/xwqu/p2/output/$tag/config.json" ]; then echo "OK $tag (skip)"; continue; fi
    python3 - << PYEOF
import re
from pathlib import Path
tpl = Path('configs/loop3/l3_cleanreplay_s42_e4_sft.yaml').read_text()
c = re.sub(r'(?m)^dataset: .*$', 'dataset: $ds', tpl)
c = re.sub(r'(?m)^dataset_dir: .*$', 'dataset_dir: ./prescription/data/d4', c)
c = re.sub(r'(?m)^seed: .*$', 'seed: $s', c)
c = re.sub(r'(?m)^num_train_epochs: .*$', 'num_train_epochs: $e', c)
c = re.sub(r'(?m)^output_dir: .*$', 'output_dir: /mnt/hdfs/xwqu/p2/output/$tag', c)
Path('/tmp/p2_$tag.yaml').write_text(c)
PYEOF
    if llamafactory-cli train /tmp/p2_$tag.yaml > /tmp/p2train_$tag.log 2>&1; then echo "OK $tag"; else echo "FAIL $tag"; fi
  done
done
echo "P2_TRAIN_DONE"
unset FORCE_TORCHRUN NPROC_PER_NODE
export P0C_EXTRA="/mnt/hdfs/xwqu/p2/output/*"
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 prescription/p1_eval.py gen --shard $g:8 >> /tmp/p2e_$g.log 2>&1 &
done
wait
python3 prescription/p1_eval.py score > /tmp/p2_score.log 2>&1
python3 prescription/p1_eval.py v2 > /tmp/p2_v2.log 2>&1
grep -E "3way" /tmp/p2_score.log /tmp/p2_v2.log | tail -8
echo "P2_ALL_DONE"
