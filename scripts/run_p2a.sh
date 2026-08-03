#!/bin/bash
# Phase-2a stage runner. Usage: run_p2a.sh <machine_idx> <n_machines> <stage:1|2>
IDX=${1:-0}; NM=${2:-1}; STAGE=${3:-1}
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github || exit 1
git fetch -q origin prescription-v1 && git checkout -q -B prescription-v1 origin/prescription-v1
python3 prescription/d_components.py > /tmp/p2a_build.log 2>&1
export FORCE_TORCHRUN=1 NPROC_PER_NODE=8
SPECS=()
for c in d0_replay d1_format d2_verify d3_revise d5_provenance d6_abstain; do
  if [ "$STAGE" = "1" ]; then doses="60"; else doses="600 2000"; fi
  for d in $doses; do for e in 2 4; do SPECS+=("${c}_${d}:e${e}"); done; done
done
i=0; nfail=0
for spec in "${SPECS[@]}"; do
  if [ $((i % NM)) -ne $IDX ]; then i=$((i+1)); continue; fi
  i=$((i+1))
  ds="${spec%%:*}"; e="${spec##*:e}"
  tag=p2a_${ds}_e${e}
  if [ -f "/mnt/hdfs/xwqu/p2a/output/$tag/config.json" ]; then echo "OK $tag (skip)"; continue; fi
  python3 - << PYEOF
import re
from pathlib import Path
tpl = Path('configs/loop3/l3_cleanreplay_s42_e4_sft.yaml').read_text()
c = re.sub(r'(?m)^dataset: .*$', 'dataset: $ds', tpl)
c = re.sub(r'(?m)^dataset_dir: .*$', 'dataset_dir: ./prescription/data/p2a', c)
c = re.sub(r'(?m)^num_train_epochs: .*$', 'num_train_epochs: $e', c)
c = re.sub(r'(?m)^output_dir: .*$', 'output_dir: /mnt/hdfs/xwqu/p2a/output/$tag', c)
Path('/tmp/p2a_$tag.yaml').write_text(c)
PYEOF
  if llamafactory-cli train /tmp/p2a_$tag.yaml > /tmp/p2a_$tag.log 2>&1; then echo "OK $tag"; else echo "FAIL $tag"; nfail=$((nfail+1)); fi
done
if [ $nfail -eq 0 ]; then
  mkdir -p /mnt/hdfs/xwqu/p2a && touch /mnt/hdfs/xwqu/p2a/done_stage${STAGE}_m${IDX}
  echo "P2A_M${IDX}_STAGE${STAGE}_DONE"
else
  echo "P2A_M${IDX}_STAGE${STAGE}_FAILED nfail=$nfail"
fi
