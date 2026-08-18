#!/bin/bash
# Generic queue worker: claims lines from a shared queue file via HDFS mkdir locks.
# Usage: machine_worker.sh <queue_name>
# Queue file: /mnt/hdfs/xwqu/vnext0818/queues/<queue_name>.txt (one shell command per line; '#' = comment)
set -u
QN=$1
source ~/atomic_env.sh
QF=/mnt/hdfs/xwqu/vnext0818/queues/$QN.txt
LK=/mnt/hdfs/xwqu/vnext0818/locks
LOGD=/mnt/hdfs/xwqu/vnext0818/logs; mkdir -p $LK $LOGD
cd /opt/tiger/atomic-repair-sft-github
git fetch -q origin vnext-atomic-scaling && git checkout -f -q -B vnext-atomic-scaling origin/vnext-atomic-scaling
while true; do
  GOT=0
  N=$(wc -l < $QF)
  for i in $(seq 1 $N); do
    LINE=$(sed -n "${i}p" $QF)
    [ -z "$LINE" ] && continue
    case "$LINE" in \#*) continue;; esac
    ID=$(echo "$QN-$i" )
    if mkdir $LK/$ID 2>/dev/null; then
      GOT=1
      echo "$(date +%H:%M:%S) CLAIM $ID: $LINE" | tee -a $LOGD/$(hostname).log
      if bash -c "$LINE" >> $LOGD/$ID.log 2>&1; then
        touch $LK/$ID/OK
      else
        if [ ! -f $LK/$ID/RETRIED ]; then
          touch $LK/$ID/RETRIED
          echo "RETRY $ID" >> $LOGD/$(hostname).log
          bash -c "$LINE" >> $LOGD/$ID.log 2>&1 && touch $LK/$ID/OK || touch $LK/$ID/FAIL
        else
          touch $LK/$ID/FAIL
        fi
      fi
    fi
  done
  [ $GOT -eq 0 ] && { sleep 60; NEW=$(wc -l < $QF); [ "$NEW" == "$N" ] && [ -f /mnt/hdfs/xwqu/vnext0818/queues/$QN.CLOSED ] && break; }
done
echo "WORKER_EXIT $(hostname)"
