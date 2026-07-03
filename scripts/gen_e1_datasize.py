#!/usr/bin/env python3
"""E1 data-size sweep + E3 3-seed generator (CC_INSTRUCTION_C8, Batch-3).

E1: subsample training sets from the two existing v4 pools and emit the full config
grid. Deterministic, idempotent, additive-only (new files + dataset_info entries).

  pools    : targeted-mixed = v4_actionized_train (3000, all operators mixed)
             random         = concat of 4 controls/random_{op}_train (2640 total)
             -> N=3000 for random == the FULL pool (2640), disclosed in the card.
  grid     : cond x N{100,300,1000,3000} x seed{42; +43,44 at N=300} x epoch{2,4,8,16}
             = 48 sft runs, each with repair(384) + transfer(2048) predicts = 96 predicts.
  ridge    : per C-8/R-18, each run's REPORT point = its own ridge epoch
             (parse>=0.95 AND json_bleed<=5%, judged at harvest, not here).

E3: canonical headline cells x seeds 43/44 at their ridge points:
             scaffold_conv@e8, targeted_override_wrong_claim@e2, targeted_recompute@e3.

Run:  python3 scripts/gen_e1_datasize.py
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_HDFS = "/mnt/hdfs/xwqu/gsm-repair-v4/output"
NS = [100, 300, 1000, 3000]
EPOCHS = [2, 4, 8, 16]

SFT_TMPL = (ROOT / "configs/v4/epoch_sweep/scaffold_conv_e8_sft.yaml").read_text()
REP_TMPL = (ROOT / "configs/v4/scaffold_conv_predict.yaml").read_text()
TRA_TMPL = (ROOT / "configs/v4/transfer_base_predict.yaml").read_text()


def sub(tmpl, **kv):
    t = tmpl
    for k, v in kv.items():
        t = re.sub(rf"(?m)^{k}:.*$", f"{k}: {v}", t)
    return t


def main():
    (ROOT / "data_v4/e1").mkdir(exist_ok=True)
    (ROOT / "configs/v4/e1").mkdir(exist_ok=True)
    (ROOT / "configs/v4/e3").mkdir(exist_ok=True)

    pools = {"targeted": json.load((ROOT / "data_v4/actionized_full_train.json").open())}
    rnd = []
    for op in ["verify_step", "override_wrong_claim", "recompute", "retrieve_or_abstain"]:
        rnd += json.load((ROOT / f"data_v4/controls/random_{op}_train.json").open())
    pools["random"] = rnd

    di = json.load((ROOT / "data_v4/dataset_info.json").open())
    manifest, n_sft, n_pred = {}, 0, 0

    def seeds_for(n):
        return [42, 43, 44] if n == 300 else [42]

    for cond, pool in pools.items():
        for n in NS:
            for s in seeds_for(n):
                take = min(n, len(pool))
                rng = random.Random(s)
                idx = sorted(rng.sample(range(len(pool)), take))
                tag = f"{cond}_n{n}_s{s}"
                (ROOT / f"data_v4/e1/{tag}.json").write_text(
                    json.dumps([pool[i] for i in idx], ensure_ascii=False, indent=1))
                manifest[tag] = {"pool_size": len(pool), "taken": take, "indices": idx}
                di[f"e1_{tag}"] = {"file_name": f"e1/{tag}.json",
                                   "columns": {"prompt": "instruction", "query": "input",
                                               "response": "output"}}
                for e in EPOCHS:
                    run = f"e1_{tag}_e{e}"
                    (ROOT / f"configs/v4/e1/{run}_sft.yaml").write_text(sub(
                        SFT_TMPL, model_name_or_path="/mnt/hdfs/xwqu/Qwen3-8B",
                        dataset=f"e1_{tag}", eval_dataset=f"e1_{tag}",
                        num_train_epochs=e, seed=s,
                        output_dir=f"{OUT_HDFS}/{run}"))
                    n_sft += 1
                    (ROOT / f"configs/v4/e1/{run}_predict.yaml").write_text(sub(
                        REP_TMPL, model_name_or_path=f"{OUT_HDFS}/{run}",
                        output_dir=f"{OUT_HDFS}/predict_{run}"))
                    (ROOT / f"configs/v4/e1/transfer_{run}_predict.yaml").write_text(sub(
                        TRA_TMPL, model_name_or_path=f"{OUT_HDFS}/{run}",
                        output_dir=f"{OUT_HDFS}/predict_transfer_{run}"))
                    n_pred += 2

    (ROOT / "data_v4/e1/sampling_manifest.json").write_text(json.dumps(manifest, indent=1))
    json.dump(di, (ROOT / "data_v4/dataset_info.json").open("w"), indent=1)

    # ---------------- E3: headline 3-seed at ridge points ----------------
    e3 = [("scaffold_conv", 8, "e1_ridge_floor"),          # canonical floor
          ("targeted_override_wrong_claim", 2, None),       # its ridge (parse 1.0, bleed 1% @e2)
          ("targeted_recompute", 3, None)]                  # its ridge (parse 1.0, bleed 3% @e3)
    n3 = 0
    for branch, e, _ in e3:
        base_sft = (ROOT / f"configs/v4/epoch_sweep/{branch}_e{e}_sft.yaml").read_text()
        for s in [43, 44]:
            run = f"e3_{branch}_e{e}_s{s}"
            (ROOT / f"configs/v4/e3/{run}_sft.yaml").write_text(sub(
                base_sft, seed=s, output_dir=f"{OUT_HDFS}/{run}"))
            (ROOT / f"configs/v4/e3/{run}_predict.yaml").write_text(sub(
                REP_TMPL, model_name_or_path=f"{OUT_HDFS}/{run}",
                output_dir=f"{OUT_HDFS}/predict_{run}"))
            (ROOT / f"configs/v4/e3/transfer_{run}_predict.yaml").write_text(sub(
                TRA_TMPL, model_name_or_path=f"{OUT_HDFS}/{run}",
                output_dir=f"{OUT_HDFS}/predict_transfer_{run}"))
            n3 += 1

    print(f"E1: {len(manifest)} datasets, {n_sft} sft configs, {n_pred} predict configs")
    print(f"E3: {n3} sft configs (+{n3*2} predicts)")


if __name__ == "__main__":
    main()
