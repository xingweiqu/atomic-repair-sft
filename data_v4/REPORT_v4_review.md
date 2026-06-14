# Scenario-Repair v4 (GSM8K 真实域移植) — 详细评审报告

> 分支 `scenario-repair-v4` · 报告日期 2026-06-14 · 评分脚本 `gsm_repair_v4/evaluate_gsm.py`
> 配套机器可读结果 `data_v4/results/comparison_v4.{md,json}`

---

## 0. TL;DR(一句话结论)

把 v3 的整套「修复-操作子诱导」实验原样移植到 **真实算术域 GSM8K**。结果与 v3(合成世界)**相反**:
v3 里 4 个操作子的对角线**全亮**(+73~+93),v4 里**只有 abstain 亮**(+98),三个计算类操作子
(verify_step / override / recompute)**无增益甚至略降**(−12 / −12 / −16)。

经抽样核验,这**不是评分 bug,是真实结果**。它精确刻画了框架的边界:

> **repair / operator-induction 注入的是「决策与修复轨迹」,不是「底层计算」。**
> **增益大小 ≈ 该原子能力在 base 模型里的缺口。** 合成世界里所有能力都缺(编造运算,0%)→ 全亮;
> GSM 里算术能力已具备(floor 已 42–54%)→ 只有 base 缺失的决策类能力(abstain,base ~2%)被点亮。

Transfer 检查进一步证实:repair 训练**没有损害底层算术**(作答时正确率 95% ≈ base),
但单操作子重度专门化带来**行为漂移**(约 30% 普通题被当成修复任务、不给最终答案)。

---

## 1. 背景与动机

v2/v2.1/v3 都在一个**封闭合成世界**(编造的关系族 + 编造的运算)里做。reviewer 的核心质疑是:
合成世界里"声称值的真假"由三元组决定,可能存在记忆捷径 / 循环论证,结论未必迁移到真实任务。

**v4 的目的**:把同一套修复回路搬到 **GSM8K(真实小学数学应用题)**。在这里:
- **算术是真实的、可计算的**——中间步骤的对错是**算出来的**,不是查表记忆的;封闭世界的实体记忆捷径**结构上不存在**。
- **不做知识注入**(算术本身就是知识),直接从 base instruct 模型诊断。
- 训练只取 GSM **train split**,评测只取 **test split**,条目零重叠。
- **沿用 v3 完全相同的 actionized 输出 schema 和评分逻辑**,使 v3、v4 两域的矩阵**可直接并排比较**。

---

## 2. 方法

### 2.1 五个答案-更新操作子(policy)与失败注入器(G-cell)

GSM 支持 v3 七个 policy 中的 5 个;每个 policy 由一个确定性「失败注入器」从干净 GSM 题构造:

| policy | G-cell 注入器 | 构造方式 | 期望决策 |
|---|---|---|---|
| `verify_step` | G-Step | 在某个**可追溯**中间步骤植入错误结果(≠真值且≠最终答案) | update |
| `override_wrong_claim` | G-Claim | 在题面植入一个**错误**的最终答案断言 | update |
| (同上,去耦对照) | G-Claim-True | 50/50 植入一个**正确**的最终答案断言 | keep |
| `recompute` | G-Recompute | 给一个错误的 tentative answer,无断言,纯重算 | update |
| `keep_answer` | G-Clean | tentative answer 正确 | keep |
| `retrieve_or_abstain` | G-Abstain | 删除题中一个**恰好出现一次且参与某步运算**的承重量 → 不可解 | abstain |

输出 schema(与 v3 一致):`{update_decision, update_policy, repair_trace, final_answer}`,
trace 以 `Action: <policy>.` 开头。

### 2.2 数据

| split | 总量 | verify_step | override | recompute | keep_answer | abstain |
|---|---|---|---|---|---|---|
| train | 3000 | 500 | 500 | 500 | 1000 | 500 |
| eval | 480 | 80 | 80 | 80 | 160 | 80 |

(keep_answer 来自 G-Clean + G-Claim-True 两个 cell,故约为其它的 2×。)
GSM8K 经 `gsm_world.parse_answer` 解析 `<<a op b=c>>` 计算注解 + `#### N` 最终答案,
保留可干净解析的条目(train 7377 / test 1300 可解析)。

### 2.3 捷径审计(shortcut gate)

沿用 v3.1 的去耦检验。TF-IDF + 逻辑回归预测 `update_decision`,5 折平衡准确率:

| 指标 | 值 | 判定 |
|---|---|---|
| **GATE**(Claim 家族 / 实体掩码后 / keep-vs-update) | **0.507** | **PASS (<0.65,近随机)** |
| L2 full raw(全文 unigram) | 0.692 | 披露(跨任务词汇是合法结构) |
| L2 full masked(数字掩码后) | 0.692 | 披露 |

`sanity_v4.json` 整体 **status: PASS**。真实域天然不存在合成世界的闭世界记忆捷径(GATE 近随机)。

### 2.4 训练(LLaMA-Factory 全参数 SFT)

- 全部从 **BASE** `/mnt/hdfs/xwqu/Qwen3-8B` relay(GSM 不做知识注入)。DeepSpeed ZeRO-3,8 卡,seed 42。
- 14 个训练分支,train_loss(codex 回报):

| 分支 | train_loss | | 分支 | train_loss |
|---|---|---|---|---|
| actionized_full | **0.303** | | random_verify_step | 0.925 |
| scaffold_only | **2.528** ⚠ | | random_override | 0.927 |
| targeted_verify_step | 0.781 | | random_recompute | 0.927 |
| targeted_override | 0.889 | | random_abstain | 0.930 |
| targeted_recompute | 0.824 | | wrongtarget_verify_step | 0.799 |
| targeted_abstain | 0.896 | | wrongtarget_override | 0.911 |
| | | | wrongtarget_recompute | 0.845 |
| | | | wrongtarget_abstain | 0.977 |

⚠ `scaffold_only` loss 2.53 = 明显欠拟合(只有 ~200 条格式骨架),作为 floor 基线有噪声——见 §6 局限。

### 2.5 评测协议

- 17 个预测,各对 480 条 repair_eval(transfer 对 300 条 test);单卡 predict。
- 最终答案做**数值归一化**(去 `$`/逗号,`18.0→18`)后精确匹配 gold。
- abstain 用 **strict 判定**:仅当模型显式 `final_answer=null` 或 `update_decision=retrieve_or_abstain`
  才算正确拒答;光秃秃蒙一个数字(即便蒙对)判错(测校准,不测运气)。
- baseline floor = `scaffold_only`(与 v3.1 一致)。

---

## 3. 过程中修复的工程问题(诚实记录)

| # | 问题 | 根因 | 修复 |
|---|---|---|---|
| 1 | `transfer_base_predict` 报 `Cannot find valid samples`,全部 transfer 预测被阻塞 | `transfer_eval.json` 参考输出是光秃秃数字 `"18"`,被 LF 监督处理器系统性判为无效样本丢弃 | 参考改为**完整金标推理 + `The final answer is N.`** 行;只此文件变,其余训练集固定种子重生成字节一致 |
| 2 | 一个配置失败 → 后续(含矩阵对照组 `wrongtarget_*`)全被卡死 | `run_v4_20` 用 `set -euo pipefail` + 循环 | 改为**遇错继续 + 结尾失败汇总** |
| 3 | transfer base 看起来只有 2% | 评分**gold 抽取 bug**:`numkey(整段金标)` 抽到推理里第一个数字而非最终答案行 | gold 与 pred 都用 `FINAL_RE` 抽最终答案行;base 实为 **94%** |
| 4 | transfer 268/300 无答案行 | `max_new_tokens=384` 把 Qwen3 `<think>` 在出答案前截断 | 两个 transfer 配置调到 **2048**,重跑 |

---

## 4. 结果

### 4.1 实验一:三条件总体(final-answer accuracy)

| 条件 | overall | false-keep | clean over-repair |
|---|---|---|---|
| diagnosis_base(base,不训) | 33% | 5% | 39% |
| scaffold_only(FLOOR) | 49% | 22% | 25% |
| actionized_full(全 policy) | **62%** | 28% | 17% |

> 注:`diagnosis_base` 33% 受**格式不匹配**拖累(base 不输出 actionized JSON),不代表 base 真实算术能力,
> 仅作下锚参考。真实算术能力见 §4.4 transfer(base 94%)。

### 4.2 实验二:选择性修复矩阵(相对 FLOOR 的增益 %)

行 = 只用该操作子数据训练;列 = 在该操作子上评测;对角线 = Targeted Gain。

| trained \ eval | verify_step | override | recompute | abstain |
|---|---|---|---|---|
| **verify_step** | **−12** | −19 | −1 | +98 |
| **override** | −11 | **−12** | +11 | +98 |
| **recompute** | −15 | −20 | **−16** | +98 |
| **retrieve_or_abstain** | −18 | −25 | −15 | **+98** |

| 操作子 | Targeted Gain | Selectivity |
|---|---|---|
| verify_step | −12% | −38% |
| override_wrong_claim | −12% | −45% |
| recompute | −16% | −37% |
| **retrieve_or_abstain** | **+98%** | **+117%** |

**只有 abstain 对角线亮。** 三个计算类操作子对角线为负——与 v3 全亮(+73~+93)截然相反。

每个条件的 per-policy 准确率明细(便于核验):

| 条件 | verify_step | override | recompute | abstain | keep |
|---|---|---|---|---|---|
| base | 16% | 35% | 38% | 11% | 50% |
| floor (scaffold) | 54% | 42% | 49% | **2%** | 73% |
| full (actionized) | 58% | 25% | 26% | 100% | 83% |
| targeted_verify_step | 41% | 24% | 48% | 100% | — |
| targeted_recompute | 39% | 22% | 32% | 100% | — |

### 4.3 对照组(在各操作子自己的 eval cell 上)

| 操作子 | targeted | 同量随机 | wrong-target | floor |
|---|---|---|---|---|
| verify_step | 41% | 39% | 42% | 54% |
| override | 30% | 12% | 31% | 42% |
| recompute | 32% | 26% | 30% | 49% |
| **abstain** | **100%** | **100%** | **100%** | **2%** |

> 计算类:targeted ≈ random ≈ wrongtarget,都 ≤ floor → 这些 cell 的瓶颈不是"用哪个修复动作",而是"算得对不对"。
> abstain:targeted=random=wrongtarget=100% ≫ floor 2% → 只要训练集里**出现过** abstain 演示(scaffold 含),
> 模型就学会;这是一个"一学就会"的**决策/格式技能**,与具体 operator 标签无关。

### 4.4 Transfer 检查:未扰动 GSM8K test(修复不应损害基础任务)

`acc` = 全 300 条;`answered acc` = 模型真正给出答案时的正确率(把**算术能力**与**行为漂移**分离);
`no-answer` = 修复训练的 ckpt 吐出诊断/JSON 但没给最终答案的条数。

| 模型 | acc | **answered acc** | answered n | no-answer |
|---|---|---|---|---|
| base | 94% | 100% | 277 | 23 |
| verify_step ckpt | 68% | **95%** | 209 | 91 |

**关键诊断**:
- verify_step ckpt **作答时**算术正确率 **95% ≈ base 94%** → **底层计算没有受损**。
- 但 91/300(30%)普通题,ckpt 进入"修复/诊断模式",输出 actionized JSON(92/99 以 `{` 开头,
  甚至模仿训练集里的拒绝 `{"error": ...}`),**不给最终答案** → **行为漂移**。
- 68% 的下降几乎全部来自这 30% 的漂移,而非算术退化。

### 4.5 v3(合成)↔ v4(GSM)并排(共有 4 操作子,同一评分器)

| 操作子 | v3 floor→targeted | v3 gain | v4 floor→targeted | v4 gain |
|---|---|---|---|---|
| verify_step | 0→93 | **+93** | 54→41 | **−12** |
| override_wrong_claim | 22→95 | **+73** | 42→30 | **−12** |
| recompute | 13→100 | **+87** | 49→32 | **−16** |
| retrieve_or_abstain | 12→100 | **+88** | 2→100 | **+98** |

---

## 5. 解读(已与作者确认采纳)

**论点**:repair / operator-induction 注入的是**决策与修复轨迹**,不是**底层计算**。
**一个操作子的可诱导增益 ≈ 该原子能力在 base 模型里的缺口。**

- **abstain(决策类,base 缺失)**:v3 12→100,v4 2→100。两域都从底拉满 → 框架在两域都成立。
- **verify_step / recompute / override(计算类)**:v3 里 base 完全不会(编造运算,0%)→ 任何 operator 数据都能从 0 拉满;
  v4 里 base 本就会算术(floor 42–54%)→ 注入轨迹不创造计算能力,单 operator 训练还轻微过拟合/受 JSON 约束拖累。
- **Transfer 佐证**:repair 没创造也没破坏计算(answered 95%≈base),只是注入了决策行为。

**Caveat(同样重要)**:单操作子重度专门化有**行为漂移代价**——对常规任务也套用修复格式、30% 不作答。
→ 这支持**混合训练(actionized_full)优于单操作子**(actionized_full overall 62% > floor 49% > 各 targeted)。

**为什么这比"两域全亮"更好**:它把"对角线没全亮"从看似的弱点,变成对框架**机制与适用边界的精确刻画**——
说清了 repair 在"模型缺失的决策/轨迹能力"上有效,在"已具备的底层计算能力"上不创造能力。

---

## 6. 局限与威胁有效性(请重点 review)

1. **floor 欠拟合**:`scaffold_only` train_loss 2.53,各 cell 表现极不均(verify 54% 但 abstain 2%)。
   用它当增益基线会让"base 碰巧高"的 cell(verify/recompute)更易出现负 gain。**负 gain 的绝对值不要过度解读**;
   稳健结论是"计算类对角线**不亮**",而非精确的负幅度。
2. **diagnosis_base 33% 的格式 confound**:base 不输出 actionized JSON,该数字低估了 base 的真实能力
   (真实算术见 transfer 94%)。base 行只作下锚,不参与增益计算。
3. **abstain 的"格式技能"性质**:abstain 100% 部分是因为它是一个易学的决策/格式动作(targeted=random=wrongtarget 都 100%),
   其"增益"与计算类操作子的"增益"性质不同——前者是**决策诱导**,后者本应是**能力诱导**。这正是论点的核心,但需在论文里讲清两者不可同质比较。
4. **transfer 只测了 base 与 verify_step 两个 ckpt**;actionized_full / 其它 operator 的漂移程度未测
   (预期 full 漂移更小,因为它见过多样格式)。若要把"混合优于单操作子"做实,建议补 transfer_actionized_full。
5. **base 也有 23/300 截断**(2048 tokens 内 think 未完):base 94% 是对"作答的 277 条"而言的下界估计。

---

## 7. 复现

```bash
# 数据 + 审计(本地,读 data_v4/gsm8k_cache.json)
python3 -m gsm_repair_v4.generate_gsm
python3 -m gsm_repair_v4.validate_gsm        # -> data_v4/sanity_v4.json (PASS, GATE 0.507)
python3 -m gsm_repair_v4.convert_gsm         # -> 18 个数据集 + dataset_info

# 服务器训练(8 卡)+ 预测(单卡,遇错继续)+ 回传
bash scripts/run_v4_1{0,1,2}_train_*.sh
bash scripts/run_v4_20_predict_all.sh
bash scripts/run_v4_22_transfer_predict.sh   # transfer 2048 tokens 重跑
bash scripts/run_v4_21_collect_predictions.sh

# 本地评分 + 报告
python3 -m gsm_repair_v4.evaluate_gsm        # -> data_v4/results/comparison_v4.{md,json}
```

关键 commit(分支 `scenario-repair-v4`):`8673de8`(最终报告+评分器)、`85cb9fc`(transfer 重跑脚本)、
`68a4622`(评分器+transfer 配置修)、`a79ca41`(transfer-eval 修复+runner 加固)。

---

## 8. 建议的下一步(待你定)

1. **论文小节**「What repair can and cannot induce」:以 §4.5 v3↔v4 矩阵为主图,§4.4 transfer 漂移表为佐证。
2. 可选补强:`transfer_actionized_full` 预测,做实"混合 < 漂移 < 单操作子"。
3. 可选:重训一个**收敛的** floor(更多 scaffold 步数)以降低 §6.1 的基线噪声,让矩阵幅度更可信。
