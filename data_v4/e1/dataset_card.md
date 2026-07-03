# dataset_card — E1 data-size sweep 子采样集(2026-07-05)

| 字段 | 值 |
|---|---|
| **construct** | **procedure**(answer-update 行为;泄漏增益记 M,C-5.1) |
| 池来源 | targeted-mixed = `data_v4/actionized_full_train.json`(3000,全 operator 混合);random = `data_v4/controls/random_{4 op}_train.json` 拼接(2640) |
| 采样 | 无放回,seed=42(N=300 另有 43/44);逐条索引清单 `sampling_manifest.json` |
| **封顶披露** | random 池 2640 < 3000 → `random_n3000` 实为全池 2640,不补采、不放回 |
| 切分 | 训练自 GSM8K train 衍生池;eval = 既有 `repair_eval.jsonl`(480, GSM test)+ `transfer_eval.json`(300, 素题)——train/test 隔离沿 v4(source_id 重叠 0) |
| 闸门 | 引擎/judge 沿账本冻结口径;每 run 报告点 = 脊点(parse≥0.95 ∧ json_bleed≤5%) |
| regime | 评测 greedy 单次;pass@8 只作分桶变量(D-7(iii)) |
| 预注册 | `prereg/PREREG_datasize.md`(与本 card 同 commit,先于一切训练) |
