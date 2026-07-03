# V-1 截断排查(2026-07-04)— **PASS,机制语句放行**

> 依据:qc/LOOP1_5_RULINGS.md V-1(本裁决全部生效的开关)。零算力,只重读既有输出。
> 待排除的平庸解释:体裁内算错 = trace 撞 cutoff/max_tokens 被切 → 中间步错。

## 证据源 1 — repair-mode(v4 predict,max_new_tokens=384)

matched 子集(n=50)内,scaffold_conv 算错 vs 算对两组的输出长度(字符):

| 组 | n | mean | p50 | p95 | max | ≥90% 观测上限 | JSON 不闭合 |
|---|---|---|---|---|---|---|---|
| **算错(真算术错)** | 28 | 202 | 202 | 207 | 216 | **0/28** | **0/28** |
| 算对 | 22 | 203 | 201 | 210 | 238 | 0/22 | 0/22 |

全部输出的观测上限 267 字符,离 384 token(≈1300+ 字符)预算**远未触顶**;
两组长度分布几乎重合(mean 202 vs 203)。

## 证据源 2 — T4 素题出血 JSON(max_new_tokens=2048)

| 组 | n | 长度 | ≥90% 上限 | JSON 不闭合 |
|---|---|---|---|---|
| 出血且算错 | 8 | 138–248 | 0/8 | 0/8 |
| 出血但算对 | 3 | 144–211 | 0/3 | 0/3 |

## 判定

**截断率:错误组 = 正确组 = 0。** 算错的 trace 是**完整写完的短 JSON**——自信地算错,
不是被切断。"体裁内计算本身劣化(genre-coupled computation)"机制语句**放行**,
LOOP1_5_RULINGS 全部裁决自本文件 commit 起生效。

附注:输出普遍只有 ~200 字符,与"预算不足"方向相反——体裁劣化表现为**简短而错**,
不是"想写长被掐"。此观察并入论文 §5 机制节。

## 生效裁决的落地状态(同一 commit)

| 裁决 | 落地 |
|---|---|
| R-10 双面记账 | `master_ledger.csv`:`A` → **`A_delivered`**(repair 体裁 vs 收敛 floor,部署读数);新增 **`A_latent`** 列(素题体裁 vs pre-repair,能力主张判据;由 R-7 双体裁 eval 填充,当前留位);`d_a_prerepair`(repair 体裁 vs pre-repair)保留为辅助诊断列。fig 图例同步 |
| R-11 出血曲线仪器 | `ledger/genre.py`(plain / json_bleed / mute 三分,口径冻结自 T4 判决书;自检=复现 T4 的 13/11/4 **PASS**);23 个 epoch-sweep 素题 transfer predict configs(`configs/v4/epoch_sweep/transfer_*_predict.yaml`)+ `scripts/run_v4_43_transfer_sweep.sh`,与 sweep 训练同批执行 |
| R-12 | schema-tolerant 不进主口径——账本重建确认 F 列口径未动(residual 仍全 0) |
| R-13 | pass@8 v2 + batch-1b 已在 RUNBOOK(待服务器) |
| R-14 | Loop 5 四条读出曲线规格记录在案,入口条件(A7)已满足,排期待 Loop 2 之后或并行(用户定) |
