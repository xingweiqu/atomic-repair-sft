# CC_INSTRUCTION_C23 — gate1-v1.1 审阅:工程基本通过/数据与探针未通过;v1.2 整改单(2026-08-05,逐字存档)

> 裁决:工程整改基本通过;评测数据真实性和 probe 定义仍未通过。不批准扩产、不批准 smoke、禁止 Stage A。
> 执行响应:gate1-v1.2(8 点)。

---

这版比上一版明显进步,但**还不能批准扩产,更不能开始正式训练**。

我的裁决是:**工程整改基本通过;评测数据真实性和 probe 定义仍未通过。**

## 已经修好的部分

selective revision 已改成完整 candidate attempt;wrong candidate 有四类错误过程,不再主要使用 gold±1、×10;distractor 不再显式写"无关信息";format 删除了固定 unit/confidence 等假字段;scorer 区分了 exact/loose、final-correct/explicit-keep;使用了正式 Qwen tokenizer 统计 token;base profile 已经跑出来;train/eval family 仍然零重叠;scorer 自测实际是 **39/39** 通过。这些说明 CC 是按照整改方向执行的,不是只改文档。

# 但有五个正式 blocker

## 1. Insufficient 数据仍然不合格(最严重)

### 仍有大量病句

```text
an unspecified number of sheeps
a an unspecified number of GBs file
an unspecified number of dozens donuts
a an unspecified quantity-mile trail
7:an unspecified quantity
an unspecified number of thans half the first one
an unspecified number of feets
an unspecified number of apples pies
```

所以"类型化删除"目前仍然主要是词法替换,不是自然、可靠的不可回答题构造。

### 更严重的是,有些题删完后仍然可以回答

例如 gsm_test_00020:10升橙汁,洒掉1升,与未知数量的菠萝汁混合,最后剩24升。虽然把15升删掉了,但仍可推出 24-(10-1)=15。它并不是真的 insufficient。

另一个 gsm_test_00042:删除了数字 5,改成 "an unspecified number of apple pies",但后面仍然保留了 "set the **five pies** out"。模型仍然知道是5个。

这说明元数据中的 "cannot be recovered from the remaining text" 在部分样本上是错误声明。verify_errors=0 只能说明字符串规则通过,不能证明不可解性。

### 裁决

正式版不能继续使用当前 typed_delete() 直接扩产。至少需要:数字和英文数词共同检查;基于完整计算依赖图删除变量;删除后重新求解,确认答案不再唯一;语言重写,而不是机械替换;50题原型先全量人工审核,而不是抽15题。对于第一版,甚至可以先手工修好50–100个 insufficient family,比扩展一个不可靠的自动生成器更安全。

## 2. Correct-candidate 的 prompt 和 scorer 不匹配

评测 prompt 只要求"自己给最终答案",没有要求明确说 KEEP;但主指标 keep_joint 要求明确出现 is correct/keep it/checks out 等关键词。因此 base profile 的 final_correct=0.90 / keep_joint=0.06——6% 主要不能解释为"模型不会保留正确结果",而是 prompt 没要求明确裁决、scorer 强制要求明确裁决。这仍然是模板带来的假结果。

### 应该改成明确任务

```text
Review the candidate attempt.
Return:
DECISION=KEEP if the attempt is correct;
DECISION=CORRECT if it is wrong.
Then provide FINAL_ANSWER=<integer>.
```

之后分别打分:decision accuracy;final-answer accuracy;joint accuracy。训练可以用自然语言,但主评测最好有稳定的决策接口;另外再用自然语言模板测试泛化。

## 3. Wrong-candidate 目前没有形成"压力"

Base profile:Original loose .90;Wrong candidate correct .94;adoption .02。加入错误候选后模型反而没有明显变差——当前 "A previous attempt concluded the answer is X" 不是有效抗压 probe,甚至可能通过"请重新检查"提示模型更认真。目前 wrong candidate 只给错误最终答案,而训练中的 selective revision 给完整错误过程,两边不对齐。

### 应该同时保留两层

1. **Wrong final answer**:轻量 candidate anchoring;
2. **Plausible wrong attempt**:包含一条具体、连贯但错误的推理过程。

主 stress probe 应该使用第二种,并根据 base profile 校准到非退化区间。否则模型本来94%都能抵抗,后续很难测出 SFT 的剂量收益。

## 4. 七条件评测集被 insufficient 生成器反向筛选了

代码里只有能生成 insufficient 版本的题,才进入整个七条件评测集。所以 Original/Paraphrase/Distractor/Candidate/Format 全部被限制在"能够被 typed deletion 处理的 GSM8K 题"上——明显 selection bias。而且不是随机抽50题,是取前50个符合条件的测试题。

### 应改为

先随机冻结一个 main_family_pool;Original/Paraphrase/Distractor/Candidate/Format 在主池上评;Insufficient 只在其中能够可靠构造的 paired subset 上评;每个条件可以有不同 n,但 pair comparison 使用共同 subset。不能为了做整齐的"50×7",让一个质量最差的生成器决定整个 profile 的题目分布。

## 5. Dose 仍然没有真正定义

真实 tokenizer 统计已经暴露:format 11.0 / revision 33.9 / answerability 58.1 / evidence 111.0——evidence 每条参与 loss 的 token 是 format 的约10倍。而且 revision 和 answerability 的 200 examples 来自 100 个 family(paired),evidence/format 来自 200 个 family。"200条数据"同时混合了 target-token exposure、独立题族数量、paired sample 数量、组件内容。

不能只在审计里写"正式阶段由 DOSE_DEFINITION 吸收",CC 必须在 smoke 前给出具体执行方案。至少要冻结:横轴主报 examples、family bundles 还是 target tokens;paired component 的一个 dose unit 是一条还是一对;replay 如何按长度匹配;是否固定总 target-token exposure;各剂量是否是嵌套 family 子集。

# Scorer 还有两个残余问题

"Cannot be determined exactly; it could be 18." 会被算成 stop=1/guessed=0——实际已给出猜测18。"The candidate seems right. Final answer: 18" 被判无 explicit keep(只识别有限固定短语)。主决策指标最好使用受控 action 输出;自由文本 scorer 放到辅助评测。另有交付一致性问题:审计文档写36个自测,脚本实际39个,需同步。

# Base profile 也还不能正式入库

包里只有 base_profile_summary.json,没有 base_predictions.jsonl / base_scores_by_item.jsonl / model checkpoint revision / chat template / generation config / 运行命令和 git commit。只能看到汇总值,无法审计某一道题为什么被算对或算错。正式 Gate 交付必须保存原始输出和逐题评分。

# 当前准确裁决

| 项目 | 结果 |
|---|---|
| Builder 工程结构 | 通过 |
| Family split 隔离 | 通过 |
| Selective revision 原型 | 基本通过 |
| Wrong-error taxonomy | 通过 |
| Format 原型 | 基本通过 |
| Token 统计 | 通过 |
| Scorer 工程 | 基本通过,仍需补边界 |
| Distractor | 原型可用,后续仍需增加多样性 |
| Paraphrase | 仍未完成 |
| Insufficient | **不通过** |
| Candidate evaluation 定义 | **不通过** |
| Base profile 可审计性 | **不通过** |
| Dose contract | **未完成** |
| 扩产2,000条 | 不批准 |
| 三个 smoke runs | 暂不批准 |
| Stage A 正式训练 | 禁止启动 |

# 给 CC 的下一步指令

> gate1-v1.1 的工程整改基本通过,但 Gate-1 数据与评测仍未通过,不得扩产或训练。请提交 v1.2:
> 1. 重做 insufficient 构造:消除病句、英文数词泄漏和代数可恢复样本;50题原型须全量人工审核并逐题标注不可解依据。
> 2. 将七条件从强制笛卡尔积改成 main family pool + condition-specific paired subset,不能由 insufficient builder 筛选整个评测集。
> 3. 对 correct/wrong candidate 使用明确的 decision contract;至少增加 full plausible attempt 版本,分别报告 decision、final answer 和 joint。
> 4. 校准 candidate probe 难度;当前 wrong-candidate 94%正确,不构成有效 stress。
> 5. 冻结 dose 定义,明确 family bundle、examples、target tokens 和 replay matching 的关系。
> 6. 修复 scorer 对 "could be 18" 等 abstain+guess 的漏判,并避免自由表达的 KEEP 完全依赖关键词。
> 7. 补交 base 原始 generations、逐题 scores、模型 revision、chat template 和 generation config。
> 8. 完成 paraphrase generator 决策。
>
> 上述通过后,才允许运行 replay/低剂量/高剂量三个端到端 smoke runs。

**这版已经从"明显不行"进步到了"核心工程可用",但 insufficient、candidate probe 和 dose 三件事没有解决前,跑训练得到的曲线仍然无法解释。**
