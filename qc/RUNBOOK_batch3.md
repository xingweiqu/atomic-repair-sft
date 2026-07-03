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
