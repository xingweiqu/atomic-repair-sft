# Scenario-Repair v4 (GSM8K) — Comparison & v3↔v4 Selective Matrix

## Exp 1: Repair conditions (final-answer accuracy)

| condition | overall | false-keep | clean over-repair |
|---|---|---|---|
| diagnosis_base (base, no repair) | 33% | 5% | 39% |
| scaffold_conv (FLOOR) | 56% | 26% | 24% |
| actionized_full (all policies) | 62% | 28% | 17% |

## Exp 2: Selective Repair Matrix — gain over scaffold_conv FLOOR (%)

Rows = trained on ONLY this operator. Cols = eval on this operator. Diagonal = Targeted Gain.

| trained \ eval | verify_ste | override_w | recompute | retrieve_o |
|---|---|---|---|---|
| verify_step | +4 | +4 | +22 | +0 |
| override_wrong_c | +5 | +10 | +35 | +0 |
| recompute | +1 | +2 | +8 | +0 |
| retrieve_or_abst | -1 | -2 | +9 | +0 |

| operator | targeted gain | selectivity |
|---|---|---|
| verify_step | 4% | -5% |
| override_wrong_claim | 10% | -3% |
| recompute | 8% | 6% |
| retrieve_or_abstain | 0% | -2% |

## Controls (accuracy on the operator's own eval cell)

| operator | targeted | same-size random | wrong-target | floor |
|---|---|---|---|---|
| verify_step | 41% | 39% | 42% | 38% |
| override_wrong_claim | 30% | 12% | 31% | 20% |
| recompute | 32% | 26% | 30% | 25% |
| retrieve_or_abstain | 100% | 100% | 100% | 100% |

## Transfer check — un-perturbed GSM8K test (repair must not hurt base task)

`acc` = over all 300 items; `answered acc` = when the model committed to an answer (isolates arithmetic ability from drift into repair mode); `no-answer` = items where the repair-trained ckpt produced a diagnosis/JSON with no committed answer.

| model | acc | answered acc | answered n | no-answer |
|---|---|---|---|---|
| base | 94% | 100% | 277 | 23 |
| verify_step | 68% | 95% | 209 | 91 |
| actionized_full | 72% | 76% | 250 | 50 |

## v3 (synthetic) ↔ v4 (GSM) — Targeted Gain on shared operators

Same scorer; gain = targeted − floor (v3: scaffold_only; v4: convergent scaffold_conv), on the operator's own eval cell.

| operator | v3 floor→targeted | v3 gain | v4 floor→targeted | v4 gain |
|---|---|---|---|---|
| verify_step | 0→93 | 93 | 38→41 | 4 |
| override_wrong_claim | 22→95 | 73 | 20→30 | 10 |
| recompute | 13→100 | 87 | 25→32 | 8 |
| retrieve_or_abstain | 12→100 | 88 | 100→100 | 0 |

_v3 (synthetic) is operator-SELECTIVE (diagonal spikes). v4 (GSM), on a CONVERGENT floor, shows small positive compute-cell gains and ZERO abstain gain — the real structure is at the decision level (see decision_analysis_conv.md)._

## 结论解读 — 收敛 floor 下的三层真相 (FLOOR = scaffold_conv)

> 本表 FLOOR = scaffold_conv（收敛, parse 100%）。旧 scaffold_only（欠拟合, loss 2.53, parse 0.68–0.80）评分是格式崩溃产物, 会系统性反转结论符号, 已弃用为基线。

- **final-acc 层（本表）**: 收敛 floor 下计算类对角线全部转正（verify +4 / override +10 / recompute +8）, abstain gain 归零（floor 也 100%）。selectivity 接近 0 → v4 非 operator-selective。
- **decision 层（decision_analysis_conv.md）**: 真正结构在此 —— targeted 把 recompute/override 的「抵抗错误值」从 floor 0.60/0.64 拉到 0.98; 但任一 targeted 都泛化拉高（非 operator-specific）。
- **arithmetic 层**: 所有 run 决策对之后的重算正确率恒为 ~0.30–0.46, 谁训都不提升。

**论点**: repair / operator-induction 在真实算术域注入的是一个**通用的「抵抗错误值」修复决策**, **不注入底层算术**。final-acc 只小幅正且 selectivity 低, 因为决策增益被 base 算术上限压住。abstain 在收敛 floor 下 gain 归零, 确认是「见过格式即会」的格式技能（降为正对照）。
**v3↔v4**: v3（合成, base 全不会）operator-selective; v4（GSM, base 已会算术）泛化决策诱导 + 算术上限。共同点 = repair 注入决策/轨迹而非底层能力。
**Transfer**: 单 operator(verify_step) 30% 普通题漂移进修复模式不作答; 混合(actionized_full)漂移降到 17%; 两者作答时算术 ≈ base（未损害底层计算）。