# PREREG_transfer_matrix — 三世界双向预注册(2026-07-10,本 commit 即时间戳,C-10 §1 逐字冻结)

## 度量(R-23 一并冻结)
- **Gain(train=i, eval=j)** = 臂 i 的**脊点 ckpt**(per-branch 三闸门:parse≥0.95 ∧
  json_bleed≤5% ∧ mute≤12%)在域 j 的 corrupt repair score,相对**该域 floor**(同脊点规则选点)。
- **TransferRatio(i→j) = Gain(i,j) / Gain(i,i)**;当 **Gain(i,i) < 5pp** 时该行
  TransferRatio 无定义(整行标灰,不参与世界判定)。
- **RepairUtility = TargetGain − λ·(素题损伤 + 出血 + 无效)**,λ 敏感性扫 {0.5, 1, 2} 全报告。
- repair score 判分沿账本冻结口径(strict judge);decision margin 并报。

## 三世界判读规则(冻结;结论由 Xingwei/顾问按此裁决,CC 不宣布)
- **World A**:非对角 TransferRatio **普遍 < 0.35** → 修复是格特异的(诊断必要)。
- **World B**:非对角 **普遍 > 0.7** → 修复是通用决策(诊断的价值在别处)。
- **World C**:K↔R 互迁高,而 **H 行/列不对称** → 组合格特殊(层级结构)。
- **灰区**(0.35–0.7 且无形态)→ **如实报告为未决**,不硬塞任何世界。

## 硬停
- 出现**负迁移 < −10pp** 的格 → 停 + 验尸(与判读规则矛盾类)。
- 其余沿既有:与本预注册矛盾、residual>3pp、闸门不过隔离。

## 措辞
一律 **Repair Transfer Matrix**;禁称 capacity-specific matrix;C-7 禁令沿用。
