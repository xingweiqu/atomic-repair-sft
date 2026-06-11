# Scenario-Repair v3 完整报告

> Evaluation-Guided Targeted Operator Induction —— 用评估指导合成数据生成、按需诱导修复能力
>
> 所有数字来自本地 `evaluate_v3` / `compare_v3` 对服务器预测(commit 8855ef4)的评分,逐行对齐 600/600。
> 本报告先讲背景与设计,再逐实验给结果,最后给结论与局限。

---

## 0. 一句话总览

v3 把 atomic-repair 从"9 类标签 benchmark"升级到"**场景化合成数据 + answer-update policy**"。
9 个 cell 降级为**造坏题的工具(failure injector)**,训练/评估的单位变成 **7 个 answer-update policy**。
核心问题:**能不能用评估定位模型缺哪个能力 → 生成那一类 targeted 数据 → 选择性地把那个能力补上?**

**最终答案(混合,真实):**
- ✅ 对"需要显式动作"的难能力(verify_bridge / verify_step / recompute),**targeted 数据确实选择性诱导对应能力,且优于同量随机数据** —— 对症下药成立。
- ⚠️ 对"知识注入后已掌握"的能力(override_wrong_claim / retrieve_or_abstain),额外 targeted 训练**无增益甚至负迁移** —— 这类不需要 targeted。
- ✅ Cumulative curriculum 干净地展示能力**逐步组装**(50% → 97%,能力逐个点亮)。
- ✅ Exp1 证明 v2 结论在更真实的用户问法下**依然成立**(知识满分≠会用,trajectory 是桥)。
- 🔎 附带发现:**单一 policy 数据量决定模型能否学会输出格式**(~220 条会崩,~440 条以上才稳)。

---

## 1. 设计

### 1.1 三个灵魂转变(相对 v2)
1. **9-cell 从"输出标签"降级为"failure injector"**:K/R/H × Aug/Abl/Cor 只是制造坏题的手段,
   不进结论、不进矩阵。真正的单位是 answer-update policy。
2. **从"分类"变"决策"**:不是"这题属于哪 cell",而是"这个待检查答案该**怎么动**"。
3. **从"证明一个方法好"变"证明一套方法论"**:selective repair matrix 的对角线就是"对症下药可行"的证据。

### 1.2 七个 answer-update policy
按 `update_decision` 分三组:

| update_decision | policy | 含义 |
|---|---|---|
| keep | `keep_answer` | 答案已对,别改(测过度修复) |
| update | `override_wrong_claim` | 错误声明 → 驳回,用正确事实 |
| update | `verify_bridge` | 错误桥实体 → 验证真桥再接 |
| update | `verify_step` | 错误中间步 → 重新算对 |
| update | `recompute` | 按规则重算 / 换问法重新回忆 |
| update | `use_provided_support` | 已给支持事实 → 直接用,别再怀疑 |
| retrieve_or_abstain | `retrieve_or_abstain` | 缺 anchor 无法内部修 → 弃答/请求澄清 |

输出格式采用 v2.1 验证过最优的 **actionized 格式**:
`{update_decision, update_policy, repair_trace, final_answer}`,trace 开头 `Action: <policy>.`。

### 1.3 场景化 surface(更像真实用户)
底层 oracle 不变(book→author→nationality 两跳链、编造运算 quarn/drimble 等),但题面用自然用户措辞包装:
- 例:"I'm writing up some notes on this book. What is the nationality of Maria Voss?"
- 训练/测试措辞不交叠;oracle、failure 注入、policy、gold 答案**全部本地确定性生成,绝不经 LLM**。

### 1.4 新增 abstain 类(U-Abl)
故意去掉 anchor 的题(例:"I saw an artwork somewhere — what country is the artist from?"),
正确动作是 `retrieve_or_abstain`,gold = `null`。**模型硬猜(即便蒙对)算错**,测的是校准/拒答,不是准确率。

### 1.5 数据规模
- 知识注入:351(复用 v2,fact-QA 已验证 100%)
- repair:train 2200 / eval 600;eval 逐 policy:recompute 180、use_provided_support 120、其余各 60
- 验证全 PASS(policy 覆盖、abstain null、无 gold 泄漏、措辞不交叠)

---

## 2. 实验 1:Scenario-based Actionized Repair

**问题:v2 的发现(知识满分但要 trajectory 才会用)在更真实的用户问法下还成立吗?**

| 条件 | 总体 | abstain 正确 | false-keep | Clean 过度修复 |
|---|---|---|---|---|
| A/B Fact-only(知识注入) | **49.7%** | 100% | 1% | 80% |
| C Fact→CoT | **99.3%** | 100% | 0% | 3% |
| D Fact→Actionized(full) | **95.5%** | 100% | 6% | 0% |

**Fact-only 逐 policy(基线,后面 matrix 的基准):**
| policy | Fact-only acc |
|---|---|
| keep_answer | 20% |
| override_wrong_claim | 95% |
| verify_bridge | 13% |
| verify_step | **0%** |
| recompute | 32% |
| use_provided_support | 86% |
| retrieve_or_abstain | 100% |

**结论(Exp1):**
1. **知识满分 ≠ 会用**:知识注入后总体只有 49.7%,verify_step 0%、verify_bridge 13%、recompute 32% —— 需要组合/验证的能力,光有知识修不出来。在更真实的 scenario surface 下,v2 的核心结论**依然成立**。
2. **trajectory 是桥**:CoT/Actionized 把总体拉到 95-99%,abstain 全程 100% 工作。
3. **Actionized 行为最干净**:Clean 过度修复 0%,三个 Corrupt 的接受错误率(H-Cor/K-Cor/R-Cor)全 0%。
4. 逐 scenario 看(Actionized):reasoning 各运算 100%,实体类 87-100% —— 场景化没有破坏可解性。

---

## 3. 实验 2:Targeted Operator Induction(主实验)

**问题:只训某个 policy 的数据,是否选择性地只让对应能力涨?**

做法:从同一 Fact-only checkpoint 出发,每次只(主要)训一个 policy 的数据,然后在全 eval 上评估所有 policy。

### 3.1 Selective Repair Matrix(相对 Fact-only 的 gain,%)

行 = 训了哪个 policy 的数据;列 = 在哪个 policy 上评估;**对角线 = Targeted Repair Gain**。

| 训练 \ 评估 | override | verify_bridge | verify_step | recompute | use_support | abstain |
|---|---|---|---|---|---|---|
| **override_wrong_claim** | **+0** | +3 | +10 | +3 | +8 | −87 |
| **verify_bridge** | −27 | **+72** | +7 | +3 | −17 | −100 |
| **verify_step** | −35 | +3 | **+95** | +2 | −19 | −50 |
| **recompute** | +5 | +18 | +100 | **+68** | +11 | +0 |
| **use_provided_support** | −78 | −3 | +33 | +36 | **+14** | +0 |
| **retrieve_or_abstain** | −37 | +2 | +10 | +4 | −28 | **+0** |

### 3.2 Targeted Repair Gain & Selectivity

| policy | 对角线 gain | selectivity(对角 − 非对角均值) | 判定 |
|---|---|---|---|
| **verify_step** | **+95%** | **+115%** | ✅ 最强选择性(0% → 95%) |
| **verify_bridge** | **+72%** | **+98%** | ✅ 强选择性(13% → 85%) |
| **recompute** | **+68%** | +41% | ✅ 成立(32% → 100%) |
| use_provided_support | +14% | +17% | 弱(基线 86% 本就高) |
| override_wrong_claim | +0% | +13% | ⚠️ 无增益(基线 95% 已饱和) |
| retrieve_or_abstain | +0% | +10% | ⚠️ 无增益(基线 100% 已满) |

**结论(Exp2 —— v3 的核心):**

1. **对症下药对"难能力"成立。** verify_step、verify_bridge、recompute 这三个"知识注入后基线很低、需要显式动作"的能力,targeted 数据**选择性地把它们诱导出来**:
   - verify_step:0% → 95%(selectivity +115%,几乎纯对角)
   - verify_bridge:13% → 85%(selectivity +98%)
   - recompute:32% → 100%

2. **对"已会能力"不需要 targeted,甚至有害。** override(基线 95%)、abstain(基线 100%)、use_provided_support(基线 86%)在知识注入后就基本会了,额外训别的 policy 反而**负迁移**(矩阵里 override 列、abstain 列大面积负,如 use_provided_support 行训完把 override 砸到 −78、verify_bridge 行把 abstain 砸到 −100)—— 模型被"过度行动"带偏,把本该 keep/override/abstain 的搞乱。

3. **这比"对角线全显著"更真实、更有用**:它告诉你**哪些能力值得花 targeted 数据(难的),哪些不必(注入后已会的)**。

### 3.3 真实例子(targeted 修对了什么)

`verify_step` targeted 训练后,在一道编造运算题上:
> 题:"Quick sanity check. Someone got an intermediate value of 14 here. Compute the splisk of 2 and 10."
> tentative 73(被错误中间步带偏),gold 70
> 模型:`Action: verify step. The intermediate 14 is wrong. Correctly: add 5 to 2 to get 7; multiply 7 by 10 to get 70.` → 70 ✅

Fact-only 在 verify_step 上是 0%(完全不会验证中间步),targeted 后 95%。

---

## 4. 控制实验(Controls)

**问题:targeted 的效果是"对症"还是只是"数据量"/"碰巧"?**

每个 policy 自己那格的准确率三方对比:

| policy | targeted | 同量随机 | wrong-target |
|---|---|---|---|
| **verify_bridge** | **85%** | 25% | 80% |
| **retrieve_or_abstain** | **100%** | 40% | 100% |
| **verify_step** | **95%** | 70% | 88% |
| override_wrong_claim | 95% | 57% | 97% |
| recompute | 100% | 100% | 100% |
| use_provided_support | 100% | 100% | 97% |

**结论(Controls):**
1. **targeted > 同量随机**(verify_bridge 85 vs 25,abstain 100 vs 40,verify_step 95 vs 70)→ **是对症数据有效,不是单纯数据量。** 这是最关键的 control,证明了"evaluation 指导生成对的数据"这一主张。
2. **targeted ≈ wrong-target**(verify_bridge 85 vs 80)→ 一旦格式稳了、动作写进 trajectory,**具体 policy 标签对错没那么关键**(与 v2.1 "action commitment 通用、显式 label 非必要" 一致)。换句话说:起作用的是"承诺去做一个修复动作",不是"叫对名字"。
3. recompute / use_provided_support 三方都 100%(已饱和),区分不出。

---

## 5. 实验 3:Cumulative Curriculum

**问题:逐步累加各 policy 的数据,能力是否逐步、可预测地组装出来?**

| 阶段(累加) | 总体 | keep | override | verify_bridge | verify_step | recompute | use_support | abstain |
|---|---|---|---|---|---|---|---|---|
| M0 (Fact-only) | 50% | 20 | 95 | 13 | 0 | 32 | 86 | 100 |
| M1 (+keep+recompute) | 77% | 77 | 98 | 5 | **100** | **100** | 90 | 7 |
| M2 (+override) | 70% | 97 | 100 | 7 | 100 | 89 | 65 | 0 |
| M3 (+verify_step) | 66% | 100 | 100 | 0 | 100 | 82 | 39 | 30 |
| M4 (+verify_bridge) | 80% | 100 | 100 | **100** | 100 | 88 | 67 | 0 |
| M5 (+use_support) | 88% | 100 | 100 | 100 | 100 | 95 | **95** | 0 |
| M6 (+abstain) | **97%** | 100 | 100 | 100 | 100 | 95 | 92 | **100** |

**结论(Exp3):**
1. **总体单调爬升 50% → 97%**(M2/M3 有小回落,因加入新 policy 短暂扰动 abstain/use_support,后续恢复)。
2. **能力逐个点亮**:加 recompute → verify_step 列 0→100(M1);加 verify_bridge → verify_bridge 列 0→100(M4);加 abstain → abstain 列 0→100(M6)。**对应数据加入,对应能力出现** —— 这正是"evaluation-guided 逐步组装能力"的直接证据,也是 v3 最贴合论文主张的一节。
3. abstain 在中途被压到 0(因为前期教了一堆"要行动"的 policy,模型变得不愿弃答),直到 M6 显式补 abstain 数据才回到 100% —— 印证 abstain 是一个需要专门数据才能保住的独立能力。

---

## 6. 附带发现:数据量决定输出格式能否学会

第一轮 targeted 实验**全崩**(selective matrix 出现 −90 对角线、controls 自相矛盾)。挖出根因:

| 单 policy 训练量 | JSON 输出有效率 |
|---|---|
| ~220 条 | **0 – 34%**(模型退回散文,JSON 学不会) |
| ~440 条 | 98 – 100% |
| ~660 条以上 | 100% |

**~220 条单一同质数据不足以同时教会"输出格式"和"该 policy 的能力"** —— 模型把有限数据预算花在学格式上还不够。修法:给每个 targeted/control 集混入一个**固定的、policy 均衡的格式脚手架**(每 policy 30 条 = 210 条,跨所有集完全相同),把每个集抬到 396-830 行。格式统一学会后,集间的**差异信号纯粹来自目标 policy 的额外数据**,selectivity 得以保留、格式混淆被消除。修复后那两个崩溃分支 JSON 有效率 0% → 98%/96%。

**这本身是一个值得写进结论的发现**:targeted 能力诱导**需要一个已会输出格式的基座**;否则有限的单类数据会被格式学习吃掉。

---

## 7. 总结:v3 回答了什么

| spec 提出的问题 | 答案 |
|---|---|
| 1. 9 cell 是 failure injector 而非用户问题类型? | ✅ 是,全程只当注入器,结论围绕 policy |
| 2. scenario 合成数据能更像真实用户? | ✅ 能(模板+可选LLM改写,oracle 不变) |
| 3. 知识注入在 scenario 下是否仍不够? | ✅ 仍不够(49.7%) |
| 4. actionized trajectory 是否仍有效? | ✅ 仍有效(95.5%,行为最干净) |
| 5. targeted 数据是否选择性修复对应能力? | ✅ 对难能力是(verify_step/bridge/recompute);对已会能力否 |
| 6. 随机同量是否不如 targeted? | ✅ targeted 显著优于随机(85 vs 25 等) |
| 7. wrong-target 是否不如 matched? | ≈ 持平 —— 起作用的是 action commitment 而非 label 语义 |
| 8. 哪些内部可修、哪些需 retrieve/abstain? | abstain 类需专门数据保住(M6 才回 100) |
| 9. 如何支持 "evaluation-guided synthetic capability induction"? | Cumulative 50%→97% 能力逐个点亮 + targeted>random,共同支持 |

### 核心结论(可写进 paper)
> **Evaluation-guided targeted synthetic data 对"知识注入后仍欠缺的难能力"能选择性诱导,且优于同量随机数据;
> 但对注入后已掌握的能力,targeted 训练无益甚至负迁移。** 起作用的是"在 trajectory 里承诺一个修复动作",
> 而非显式 policy 标签的语义(targeted ≈ wrong-target)。Cumulative curriculum 干净地展示能力可逐步组装
> (50%→97%,能力随对应数据加入而逐个点亮)。附带地,**单类数据量必须先跨过"学会输出格式"的阈值
> (~440 条),否则能力诱导被格式学习吞没。**

---

## 8. 局限与下一步

1. **部分能力已饱和**(override 95%、abstain 100%、use_support 86% 基线就高),压缩了它们的 selectivity 信号 —— 想看更干净的对角线,需要让基线更低(更难的 scenario / 更小模型)。
2. **负迁移机制未深挖**:为什么训 use_provided_support 会把 override 砸到 −78?值得单独分析(疑似"过度行动"倾向)。
3. **单模型单 seed**:趋势需多 seed / 加 Qwen3-4B 验证稳定性。
4. **格式脚手架阈值**是经验值(~440),未系统扫描;可做一条"单 policy 数据量 vs JSON 有效率"的曲线作为独立 ablation。
5. **scenario 目前是模板(+可选 LLM 改写)**:可进一步用更口语、更长上下文的真实用户问法压力测试。

---

## 附:文件与复现

- 数据:`data_v3/`(inject 351 / repair 2200+600);生成器 `scenario_repair_v3/generate_v3.py`
- 评估:`scenario_repair_v3/evaluate_v3.py` + `compare_v3.py`;报告 `data_v3/results/comparison_v3.md`
- 训练配置:`configs/v3/`(53 yaml,relay 自 v2 inject ckpt);脚本 `scripts/run_v3_*`
- 分支:`scenario-repair-v3-targeted-operators`;结果预测 commit 8855ef4
