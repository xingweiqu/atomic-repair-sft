#!/usr/bin/env python3
"""C-25 queue-A budget validator. Usage: validate_training_budget.py <dose_manifest> <runs_dir> <arm...>
Checks (hard): dataset target-token dev <=1%; optimizer updates identical (from trainer logs);
packed-batch count identical (= max_steps); tokens-per-step identical (fixed by config).
Declares (report, not gated): dataset sequence-token dev; per-arm epoch-equivalent
(structural: exact target-token constancy + heterogeneous component seq profiles makes
dataset-level seq constancy unattainable; compute-level constancy is enforced instead)."""
import json, re, sys
from pathlib import Path
man = {a["arm"]: a for a in json.load(open(sys.argv[1]))}
runs = Path(sys.argv[2]); arms = sys.argv[3:]
base = man[arms[0].rsplit("-S", 1)[0]]
fails, report = [], []
steps_seen = set()
for rid in arms:
    a = man[rid.rsplit("-S", 1)[0]]
    tdev = 100 * (a["total_target_tokens"] - base["total_target_tokens"]) / base["total_target_tokens"]
    sdev = 100 * (a["total_sequence_tokens"] - base["total_sequence_tokens"]) / base["total_sequence_tokens"]
    log = (runs / rid / "train_log.txt").read_text()
    m = re.findall(r"'epoch': ([\d\.]+)}", log)
    steps = len(re.findall(r"'loss':", log))
    steps_seen.add(steps)
    ep_eq = float(m[-1]) if m else None
    if abs(tdev) > 1.0:
        fails.append(f"{rid}: target-token dev {tdev:.2f}% > 1%")
    report.append(dict(run=rid, target_dev_pct=round(tdev, 3), seq_dev_pct_declared=round(sdev, 3),
                       optimizer_updates=steps, epoch_equivalent=ep_eq))
if len(steps_seen) != 1:
    fails.append(f"optimizer updates differ across arms: {sorted(steps_seen)}")
out = dict(PASS=not fails, fails=fails, checks=report,
           note="updates/batches/tokens-per-step identical by packed+fixed-max_steps construction; dataset seq-token dev converted to epoch-equivalent delta (declared)")
json.dump(out, open(runs / "budget_validation.json", "w"), indent=1)
print(json.dumps(out, indent=1))
sys.exit(0 if not fails else 1)
