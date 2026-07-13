#!/bin/bash
# M2: Llama miniature repair — 5 arms x epochs {2,4} = 10 trains, then dual-genre eval.
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github || exit 1
export FORCE_TORCHRUN=1 NPROC_PER_NODE=8
for spec in "l3_cleanreplay:42" "l3_B:42" "l3_B:43" "l3_fmt10:42" "l3_drl25:42"; do
  ds="${spec%%:*}"; s="${spec#*:}"
  for e in 2 4; do
    tag=m2_${ds#l3_}_s${s}_e${e}
    if [ -f "/mnt/hdfs/xwqu/m2/output/$tag/config.json" ]; then echo "OK $tag (skip)"; continue; fi
    python3 - << PYEOF
import re
from pathlib import Path
tpl = Path('configs/loop3/l3_cleanreplay_s42_e4_sft.yaml').read_text()
c = re.sub(r'(?m)^model_name_or_path: .*$', 'model_name_or_path: /opt/tiger/models_mm/Llama-3.1-8B-Instruct', tpl)
c = re.sub(r'(?m)^template: .*$', 'template: llama3', c)
c = re.sub(r'(?m)^dataset: .*$', 'dataset: $ds', c)
c = re.sub(r'(?m)^seed: .*$', 'seed: $s', c)
c = re.sub(r'(?m)^num_train_epochs: .*$', 'num_train_epochs: $e', c)
c = re.sub(r'(?m)^output_dir: .*$', 'output_dir: /mnt/hdfs/xwqu/m2/output/$tag', c)
Path('/tmp/m2_$tag.yaml').write_text(c)
PYEOF
    if llamafactory-cli train /tmp/m2_$tag.yaml > /tmp/m2train_$tag.log 2>&1; then echo "OK $tag"; else echo "FAIL $tag"; fi
  done
done
echo "M2_TRAIN_DONE"
unset FORCE_TORCHRUN NPROC_PER_NODE
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 loop3/m2_eval.py gen --shard $g:8 >> /tmp/m2eval_$g.log 2>&1 &
done
wait
python3 loop3/m2_eval.py score > /tmp/m2_score.log 2>&1
echo "M2_EVAL_DONE"
