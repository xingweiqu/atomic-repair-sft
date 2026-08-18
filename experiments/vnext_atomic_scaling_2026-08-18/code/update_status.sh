#!/bin/bash
# RUN_STATUS.md generator (run on any server machine; C-48 J: every 30 min)
B=/mnt/hdfs/xwqu/vnext0818
Q=$B/queues/main.txt
S=$B/RUN_STATUS.md
{
echo "# RUN_STATUS $(date '+%F %T')"
TOT=$(grep -cv '^#' $Q 2>/dev/null || echo 0)
OK=$(ls -d $B/locks/*/OK 2>/dev/null | wc -l)
FAIL=$(ls -d $B/locks/*/FAIL 2>/dev/null | wc -l)
CLAIMED=$(ls -d $B/locks/main-* 2>/dev/null | wc -l)
echo "- queue: $TOT jobs | claimed $CLAIMED | OK $OK | FAIL $FAIL | running $((CLAIMED-OK-FAIL))"
echo "- profiles done: $(ls $B/profiles/*/DONE 2>/dev/null | wc -l) / $(ls -d $B/profiles/*/ 2>/dev/null | wc -l) started"
echo "- arms done: $(ls $B/runs/*/DONE 2>/dev/null | wc -l)"
echo "## failures"
for d in $(ls -d $B/locks/*/FAIL 2>/dev/null | xargs -n1 dirname 2>/dev/null); do
  ID=$(basename $d); LN=$(echo $ID | sed 's/main-//')
  echo "- $ID: $(sed -n ${LN}p $Q | cut -c1-120)"
  tail -3 $B/logs/$ID.log 2>/dev/null | sed 's/^/    /'
done
echo "## recent machine log tails"
for f in $B/logs/n*.log; do [ -f $f ] && { echo "### $(basename $f)"; tail -4 $f | sed 's/^/    /'; }; done
} > $S
cat $S
