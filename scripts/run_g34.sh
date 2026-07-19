#!/bin/bash
# C-16 G3 (SVAMP) + G4 (StrategyQA): genp -> 8 trains -> probes -> score, per cell.
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github || exit 1
unset FORCE_TORCHRUN NPROC_PER_NODE
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 svamp/build_svamp.py genp --shard $g:8 >> /tmp/g3_genp_$g.log 2>&1 &
done
wait
echo "G3_GENP_DONE"
export FORCE_TORCHRUN=1 NPROC_PER_NODE=8
for cell in g3 g4; do
  dir=$( [ $cell = g3 ] && echo svamp/data || echo stratqa/data )
  for arm in cleanreplay U fmt10 drl25; do
    for e in 2 4; do
      tag=${cell}_${arm}_s42_e${e}
      if [ -f "/mnt/hdfs/xwqu/$cell/output/$tag/config.json" ]; then echo "OK $tag (skip)"; continue; fi
      python3 - << PYEOF
import re
from pathlib import Path
tpl = Path('configs/loop3/l3_cleanreplay_s42_e4_sft.yaml').read_text()
c = re.sub(r'(?m)^dataset: .*$', 'dataset: ${cell}_${arm}', tpl)
c = re.sub(r'(?m)^dataset_dir: .*$', 'dataset_dir: ./$dir', c)
c = re.sub(r'(?m)^num_train_epochs: .*$', 'num_train_epochs: $e', c)
c = re.sub(r'(?m)^output_dir: .*$', 'output_dir: /mnt/hdfs/xwqu/$cell/output/$tag', c)
Path('/tmp/${tag}.yaml').write_text(c)
PYEOF
      if llamafactory-cli train /tmp/${tag}.yaml > /tmp/train_${tag}.log 2>&1; then echo "OK $tag"; else echo "FAIL $tag"; fi
    done
  done
done
echo "G34_TRAIN_DONE"
unset FORCE_TORCHRUN NPROC_PER_NODE
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 svamp/build_svamp.py probes --shard $g:8 >> /tmp/g3_probe_$g.log 2>&1 &
done
wait
python3 svamp/build_svamp.py score > /tmp/g3_score.log 2>&1
echo "G3_DONE"
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 stratqa/build_stratqa.py probes --shard $g:8 >> /tmp/g4_probe_$g.log 2>&1 &
done
wait
python3 stratqa/build_stratqa.py score > /tmp/g4_score.log 2>&1
echo "G34_ALL_DONE"
