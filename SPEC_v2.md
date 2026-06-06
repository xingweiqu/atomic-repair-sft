# Atomic-Repair v2 — 规格文档(给用户拍板)

> 这份定义 v2 要造什么数据、怎么造、怎么训、怎么评。确认后才写代码。
> v2 = 把 paper《Same Benchmark Score, Different Failures》的**诊断**,接成**修复**。

---

## 0. 一句话故事

> **paper 诊断出:同样的领域分数下,模型坏在不同的原子能力上,每个坏点对应一个不同的
> 修复动作(Table 1 最后一列)。v2 接着问:假设所有 facts 已经像 pretraining 一样灌进
> 模型了(知识满分),它 inference 时这些原子能力仍然失败 —— 补什么样的 traj 数据
> (纯 CoT?还是带 skill/intervention 标签的 CoT?)能针对性地修好?**

核心假设(你的"北京→中国→普通话"):**模型知道两个 fact,但不会自发把它们接起来。**
只有用**合成实体**才能测干净(真实知识没法控制"它到底知不知道")。

---

## 1. 路线决定(已确认)

- **路 A**:复用 probing 的 **9 格扰动逻辑**(`build_natural_variants` 那套确定性字符串模板),
  但底座换成**合成实体世界**(v1 已验证的那套 + Reasoning 合成规则)。
- 不用 probing 那 90 条真实知识数据本身(真实知识 → 模型本来就会 → 知识注入无意义)。
- 复用的是**扰动的"造法"**,不是"数据"。无 API、纯确定性。

---

## 2. 九格原子能力(paper Table 1)+ 修复动作

3 域(K/R/H)× 3 扰动(Aug/Abl/Cor)。每格的 `repair_skill` = paper Table 1 的 candidate intervention。

| 格 | 域 | 扰动 | 失败诊断 (diagnosis) | repair_skill (= paper intervention) |
|----|----|----|----|----|
| **K-Aug** | Knowledge | Augment(给提示) | knowledge_not_surfaced | retrieval_cueing |
| **K-Abl** | Knowledge | Ablate(换问法) | paraphrase_fragile | paraphrase_robust_recall |
| **K-Cor** | Knowledge | Corrupt(注错claim) | wrong_factual_claim | contradiction_check |
| **R-Aug** | Reasoning | Augment(给脚手架) | needs_decomposition | decomposition_scaffold |
| **R-Abl** | Reasoning | Ablate(去规则) | rule_not_grounded | rule_reinjection |
| **R-Cor** | Reasoning | Corrupt(错中间步) | wrong_intermediate | step_verification |
| **H-Aug** | Hybrid | Augment(给桥事实) | missing_bridge_fact | bridge_retrieval |
| **H-Abl** | Hybrid | Ablate(去桥实体) | bridge_entity_missing | provide_bridge_entity |
| **H-Cor** | Hybrid | Corrupt(注错桥) | wrong_bridge_contamination | source_verification |
| **Clean** | —— | 无 | no_failure_detected | keep_answer |

> 注:paper 的扰动语义:**Augment = 加支持线索**(测"给了提示能不能用"),
> **Ablate = 去掉线索/换形式**(测"没线索/换问法还行不行"),**Corrupt = 注入错误竞争信号**
> (测"被带偏不被带偏")。Aug 用 `¬o ∧ v` 判据(原始错、加料后对);Abl/Cor 用 `o ∧ ¬v`。

---

## 3. 合成世界(底座)

### 3.1 Knowledge / Hybrid —— 复用 v1 合成实体
- 6 个关系族(book→author→nationality 等),每族 30 边,**345 条原子事实**。
- 实体全合成(Maria Voss / Lydorian),模型预训练绝对没见过(干净度闸门保证)。
- K 域 = 单跳(head→bridge 或 bridge→tail);H 域 = 两跳桥(head→bridge→tail)。

### 3.2 Reasoning —— 新建合成规则世界(复用 dataset_synthesis_mvp 的结构思路)
- 算术/逻辑规则,但用**合成的规则陈述**,测试**换数值**。
- 例:规则 "Quark-addition: 把两数相加再乘以 3"(合成的、编出来的运算名)。
  - 注入阶段:教 "Quark-addition 的定义是 (a+b)×3"(规则陈述,当 fact 注入)。
  - 测试:"用 Quark-addition 算 4 和 5" → 答案 27(**换了数值,没在注入里出现**)。
- **关键**:Reasoning 注入的是**规则陈述**,不是"题→答案"。测试用没注入过的数值组合 →
  区分"会背规则" vs "会执行规则"。这样 R 域不会变成背答案。

---

## 4. 三个阶段

### 阶段 ① 知识注入(地基,训测同集)
- 注入内容:
  - K/H 的全部 **345 条单跳实体 facts**("谁写了 X"、"X 是哪国人")。
  - R 的全部**规则陈述**("Quark-addition 的定义是…")。
- **训练集 = 测试集**(同一批,可同问法)。目的是**过拟合背死**。
- **验收闸门**:fact-QA 准确率 **≈100%**(K/H 实体事实)+ 规则陈述复述 ≈100%。
  不到就不往下走 —— 把"知识没记住"这个甩锅彻底堵死。
- **干净度对照**:原始模型(未注入)在同一批上必须 ≈0%,证明合成知识不在预训练里。

### 阶段 ② 裸能力测试(不给中间线索)
- 在"知识满分"的注入后模型上,跑 9 格的 **variant 题**。
- **输入只有 problem + tentative answer,不给 oracle facts / 不给中间桥 / 不给规则**。
- 模型必须从注入的知识里自己调用 + 接桥 + 抗干扰。
- 预期:即使知识满分,很多格仍然失败(尤其 H-Cor/H-Aug)→ **这就立住了"知道但不会用"**。

### 阶段 ③ 补 traj 修复(两种配方对比)
从阶段①的知识 checkpoint **接力**训练,两个分支:
- **C 纯 CoT**:输出 = `{repair_trace, final_answer}`(只教推理过程)。
- **D CoT+skill**:输出 = `{diagnosis, repair_skill, repair_trace, final_answer}`
  (skill = §2 表里的 intervention)。
- C 和 D **输入逐字节相同**,只差输出监督 → 隔离"skill 标签是否额外加分"。
- traj 里**不给中间线索**(和阶段②一致),教的是"如何自己接/验/抗"。

---

## 5. 四个实验条件(最终汇报)

| 条件 | 训练 | 测 9 格怎么测 | 回答 |
|----|----|----|----|
| **A** 零样本 | 不训(原始 Instruct) | 直接问,不给线索 | 光 prompt 行不行;干净度(应≈0) |
| **B** 知识注入 | 全 facts/规则注入 | 裸测 9 格 | **知识满分,能自发用吗**(预期大面积崩) |
| **C** B→纯CoT | B 接力训 CoT | 裸测 9 格 | 补 CoT traj 修好多少 |
| **D** B→CoT+skill | B 接力训带skill | 裸测 9 格 | skill 标签比纯 CoT 多多少 |

**主结论 = 逐格看 B→C→D 的提升**,以及哪些格(按 paper:H-Cor 最难)修得动/修不动。
**两道闸门**:干净度(A≈0)、学会(B 的 fact-QA≈100%)。不过就不解释 repair。

---

## 6. 泛化轴(防作弊)

- **知识**:阶段①训测同集(故意过拟合,这是地基不是泛化)。
- **9 格 variant 的"题"**:用注入过的 facts 的**新组合 / 新数值**(facts 见过,组合没见过)。
- **traj 的形式**:训练用的扰动措辞 / 推理措辞,与测试用的**不交叠**(沿用 v1 的 form 划分)。
- **实体**:repair train/eval **共享**(不是 entity-OOD);泛化只在"组合 + 形式"。

---

## 7. 要写的文件

复用:`generate_repair_data.py`(v1 合成世界)、`forms_v1.py`(K/H 扰动措辞)、
probing 的 `build_natural_variants` 扰动逻辑(搬成确定性合成版)。

新建:
- `reasoning_world_v2.py` —— 合成规则世界(规则陈述 + 换数值测试)。
- `forms_v2.py` —— 9 格的扰动措辞库(K/R/H × Aug/Abl/Cor,train/eval 划分)。
- `generate_v2.py` —— 出 5 个数据集:`inject_{train==eval}.jsonl`(知识注入,训测同集)、
  `repair_{train,eval}.jsonl`(9 格 variant,两种 traj 格式由 convert 出)。
- `convert_v2.py` —— 出 fact-only / CoT / CoT+skill / zero-shot 四种 LF 格式 + dataset_info。
- `validate_v2.py` —— 9 格计数、规则不背答案检查、注入覆盖、form 不交叠、输入一致。
- `evaluate_v2.py` —— 9 格逐格准确率 + 接受率 + 两道闸门(含 fact-QA、规则执行)。
- `compare_v2.py` —— B→C→D 逐格对比 + 闸门横幅。
- configs/v2 (Instruct、防乱码 eos)、scripts/run_v2_*、README_v2。

仓库:全部进 **`atomic-repair-sft`**(公开仓库,已定);训练交 codex,数据/eval 我写。

---

## 8. 待你拍板的点

1. **规模**:每格多少条?建议 train 每格 ~200(9格≈1800)+ Clean 200;eval 每格 ~60。
   知识注入 ~345 facts + ~R 规则数。够训练又不臃肿。
2. **Reasoning 合成规则**:用"编造运算名 + 定义"(如 Quark-addition=(a+b)×3)这种,
   还是沿用真实算术(x+5=12 解 x)?编造的更干净(模型绝对没见过),真实算术模型可能本来会。
   → 建议**编造合成运算**,与 K/H 的"合成实体"一致,干净度统一。
3. **traj 的 repair_trace 谁写**:确定性模板生成(我写,像 v1)——不走 API,保证可控。
