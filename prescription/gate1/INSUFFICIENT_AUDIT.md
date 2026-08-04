# INSUFFICIENT_AUDIT — v1.2 insufficient 全量人工审核(C-23 #1;2026-08-05)

> 审核人:CC(逐题通读;每题判三项:语法自然性 / 真不可解性(含心算反推)/ 泄漏)。
> 机械闸门(先行):值匹配全 token、数词泄漏扫描、≤2 步代数可恢复检查、冠词/连字符/
> 比号/定语价格/单位词跳过、语法残渣扫描、val==1 弃用。50 主池 → 机械闸门余 27 →
> 人工全审 → 2 项修复 + 1 项黑名单 → **终版 26 条,全部 PASS**。

## 逐题裁决(27 条初审)

| # | family | 删除 | 类型 | 语法 | 不可解 | 裁决 |
|---|---|---|---|---|---|---|
| 1 | 00119 | 40% | percentage | ✓ | ✓(增幅未知→四年后总额不可得) | PASS |
| 2 | 00150 | 3 (miles) | count | ✓ | ✓(Steve 距离未知→胜负与等待时间不可得) | PASS |
| 3 | 01315 | 3 (min) | count | ✓ | ✓(Ana 速率未知) | PASS |
| 4 | 00544 | 100 (dollars) | price | ✗ "amount dollars" | ✓ | **FIX**→替换词补 "of",复审 PASS |
| 5 | 00393 | 4 (hours) | count | ✓ | ✓(总时长未知→占比不可得) | PASS |
| 6 | 00403 | 8 (hours) | count | ✓ | **✗**:另一合理解读(省电=5h×900W×30d=135)可绕过被删变量 | **REJECT→黑名单** |
| 7 | 00456 | 60% | percentage | ✓ | ✓ | PASS |
| 8 | 00103 | 42 (miles) | count | ✓ | ✓ | PASS |
| 9 | 00352 | $11(定语 "an $11 sweater") | price | ✗ "unspecified price sweater" | ✓ | **FIX**→定语价格判不可安全删,生成器改删 $4("gave her brother an unspecified amount"),复审 PASS |
| 10 | 01059 | 60 (grams) | count | ✓ | ✓ | PASS |
| 11 | 01243 | $18.00 | price | ✓ | ✓($3 折扣与30支不足以定价) | PASS |
| 12 | 00407 | 10,000 | count | ✓ | ✓(总步数 T 未知→慢跑步数=T/2−3000 不可得) | PASS |
| 13 | 01206 | $250,000 | price | ✓ | ✓ | PASS |
| 14 | 00522 | 6 (quarts) | count | ✓ | ✓(全员速率挂在 Tony 上) | PASS |
| 15 | 01049 | 50 (books) | count | ✓ | ✓(比例齐但总量未知) | PASS |
| 16 | 00342 | 24 | count | ✓ | ✓ | PASS |
| 17 | 00283 | 8 (gemstones) | count | ✓ | ✓(beads=(25−g)/0.25,g 未知) | PASS |
| 18 | 00636 | 50 (customers) | count | ✓ | ✓ | PASS |
| 19 | 00251 | 61 (apps) | count | ✓ | ✓(61 ∉ f(9,18) ≤2步) | PASS |
| 20 | 00034 | 40 (jewels) | count | ✓ | ✓ | PASS |
| 21 | 00139 | 12 (blue) | count | ✓ | ✓ | PASS |
| 22 | 00417 | 200 (km/day) | count | ✓ | ✓(第二周300不够拼出前四天) | PASS |
| 23 | 00841 | $10000 | price | ✓ | ✓(10000 ∉ f(800,5000,200) ≤2步) | PASS |
| 24 | 01023 | 5 (sandwiches) | count | ✓ | ✓(5 ∉ f(4,2) ≤2步,含复合) | PASS |
| 25 | 00735 | 100 (voters) | count | ✓ | ✓(百分比齐、基数未知) | PASS |
| 26 | 00835 | 18 (hours) | count | ✓ | ✓ | PASS |
| 27 | 00426 | $4 | price | ✓ | ✓(三项价格全挂在 bagel 上) | PASS |

## 复审(修复后重扫)

- 00544:"divide an unspecified amount of dollars between them" ✓;
- 00352:改删 $4,"gave her brother an unspecified amount" ✓,不可解性成立(36−11−x);
- 00403:入 `INSUF_BLOCKLIST`(代码内注明理由),终版剔除;
- 全 26 条复扫:无 "unspecified price/amount+名词" 类病句、无数词泄漏、无语法残渣。

## 结论

**终版 insufficient = 26/50 主池 family,逐题人工审核通过;为凑数降质=0。**
每条 meta 含 removed_variable / variable_type / replacement / dependency_path /
why_unanswerable(依据=首步直接算子 + 表面唯一 + 无词形复述 + ≤2 步不可组合恢复 + 人工复核)。
扩产前置条件(顾问裁决保留):自动生成器不得直接扩产;扩产批次须同规格全量或分层人工审核。
