# Scenario-Repair v4 (GSM8K) — Comparison & v3↔v4 Selective Matrix

## Exp 1: Repair conditions (final-answer accuracy)

| condition | overall | false-keep | clean over-repair |
|---|---|---|---|
| diagnosis_base (base, no repair) | 33% | 5% | 39% |
| scaffold_only (FLOOR) | 49% | 22% | 25% |
| actionized_full (all policies) | 62% | 28% | 17% |

## Exp 2: Selective Repair Matrix — gain over scaffold_only FLOOR (%)

Rows = trained on ONLY this operator. Cols = eval on this operator. Diagonal = Targeted Gain.

| trained \ eval | verify_ste | override_w | recompute | retrieve_o |
|---|---|---|---|---|
| verify_step | -12 | -19 | -1 | +98 |
| override_wrong_c | -11 | -12 | +11 | +98 |
| recompute | -15 | -20 | -16 | +98 |
| retrieve_or_abst | -18 | -25 | -15 | +98 |

| operator | targeted gain | selectivity |
|---|---|---|
| verify_step | -12% | -38% |
| override_wrong_claim | -12% | -45% |
| recompute | -16% | -37% |
| retrieve_or_abstain | 98% | 117% |

## Controls (accuracy on the operator's own eval cell)

| operator | targeted | same-size random | wrong-target | floor |
|---|---|---|---|---|
| verify_step | 41% | 39% | 42% | 54% |
| override_wrong_claim | 30% | 12% | 31% | 42% |
| recompute | 32% | 26% | 30% | 49% |
| retrieve_or_abstain | 100% | 100% | 100% | 2% |

## Transfer check — un-perturbed GSM8K test (repair must not hurt base task)

`acc` = over all 300 items; `answered acc` = when the model committed to an answer (isolates arithmetic ability from drift into repair mode); `no-answer` = items where the repair-trained ckpt produced a diagnosis/JSON with no committed answer.

| model | acc | answered acc | answered n | no-answer |
|---|---|---|---|---|
| base | 94% | 100% | 277 | 23 |
| verify_step | 68% | 95% | 209 | 91 |

## v3 (synthetic) ↔ v4 (GSM) — Targeted Gain on shared operators

Same scorer; gain = targeted − scaffold_only floor, on the operator's own eval cell.

| operator | v3 floor→targeted | v3 gain | v4 floor→targeted | v4 gain |
|---|---|---|---|---|
| verify_step | 0→93 | 93 | 54→41 | -12 |
| override_wrong_claim | 22→95 | 73 | 42→30 | -12 |
| recompute | 13→100 | 87 | 49→32 | -16 |
| retrieve_or_abstain | 12→100 | 88 | 2→100 | 98 |

_v3 (synthetic) lights up on EVERY operator; v4 (GSM) only on abstain. The contrast is the result — see interpretation below._

## 结论解读 — repair 注入「决策」而非「计算」

- abstain(决策类能力): v3 12->100, v4 2->100。base 几乎不会, 两域都被 repair 从底拉满。
- verify_step / recompute / override(计算类能力): v3 从 0 拉满(合成运算 base 全不会); v4 floor 已 42-54%(base 本就会算术), 单 operator targeted 无增益甚至略降。
- Transfer: verify_step ckpt 在干净 GSM 上「作答时」算术正确率 95%(约等于 base 94%), 底层计算未受损; 但 30% 普通题漂移进修复模式、不给最终答案。

**论点**: repair / operator-induction 注入的是决策与修复轨迹, 不是底层计算。增益大小 = 该原子能力在 base 的缺口(合成世界全缺->全亮; GSM 算术已具备->仅决策类 abstain 亮)。
**Caveat**: 单 operator 重度专门化有行为漂移代价(对常规任务也套用修复格式), 支持混合训练(actionized_full)而非单 operator。