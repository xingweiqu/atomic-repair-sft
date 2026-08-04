# UTILITY_AND_BASELINES — recipe 目标与基线公式冻结文件(lawv1;2026-08-04 draft → 章程 commit 时冻结,M5 前不得再改)

> 回应 REVIEW_lawv1_v1 第八、九条:U 必须在看结果前写成确定公式,否则 recipe = 事后挑选。

## 1. 优化目标:字典序(不用加权和)

**硬约束**(不满足即不可行):
- Δs_original ≥ −ε_o,ε_o = 2.0pp(PROPOSED,章程 commit 时定稿;不得晚于 Stage A 开跑);
- Δs_retention ≥ −ε_r,ε_r = 2.0pp(retention = 三域 Original 合并套卷 + 训练域外基准);
- s_insufficient ≥ ρ,ρ = s₀,insufficient − 5.0pp(弃答边界最多让 5pp)。

**可行集内字典序**:
1. max worst-condition(适用条件集上的最小 Δplacebo-adjusted 分);
2. 次级:max 主条件 macro-average(按 APPLICABILITY_MATRIX 的适用格平均);
3. 平手:选组件总 token 份额更小(更简单)的 recipe。

预测值一律用 placebo-adjusted(F/G 分解后的 ŝ);worst/macro 的条件集在评测套件冻结时一并冻结。

## 2. 组件→endpoint 映射(fix-worst / by-frequency 用)

| 组件 | 映射 endpoint |
|---|---|
| format | structured_output |
| evidence robustness | distractor + wrong_candidate(均值) |
| selective revision | correct_candidate(preserve)+ wrong_candidate(repair)(均值) |
| answerability | insufficient |

## 3. 六个 mixture 臂(判别性选点;确定公式)

设可分配特殊 token 份额上限 Q*(= r* 的特殊份额;r* 先解出,其余臂份额与之对齐,保证同成本可比):

1. **clean replay**:全部 replay(q_d=0 ∀d);
2. **uniform**:Q* 均分给 4 组件;
3. **constrained predicted optimum r\***:§1 字典序解;
4. **unconstrained target optimum**:忽略全部硬约束,max macro-average 的解;
5. **max-negative-interaction pair**:取单组件曲线中高剂量段预测损伤最大的两个组件,各给 Q*/2(把预测最危险的 corner 显式踩上);
6. **max-disagreement**:在预算网格上取 |加性模型预测 − 最佳单组件模型预测| 最大的配方(加性 vs 单组件假设分歧最大点)。

臂 5/6 的具体配比由 Stage A 曲线代入公式机械解出,解出过程入 mixture 预测冻结 commit(节点5)。交互修正 scope = **targeted interaction correction**(只校准一个最重要组件对,最多 +6 runs,不声称完整 pairwise model)。

## 4. 新模型阶段(M6)基线与 seed 配置

- predicted recipe / uniform / clean replay:各 **3 seeds**;
- 人工比例、补最差:单 seed(标注 single preregistered arm);
- 跨模型迁移假设(预注册):G_new_{e,d}(n) = a_{e,d} · G_source_{e,d}(b_d·n)(形状迁移,幅度+横向尺度重标定);两个 pilot 点估 (a,b);
- **触发规则**:若两 pilot 点与 source 形状的拟合残差 > 该 endpoint 的 seed+模板噪声,追加第三个 calibration dose,而非强行输出 recipe。

## 5. 补最差 / 按失败频率 的确定公式

- **fix-worst**:全部 Q* 给 s₀ 最差主条件所映射的组件(§2 表);
- **by-failure-frequency**:q_d ∝ (1 − s₀,e(d)),e(d) 为 §2 映射 endpoint(多 endpoint 取均值),归一化到 Q*。
