#!/bin/bash
# Matrix-completion batch (PREREG_matrix_completion): MC-1 lever domain transfer ->
# MC-2 Mistral steering -> MC-3 2wiki drills arm. Refreeze after harvest.
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github || exit 1
unset FORCE_TORCHRUN NPROC_PER_NODE
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 loop3/steer_domain.py gen --shard $g:8 >> /tmp/mc1_$g.log 2>&1 &
done
wait
python3 loop3/steer_domain.py score > /tmp/mc1_score.log 2>&1
echo "MC1_DONE"
export M3_MODEL=/opt/tiger/models_mm/Mistral-7B-Instruct-v0.3 M3_OUT=loop3/eval_mc_mistral M3_MM=probes/out_mm/mistral7b
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 loop3/m3_steer.py extract --shard $g:8 >> /tmp/mc2_ext_$g.log 2>&1 &
done
wait
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 loop3/m3_steer.py scan2 --shard $g:8 >> /tmp/mc2_scan_$g.log 2>&1 &
done
wait
python3 loop3/m3_steer.py merge2 > /tmp/mc2_verdict.log 2>&1
cat /tmp/mc2_verdict.log
echo "MC2_DONE"
unset M3_MODEL M3_OUT M3_MM
python3 wiki2/build_2wiki.py armx2 > /tmp/mc3_armx2.log 2>&1 || { echo "MC3_BUILD_FAIL"; exit 1; }
export FORCE_TORCHRUN=1 NPROC_PER_NODE=8
for e in 2 4; do
  tag=w2_drl25_s42_e${e}
  if [ -f "/mnt/hdfs/xwqu/wiki2/output/$tag/config.json" ]; then echo "OK $tag (skip)"; continue; fi
  python3 - << PYEOF
import re
from pathlib import Path
tpl = Path('configs/loop3/l3_cleanreplay_s42_e4_sft.yaml').read_text()
c = re.sub(r'(?m)^dataset: .*$', 'dataset: w2_drl25', tpl)
c = re.sub(r'(?m)^dataset_dir: .*$', 'dataset_dir: ./wiki2/data', c)
c = re.sub(r'(?m)^num_train_epochs: .*$', 'num_train_epochs: $e', c)
c = re.sub(r'(?m)^output_dir: .*$', 'output_dir: /mnt/hdfs/xwqu/wiki2/output/$tag', c)
Path('/tmp/mc3_$tag.yaml').write_text(c)
PYEOF
  if llamafactory-cli train /tmp/mc3_$tag.yaml > /tmp/mc3train_$tag.log 2>&1; then echo "OK $tag"; else echo "FAIL $tag"; fi
done
unset FORCE_TORCHRUN NPROC_PER_NODE
export CKPTS="/mnt/hdfs/xwqu/wiki2/output/w2_drl25_*"
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 wiki2/build_2wiki.py probes --shard $g:8 >> /tmp/mc3_probe_$g.log 2>&1 &
done
wait
python3 wiki2/build_2wiki.py score > /tmp/mc3_score.log 2>&1
echo "MC_ALL_DONE"
