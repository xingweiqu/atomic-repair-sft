# dataset_card — E1b/E1c(2026-07-06)
| 字段 | 值 |
|---|---|
| **construct** | procedure |
| 池 | per_policy/{4 op}_train.json 各 660;keep 池 = actionized_full_train 内 Action="keep answer"(1000) |
| 采样 | 无放回 seed 42;逐条索引 `sampling_manifest.json`;opsonly=各 op N/4 均匀;keep15=45 keep+64/64/64/63 ops;keeponly=660 |
| 闸门 | C-9 三闸(parse≥0.95∧json_bleed≤5%∧mute≤12%);judge/引擎沿账本冻结口径 |
| 预注册 | prereg/PREREG_e1b.md(同 commit,先于训练) |
