# RUNBOOK batch-3(C-8:E2 + E1 + E3;E4/E5 另发)

> 前置:`cd <repo> && git checkout gain-accounting-v1 && git pull`(需含本文件所在 commit)。
> 预注册 `prereg/PREREG_datasize.md` 已先于训练 commit ✓。红线与回传纪律沿 batch-1/2。

## Job A — E2 pass@8 合并池全量(纯推理,先占一路;可与 Job B 并行)

    cd <repo>
    python3 scripts/pass8_gsm.py --model /mnt/hdfs/xwqu/Qwen3-8B --pool merged --out data_v4/pass8_merged.jsonl

预期:`data_v4/pass8_merged.jsonl`(1 header + 1319 gsm + 1319 gsmhard = 2639 行,
每行带 source 字段)+ `pass8_merged.samples20.json`。
需 datasets 库联网拉 `reasoning-machines/gsm-hard`;拉不动贴报错停。

## Job B — E1+E3 训练(54 个 sft:48 E1 + 6 E3;8 卡逐个,断点续跑)

    cd <repo>
    bash scripts/run_e1_train.sh

多为小 N 小 epoch,单个几分钟;结束贴 FAILED 名单(应为空)。

## Job C — E1+E3 predicts(108 条,8 卡并行,断点续跑;Job B 完成后)

    cd <repo>
    bash scripts/run_e1_predict.sh

结束贴 missing 名单(应为空)。

## Job D — 收集回传

    bash scripts/run_v4_42_epoch_sweep_collect.sh   # 会一并收 predict_e1_* / predict_e3_*? 见下

注意:run_v4_42 的 glob 是 `predict_*_e*`——e1/e3 的目录名(predict_e1_..._e8 等)匹配 ✓。
回传:收集到的全部新 predict 目录 + Job A 两个文件,一个 commit:
    server: batch-3 results (pass@8 merged, E1 datasize 96 predicts, E3 seeds 12 predicts)
只含新增文件。每 Job 报:退出码 + 产物计数。

---

## batch-4a(2026-07-06,E1 裁决后复工)— E1b/E1c/E3 追溯

前置:git pull(需含 PREREG_e1b commit)。优先序:E1b 主臂 > E1c > 剂量臂(脚本按字母序自然覆盖)。

    ONLY='^(e1b_|e1c_|e3_targeted_override_wrong_claim_e3)' bash scripts/run_e1_train.sh    # 19 sft
    ONLY='e1b_|e1c_|e3_targeted_override_wrong_claim_e3' bash scripts/run_e1_predict.sh     # 38 predicts
    bash scripts/run_v4_42_epoch_sweep_collect.sh

注:run_e1_*.sh 的 glob 已扩到 configs/v4/{e1,e1b,e3},ONLY 过滤照常。

---

## batch-4b(E5 steering,单卡,可与 4a 并行;PREREG_steering 已先行 commit)

```bash
cd <repo> && git pull
CUDA_VISIBLE_DEVICES=0 python3 steering/e5_steering.py extract --model /mnt/hdfs/xwqu/Qwen3-8B
CUDA_VISIBLE_DEVICES=0 python3 steering/e5_steering.py sweep   --model /mnt/hdfs/xwqu/Qwen3-8B
# align 需 batch-4a 的 e1b/e1c ckpt 就位后再跑:
CUDA_VISIBLE_DEVICES=0 python3 steering/e5_steering.py align   --model /mnt/hdfs/xwqu/Qwen3-8B
```
- 产物全在 steering/out/(directions.pt / sweep_meta.json / gen_*_L*_a*.jsonl / alignment.json);
  gen 文件回传(评分本地做),commit message:server: batch-4b (E5 steering extract+sweep[+align])。
- extract 报两类样本数(resist=1/0;R-14 期望≥200/类,不够如实报)。
