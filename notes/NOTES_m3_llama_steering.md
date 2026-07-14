# M3 收割:Llama steering(PREREG_m3;封数据前最后一项;2026-07-14)

> 自提方向(M1 W 行为标签,mean-diff,last-token);扫描 BEST=L12 α4;
> 全评 W400+O300+修复腔480。数据:loop3/eval_m3/{scan.json,m3_result.json}。

## 预测判分

| 预测 | 实测 | 判 |
|---|---|---|
| P-M3-1 resist +10pp | .545→.790(+24.5) | 字面 HIT,但**不可解释**(见下) |
| P-M3-2 能力平线 ±5pp | ability\|resist .88→.17 | **MISS(灾难级)** |
| P-M3-3 素题损失 ≤3pp | O_acc .587→.220(−37) | **MISS(灾难级)** |

**E 臂验尸单 (d) 项(全局退化排除)在 Llama 上不通过**:resist 的 +24.5pp
伴随全面崩坏(修复腔 .100→.010),是"多答且乱答"的副产物,不是决策杠杆——
资格前提失败,P-M3-1 的字面 HIT 不具备解释力。

## 结局(按预注册诚实结局条款)

**CL-3 范围收窄为 Qwen 家族**:"决策与体裁在激活层可分离、决策可单卖"
在本配方(W 行为 mean-diff、last-token、L∈{8,12,16}×α∈{4,8,16})与本预算下
未能迁移到 Llama-3.1-8B;处方第 5 条的 steering 一线地位同步限定范围。
不主张不可能——只主张"本配方未复现",如实。两个结局都能进稿,进的是这个。

## 仪器登记

score_repair 对非 dict parse(裸 JSON 列表)补守卫(与 is_abstain_strict
同族第二例);steered Llama 输出形态本身即失稳证据之一。
