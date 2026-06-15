# Scenario-Repair v4 (GSM8K 真实域移植) — 详细评审报告 (round-1 修订版)

> 分支 `scenario-repair-v4` · 修订日期 2026-06-15 · 评分 `gsm_repair_v4/evaluate_gsm.py` + `decision_analysis.py`
> 机器可读结果 `data_v4/results/comparison_v4.{md,json}` + `data_v4/results/decision_analysis_conv.{md,json}`
>
> **本版相对初版的重大更正(评审第一轮)**:初版用 **欠拟合 floor**(`scaffold_only`, train_loss 2.53,
> parse 仅 0.68–0.80, 格式半崩)当基线, 得出"计算类对角线为负、abstain 独亮 +98"。该结论**已被推翻**:
> 换成 **收敛 floor**(`scaffold_conv`, 30 epoch, parse 100%)后, 计算类对角线全部转正、abstain 增益归零。
> 欠拟合 floor 系统性地反转了结论符号。详见 §3.0 与 §6。

---

## 0. TL;DR

把 v3 的修复-操作子诱导实验移植到真实算术域 GSM8K。**收敛 floor 下的三层结论:**

1. **final-acc 层**:计算类操作子(verify_step/override/recompute)targeted 增益**小幅为正**(+4 / +10 / +8),
   abstain 增益**归零**(收敛 floor 自己也 100%)。**selectivity ≈ 0** → v4 **不是** operator-selective。
2. **decision 层**(真正的结构):targeted 把 recompute/override 的"抵抗错误值"决策从 floor **0.60/0.64**
   拉到 **0.98**(verify_step 的 floor 已 0.98);但**任一** targeted 都泛化地拉高 → 是一个**通用修复决策**, 非 operator-specific。
3. **arithmetic 层**:决策对之后的重算正确率所有 run 恒为 **~0.30–0.46**, 谁训都不提升。

**论点**:repair / operator-induction 在真实域注入的是一个**通用的"抵抗错误值"修复决策, 而非底层算术**。
final-acc 只小幅为正、且 selectivity 低, 因为决策增益被 base 算术上限压住。
**v3↔v4**:v3(合成, base 全不会)是 operator-selective(对角线突出);v4(GSM, base 已会算术)是泛化决策诱导 + 算术上限。
**Transfer**:单 operator 漂移 30%、混合 17%, 作答时算术≈base(未损害底层计算)。

---

## 1. 背景与动机

v2/v2.1/v3 都在封闭合成世界做, reviewer 质疑记忆捷径/循环论证。v4 把整套修复回路搬到 **GSM8K**:
算术真实可计算、无知识注入、train/test 条目零重叠、沿用 v3 的 actionized schema 与评分器使两域可并排。

---

## 2. 方法

### 2.1 五操作子 × 失败注入器(G-cell)

| policy | G-cell | 构造 | 决策 |
|---|---|---|---|
| `verify_step` | G-Step | 植入一个**可追溯**的错误中间步骤结果(≠真值且≠最终答案) | update |
| `override_wrong_claim` | G-Claim | 植入**错误**最终答案断言 | update |
| (去耦对照) | G-Claim-True | 50/50 植入**正确**断言 | keep |
| `recompute` | G-Recompute | 错误 tentative, 无断言, 纯重算 | update |
| `keep_answer` | G-Clean | tentative 正确 | keep |
| `retrieve_or_abstain` | G-Abstain | 删除一个**恰出现一次且承重**的量 → 不可解 | abstain |

输出 `{update_decision, update_policy, repair_trace, final_answer}`, trace 以 `Action: <policy>.` 开头。

### 2.2 数据

| split | 总量 | verify_step | override | recompute | keep | abstain |
|---|---|---|---|---|---|---|
| train | 3000 | 500 | 500 | 500 | 1000 | 500 |
| eval | 480 | 80 | 80 | 80 | 160 | 80 |

### 2.3 捷径审计

GATE(Claim 家族 / 实体掩码 / keep-vs-update) = **0.507 PASS (<0.65)**;`sanity_v4.json` status **PASS**。真实域无闭世界记忆捷径。

### 2.4 训练(LLaMA-Factory 全参数 SFT, relay from BASE)

15 个分支。关键 train_loss:actionized_full **0.30**, targeted ~0.78–0.90, controls ~0.84–0.98,
原 `scaffold_only` **2.53(欠拟合)**, **新 `scaffold_conv`(30 epoch)收敛**(parse 100%, 替换为基线)。

### 2.5 评测协议

- final answer 数值归一化后精确匹配;abstain 用 strict(蒙对判错);
- **baseline = `scaffold_conv`(收敛 floor)**。`scaffold_only`(欠拟合)仅作 §3.0/§6 的反例保留。
- **decision/arithmetic 拆分**(`decision_analysis.py`):把 final-acc 劈成
  `resist_wrong`(委托答案 ≠ 植入/tentative 错误值, 纯决策) 与 `arith_given_ok`(抵抗子集上的纯算术)。

---

## 3. 过程中修复的工程/方法问题(诚实记录)

### 3.0 ★ floor 欠拟合 → 系统性反转结论(评审第一轮发现)

初版 floor `scaffold_only` 只训 3 epoch(~37 步), train_loss 2.53, 在计算类 cell 上 **parse 仅 0.675–0.80**
(20–32% JSON 崩)。它的"高分"是格式崩溃 + judge 抽取 + 幸存者偏差的产物, 虚高的 floor 把 targeted 的增益减成了负。
**修复**:同一 scaffold 数据训到收敛(`scaffold_conv`, 30 epoch, parse 100%), 全矩阵重算 → 符号反转(见 §4)。
**教训**:floor 必须与被比较分支训练充分度可比, 否则基线噪声会决定结论符号。

### 3.1–3.4 其它(初版已记)

| # | 问题 | 修复 |
|---|---|---|
| 1 | transfer_eval 被 LF 判无效全丢弃 | 参考改为完整金标推理 + `The final answer is N.` |
| 2 | 一个配置失败阻塞后续 | predict runner 改遇错继续 + 汇总 |
| 3 | transfer base 看似 2% | 评分 gold 抽取 bug(抽到推理首数字), 改用 `FINAL_RE`, 实为 94% |
| 4 | transfer 268/300 截断 | `max_new_tokens` 384→2048 |

(另:已查 **repair eval 域内无截断**——预测 ~200 字符 ≪ 384, JSON 全闭合;漂移是行为非容量。)

---

## 4. 结果(全部基于收敛 floor `scaffold_conv`)

### 4.1 Exp 1:三条件总体

| 条件 | overall | false-keep | clean over-repair |
|---|---|---|---|
| diagnosis_base(base, 不训) | 33% | 5% | 39% |
| **scaffold_conv(收敛 FLOOR)** | **56%** | 26% | 24% |
| actionized_full(全 policy) | 62% | 28% | 17% |

> `diagnosis_base` 33% 受格式不匹配拖累(base 不输出 actionized JSON), 仅下锚;真实算术见 §4.4(base 94%)。

### 4.2 Exp 2:final-acc 选择性矩阵(相对收敛 floor 的增益 %)

| trained \ eval | verify_step | override | recompute | abstain |
|---|---|---|---|---|
| **verify_step** | **+4** | +4 | +22 | +0 |
| **override** | +5 | **+10** | +35 | +0 |
| **recompute** | +1 | +2 | **+8** | +0 |
| **abstain** | −1 | −2 | +9 | **+0** |

| 操作子 | Targeted Gain | Selectivity |
|---|---|---|
| verify_step | +4% | −5% |
| override_wrong_claim | +10% | −3% |
| recompute | +8% | +6% |
| retrieve_or_abstain | +0% | −2% |

**对比初版(欠拟合 floor):verify −12→+4, override −12→+10, recompute −16→+8, abstain +98→+0。符号全反转。**
计算类对角线转正但幅度小, selectivity ≈ 0(非对角与对角同量级, 如 override 行的 recompute cell +35)→ **v4 非 operator-selective**。

### 4.3 ★ decision/arithmetic 拆分(收敛 floor)

| cell | 指标 | floor | targeted | full |
|---|---|---|---|---|
| **verify_step** | resist-wrong(决策) | 0.975 | **1.00** | 1.00 |
| | arith-given-ok(算术) | 0.385 | 0.412 | 0.575 |
| **recompute** | resist-wrong | **0.60** | **0.98** | 0.575 |
| | arith-given-ok | 0.417 | 0.333 | 0.457 |
| **override** | resist-wrong | **0.64** | **0.99** | 0.60 |
| | arith-given-ok | 0.314 | 0.304 | 0.417 |

- **决策层**:targeted 在 recompute/override 把"抵抗错误值"从 floor 0.60/0.64 拉到 ~0.98(**+37/+35**);
  verify_step 的 floor 已 0.975(该 cell 仅靠格式即可抵抗)。混合 full 在 recompute/override 反而只有 0.58/0.60。
- **算术层**:所有 run 恒为 0.30–0.46, targeted **不提升**(见 §6 注:跨 run 因抵抗率不同有分母偏差, 不可直接横比)。
- **结论**:final-acc 的小幅正增益 = 决策诱导(大)被算术上限(顶)压平的净效应。

**decision-level 矩阵(resist-wrong, 行=训, 列=评):对角(1.0/0.97/0.99)≈非对角(0.85–0.99)** → 抵抗决策是**跨 operator 泛化**的通用技能, 非 operator-selective。

### 4.4 Transfer:未扰动 GSM8K test

| 模型 | acc | **answered-acc** | no-answer |
|---|---|---|---|
| base | 94% | 100% | 23/300 |
| verify_step(单 operator) | 68% | **95%** | 91/300 (30%) |
| actionized_full(混合) | 72% | 76% | 50/300 (17%) |

- 两个 repair ckpt **作答时**算术 ≈ base(95% / —) → **底层计算未受损**。
- 下降来自**行为漂移**:把普通题当修复任务、输出诊断 JSON 不给答案。**混合(17%)比单 operator(30%)漂移小** → 混合缓解漂移。
- 漂移是**域外**现象;**域内 repair eval 无漂移**(committed ~100%)。

### 4.5 v3 ↔ v4 并排(共有 4 操作子, 同评分器)

| 操作子 | v3 floor→targeted | v3 gain | v4 floor→targeted | v4 gain |
|---|---|---|---|---|
| verify_step | 0→93 | **+93** | 38→41 | +4 |
| override_wrong_claim | 22→95 | **+73** | 20→30 | +10 |
| recompute | 13→100 | **+87** | 25→32 | +8 |
| retrieve_or_abstain | 12→100 | **+88** | 100→100 | +0 |

v3 operator-selective(对角线突出);v4 final-acc 平淡, 真实结构在 decision 层(§4.3)。

---

## 5. 解读(已与作者确认采纳"决策 vs 计算"框架)

> **repair / operator-induction 注入的是一个通用的"抵抗错误值"修复决策与轨迹, 不是底层算术。**

- **decision 层**有效:targeted 把计算类 cell 的抵抗决策诱导到 ~0.98(floor 0.60/0.64, full 仅 0.58/0.60), floor-independent。
- **arithmetic 层**无效:重算正确率恒 ~0.35, 谁训都不动 → 这是"不注入计算"的直接证据。
- **final-acc**耦合二者:决策增益被算术上限压平 → 小幅正、selectivity 低。
- **abstain**在收敛 floor 下 gain 归零(floor 也 100%)→ 它是"见过格式即会"的格式技能, **降为正对照**(证明回路在真实域能点亮一个 base 缺失的决策能力)。
- **v3↔v4 统一**:增益结构取决于 base 缺口 + 目标能力性质。v3 所有能力皆缺且"重算=查表"(决策对→最终对)→ operator-selective 全亮;
  v4 算术已具备且"重算=真计算"(决策对≠最终对)→ 泛化决策诱导, final-acc 被算术封顶。
- **Caveat**:单 operator 专门化在**域外**有行为漂移代价(30%), 混合缓解到 17% → 支持混合训练。

**为什么比初版强**:初版把欠拟合 floor 的假象当成了"计算类无效 / abstain 独亮"。更正后, 故事是
"repair 诱导通用修复决策、受真实算术上限制约", 并用 decision/arith 拆分给出了机制级证据, 且修正了一个会被审稿人一眼看穿的 floor 偏差。

---

## 6. 局限与威胁有效性(请重点 review)

1. **`arith-given-ok` 跨 run 不可直接横比**:分母是"抵抗子集", floor/full 抵抗率低 → 子集小且偏易 → arith 虚高;
   targeted 抵抗≈1.0 → 全样本含难题 → arith 偏低。**故"targeted 算术 0.30 < full 0.42"是分母假象, 不能读成 targeted 算术更差。**
   建议最终图改在**同一难度/同一题子集**上比 arith。(本轮**尚未**做。)
2. **selectivity ≈ 0**:v4 的决策增益是泛化的(任一 targeted 都拉高所有计算类 cell), 不是 operator-specific。
   这与 v3 的强选择性不同, 需正面写(与 v2.1「action-commitment 通用」一致), 不能假装 v4 也 selective。
3. **"决策对 ≠ 修复成功"**:targeted 不被错误值带跑(resist→0.98), 但自己重算只对 ~0.30 → 等于"把 keep-错值换成 override-另一个错值"。
   从"最终修复成功率"看 targeted 未显著赢过 floor/full。论点只能是"诱导了决策、受限于算术", 不能宣称"修复成功"。
4. **transfer 的 answered-acc 定义**:full 的 answered-acc 76% 偏低(部分含 fallback 抽到的中间数), 需细化定义;
   但漂移(no-answer)对比 30% vs 17% 稳健。
5. **base 也有 23/300 截断**:base 94% 是"作答 277 条"的下界估计。

---

## 7. 复现

```bash
python3 -m gsm_repair_v4.generate_gsm && python3 -m gsm_repair_v4.validate_gsm && python3 -m gsm_repair_v4.convert_gsm
bash scripts/run_v4_1{0,1,2}_train_*.sh          # 主训练
bash scripts/run_v4_20_predict_all.sh            # 17 预测(遇错继续)
bash scripts/run_v4_22_transfer_predict.sh       # transfer 2048 tokens
bash scripts/run_v4_30_floor_and_transfer.sh     # 收敛 floor + transfer_full
bash scripts/run_v4_21_collect_predictions.sh    # 回传
python3 -m gsm_repair_v4.evaluate_gsm                                   # final-acc 矩阵(默认收敛 floor)
python3 -m gsm_repair_v4.decision_analysis --floor scaffold_conv --out data_v4/results/decision_analysis_conv
```

关键 commit(`scenario-repair-v4`):`82c1388`(decision 拆分 + 收敛 floor/transfer_full 配置), 本修订待 commit。

---

## 8. 待办(评审第二轮)

1. **同难度子集上重算 arith-given-ok**(消 §6.1 分母偏差)——可能让"算术不被注入"更干净或出现细微差异。
2. 决定主图:**decision-level matrix**(显著, +37/+35)还是 **final-acc matrix**(平淡, +4~+10)。建议前者主、后者旁注。
3. selectivity 低如何呈现:作为"v4=泛化决策, v3=选择性"的对比写入, 还是补实验尝试分离 operator。
4. (可选)transfer answered-acc 定义细化。
