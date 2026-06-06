# When Unstructured CoT Hurts Factual Robustness (v2.1 §8 error analysis)

> 纯事实 + 真实例子。本地用已有 B/C/D 预测分析,无重训。数据来自 `data_v2/predict_outputs/`。

## 现象

普通 CoT(条件 C)在两个 Knowledge 格上**比知识注入(B)更差**:

| 格 | B Fact-only | C Fact→CoT | D Skill+CoT |
|---|---|---|---|
| K-Aug | 96.7% | **81.7%** ↓ | 95.0% |
| K-Cor | 91.7% | **75.0%** ↓ | 100% |
| K-Abl | 98.3% | 100% | 100% |

C 在 K-Aug 比 B 掉 15 分,K-Cor 掉 16.7 分;D(加 skill)又修回来。

## 失败模式:100% 是同一种,无一例外

逐题检查 C 在 K 格的所有失败:

| K 格 | C 答错数 | 抄了错 tentative | trace 已含正确答案 | 套用 Clean 模板 |
|---|---|---|---|---|
| K-Aug | 11 | 11(全部) | 11(全部) | 11(全部) |
| K-Cor | 13 | 13(全部) | 13(全部) | 13(全部) |
| K-Abl | 0 | — | — | — |

**每一个 C 的 K 失败都是:trace 正确复述了事实 → 套用 Clean 句式 "the tentative answer is correct; no repair needed" → final_answer 抄了那个错的 tentative。**

## 真实例子

**K-Cor**(注入了错误claim "Pendralia"):
```
题:    A common error gives the answer as Pendralia. In which country was Hilde Olmari born?
gold:   Mavinia
C trace: "The facts support the answer: Hilde Olmari was born in Mavinia.   ← 复述正确
          So the tentative answer 'Pendralia' is correct; no repair needed."  ← 却确认错的
C final: Pendralia   ← 抄了错的
D final: Mavinia     ← 对(D 先输出 repair_skill=contradiction_check 锁定"该修")
```

**K-Aug**:
```
题:    Cue: bring to mind what you know. What is the nationality of Tobias Forencia?
gold:   Brendaran
C trace: "...Tobias Forencia is Brendaran. So the tentative answer 'Drasivian' is correct..."
C final: Drasivian   ← trace 说对、答案抄错
D final: Brendaran   ← 对
```

## 客观陈述(不带解读)

1. C 在 K 格的失败 = trace 复述对(gold 出现在 trace 里),但 final_answer = tentative(错的)。
2. 这些失败 100% 伴随 Clean 模板句式 "is correct; no repair needed"。
3. 不是算错、不是被带去重新推理、不是 overthinking 生成错误事实 —— 是**决策(keep vs repair)选错**。
4. D 在同样这些题上 final_answer 正确;D 的输出在 final_answer 之前先有 repair_skill 字段(K-Cor=contradiction_check,K-Aug=retrieval_cueing)。
5. K-Abl 不受影响(C 100%)。

## 量化指标(B/C/D 全格)

| 指标 | B Fact-only | C Fact→CoT | D Skill+CoT |
|---|---|---|---|
| overall correct | 39.7% | 79.0% | 85.5% |
| gold-in-trace 但 final 错(想对但答错) | 0 | 27 | 4 |
| tentative-copy 错误(final==tentative≠gold) | 8 | 65 | 40 |
| **false-keep**(非Clean 却判 keep) | 0 | **51** | **36** |
| **repair-decision accuracy**(keep vs repair 二分类) | N/A* | 91.5% | 94.0% |

\* B 不输出 trace,无法解析其 keep/repair 决策 —— 它没有显式"决策位",直接吐答案。

K 格单列:
| | C correct | C false-keep | C decision-acc | D correct | D false-keep | D decision-acc |
|---|---|---|---|---|---|---|
| K-Aug | 49/60 | 11 | 49/60 | 57/60 | 3 | 57/60 |
| K-Cor | 45/60 | 13 | 47/60 | 60/60 | **0** | **60/60** |

## 核心 insight(可提升为 paper-level finding)

失败不在 knowledge recall,也不在 reasoning,而在 **repair-decision arbitration**:

> **Unstructured CoT can recover the correct evidence but still fail the repair decision.**
> 在每一个 C 的 K 失败里 trace 都含正确 gold;失败发生在决策位:模型套用 Clean 式
> "no repair needed" 模板,把错误 tentative 当成 final。Skill-conditioned trajectory
> 通过在生成答案前**强制 commit 一个 repair state**,消除这些 false-keep 错误。

skill 的意义因此从"提升 accuracy"升级为:
> **skill label = a pre-answer repair-state commitment** —— 它控制后续生成走 keep 还是 repair,
> 不是装饰性分类。证据:C→D 的增量主要来自 false-keep 下降(51→36)与 K-Cor 决策修正(13→0)。

## 待验证的关键 ablation:Decision+CoT

数据暗示 C→D 的提升大半可由"加一个 keep/repair 决策位"解释。新增分支验证:
- `C` CoT-only < `C_decision` (keep/repair 二分类 + CoT) < `D` (skill + CoT)
- 若 C_decision 已大幅修复 K-Aug/K-Cor → 关键是**先做 keep-vs-repair 决策**;
- 若 D 仍强于 C_decision → 更细粒度 skill 有额外价值(选具体 repair operation)。

把三层拆清楚:knowledge recall → evidence reasoning → **repair decision** → repair operation → final-answer arbitration。C 卡在 repair decision / arbitration,不在 recall。

## 可接到 atom paper 的点

atom paper 已有 "zero-shot CoT not uniformly beneficial"(Corrupt 格上 CoT 可能把 margin 推负)。
v2.1 这里是 SFT-CoT 版本的同类现象,且定位更精确:无结构 CoT 在决策位惯性套 keep 模板,
在 tentative 为错时伤害事实鲁棒性;skill-conditioned CoT 作为 repair-state control 约束决策模式。

更一般的观点(下一篇的种子):
> Many failures are not absence of knowledge or inability to reason, but failure to choose
> the correct **answer-update policy**: keep / override / verify / decompose / retrieve.
> Repair categories are not task labels — they are answer-update policies.
