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
