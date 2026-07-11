#!/bin/bash
# B1 2Wiki validation chapter: screen -> genp -> build -> 12 trains -> probes -> score.
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github || exit 1
unset FORCE_TORCHRUN NPROC_PER_NODE
if [ ! -f wiki2/data/screen_shard7.jsonl ]; then
  for g in 0 1 2 3 4 5 6 7; do
    CUDA_VISIBLE_DEVICES=$g python3 wiki2/build_2wiki.py screen --shard $g:8 >> /tmp/w2_screen_$g.log 2>&1 &
  done
  wait
fi
if [ ! -f wiki2/data/para_shard7.jsonl ]; then
  for g in 0 1 2 3 4 5 6 7; do
    CUDA_VISIBLE_DEVICES=$g python3 wiki2/build_2wiki.py genp --shard $g:8 >> /tmp/w2_genp_$g.log 2>&1 &
  done
  wait
fi
python3 wiki2/build_2wiki.py build > /tmp/w2_build.log 2>&1 || { echo "W2_BUILD_FAIL"; exit 1; }
cat /tmp/w2_build.log
export FORCE_TORCHRUN=1 NPROC_PER_NODE=8
for arm in w2_U w2_FMT w2_cleanreplay; do
  for e in 2 4 8 16; do
    tag=${arm}_e${e}
    if [ -f "/mnt/hdfs/xwqu/wiki2/output/$tag/config.json" ]; then echo "OK $tag (skip)"; continue; fi
    python3 - << PYEOF
import re
from pathlib import Path
tpl = Path('configs/loop3/l3_cleanreplay_s42_e4_sft.yaml').read_text()
c = re.sub(r'(?m)^dataset: .*$', 'dataset: $arm', tpl)
c = re.sub(r'(?m)^dataset_dir: .*$', 'dataset_dir: ./wiki2/data', c)
c = re.sub(r'(?m)^num_train_epochs: .*$', 'num_train_epochs: $e', c)
c = re.sub(r'(?m)^output_dir: .*$', 'output_dir: /mnt/hdfs/xwqu/wiki2/output/$tag', c)
Path('/tmp/w2_$tag.yaml').write_text(c)
PYEOF
    if llamafactory-cli train /tmp/w2_$tag.yaml > /tmp/w2train_$tag.log 2>&1; then echo "OK $tag"; else echo "FAIL $tag"; fi
  done
done
echo "W2_TRAIN_DONE"
unset FORCE_TORCHRUN NPROC_PER_NODE
export CKPTS="/mnt/hdfs/xwqu/wiki2/output/w2_*"
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 wiki2/build_2wiki.py probes --shard $g:8 >> /tmp/w2probe_$g.log 2>&1 &
done
wait
python3 wiki2/build_2wiki.py score > /tmp/w2_score.log 2>&1
echo "W2_EVAL_DONE"
