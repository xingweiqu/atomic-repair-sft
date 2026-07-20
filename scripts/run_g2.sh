#!/bin/bash
# C-16 G2: Qwen3-32B — profile (TP=2, 4 shards) + steering extract/scan2 (no training).
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github || exit 1
unset FORCE_TORCHRUN NPROC_PER_NODE
export TP=2
pairs=("0,1" "2,3" "4,5" "6,7")
for i in 0 1 2 3; do
  CUDA_VISIBLE_DEVICES=${pairs[$i]} python3 probes/run_probes_mm.py gen --model /opt/tiger/models_mm/Qwen3-32B --tag qwen32b --shard $i:4 >> /tmp/g2_prof_$i.log 2>&1 &
done
wait
unset TP
python3 probes/run_probes_mm.py score --tag qwen32b >> /tmp/g2_prof_score.log 2>&1
echo "G2_PROFILE_DONE"
export M3_MODEL=/opt/tiger/models_mm/Qwen3-32B M3_OUT=loop3/eval_g2 M3_MM=probes/out_mm/qwen32b
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 loop3/m3_steer.py extract --shard $g:8 >> /tmp/g2_ext_$g.log 2>&1 &
done
wait
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 loop3/m3_steer.py scan2 --shard $g:8 >> /tmp/g2_scan_$g.log 2>&1 &
done
wait
python3 loop3/m3_steer.py merge2 > /tmp/g2_verdict.log 2>&1
cat /tmp/g2_verdict.log
echo "G2_DONE"
