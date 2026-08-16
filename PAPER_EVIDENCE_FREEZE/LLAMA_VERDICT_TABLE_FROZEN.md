# LLAMA 终局判决表(2026-08-16 冻结;先于任何 Llama 结果)

## Primary
U_predicted − U_uniform;要求 predicted ≥ uniform 且全部 hard constraints 通过(false-abstain ≤.10 R/K 两域)。

## Secondary
U_predicted − U_replay;worst branch;original retention;false-abstain;candidate joint;endpoint-vector 预测误差(MAE 与方向命中率)。

## Outcomes(预注册)
- **A Strong transfer**:predicted > uniform ∧ constraints 全过 ∧ 预测误差可接受 → recipe prediction transfer 成立;
- **B Competitive transfer**:predicted ≈ uniform(差距 ≤ 3-seed 噪声带)∧ > replay ∧ constraints/worst-endpoint 更优 → 修正模型产生 competitive constrained recipe;
- **C No transfer**:predicted < uniform ∧ 结构预测也不准 → correction 不跨模型;论文转实证版定位。

## base profile 输入白名单(防第三校准通道)
机械公式允许读取:baseline endpoint vector(算 U_base 与预测向量的加法底)/当前违反的 constraints 清单/归一化常数。
禁止:任何人工阅读后的配方调整;recipe search 代码的输入字段在 profile 生成前已固定(本文件+CALIBRATION_RULE 即为字段清单)。

## 执行纪律
前 3 run 无论好坏,10 对照跑满;Qwen 不再动;开牌只看预注册三数字。
