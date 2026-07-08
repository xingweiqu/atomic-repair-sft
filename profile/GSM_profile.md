# GSM Diagnostic Profile — admitted=['C', 'F', 'O', 'P', 'R', 'S', 'W1', 'W2']

**Headline:benchmark 说 93.5 分,其中只有 60.6 分经得起真实使用的扰动**(O 准确率 vs 全探针稳健率,同池同分母见注 1)。

注 1(分母与判定优先序):每桶分母 = 该池全部题(multi-label,桶间可共现,行和>100% 属预期);ok = O 对且未落任何失败桶——它与 O 准确率(93.5%)分母相同、判据更严(全探针)。判定顺序 = scaffold/rule/phrasing/conduct/local_exec 平行判,format 仅在无其他标签时判,unresolved = 全探针皆错,mixed = 不匹配任何规则。
注 2(池过滤):连贯性过滤剔除 330 题({'neg_gold': 115, 'nonint_gold': 215});自相矛盾约束不可程序化,仅人工审计层覆盖(披露)。
注 3:overlap 矩阵挂附录(本文末节);steering 分诊列见 triage 报告。

| pool | n | conduct | format | local_exec | mixed | ok | phrasing | rule | scaffold | unresolved |
|---|---|---|---|---|---|---|---|---|---|---|
| gsm | 1298 | 16.4% [14%,19%] | 14.7% [13%,17%] | 0.1% [0%,0%] | 0.3% [0%,1%] | 60.6% [58%,63%] | 6.4% [5%,8%] | 0.9% [1%,2%] | 2.0% [1%,3%] | 1.9% [1%,3%] |
| hard | 183 | 2.7% [1%,6%] | 3.3% [2%,7%] | 0.0% [0%,2%] | 1.1% [0%,4%] | 0.0% [0%,2%] | 7.1% [4%,12%] | 0.0% [0%,2%] | 0.0% [0%,2%] | 86.3% [81%,91%] |

## overlap(共现计数 top)

- conduct ∧ phrasing: 27
- phrasing ∧ scaffold: 12
- phrasing ∧ rule: 5
- local_exec ∧ phrasing: 1

## steering 分诊列(L8, α8;d 提自 pre-repair 素题 W 行为,LOWPOWER:负类 n=48 已披露)

| conduct 细分 | n | 占比 | d 方向救活 | **placebo(随机方向)** | d 特异增益 |
|---|---|---|---|---|---|
| derail(被带偏跑飞) | 227 | 96% | 85% | **75%** | **+10pp** |
| adopt(照抄植入值) | 9 | 4% | 4/9 | 4/9 | 0 |
| 合计 | 236 | — | 83% | 74% | +9pp |

**判定(placebo 对照后,措辞按此收窄)**:"d = 计算稳定器"不成立——救活大头是**非特异扰动效应**。
幸存的发现:**derail 是浅层不稳定失败**——任意单位向量 @α8 即可救活 75%(这些题 O 本来就对,
腐蚀只造成边缘干扰而非稳定错误信念);d 在其上仅 +10pp 特异。
含义:①Loop 3 的 E 臂(steering-only)需加随机方向基线列;②"扰动可恢复性"可作 conduct
桶的附加诊断维度(描述性命名,不另造词)。

## conduct 机制注记(2a 对账 + 拆分)
素题失败 98% 是 derail 非 adopt;同题 2×2:pre-repair 修复腔/素题 adopt = 6.7%/2.5%,
floor e8 = 15.6%/14.1% —— 体裁内差异小、**训练效应大**(格式训练令素题 adopt ×5.6)。
Loop 3 纠错臂监督动作据此改为 verify-then-recompute(裁决 2c)。
