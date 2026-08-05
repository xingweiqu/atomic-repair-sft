# CC_INSTRUCTION_C24 — v1.2 审阅:评测侧通过/训练侧不通过;gate1-v1.2.1-exec 整改单(2026-08-05,逐字存档)

> 标准:**CC 能不能基于这个交付,可靠地进入三个端到端 smoke runs。**
> 裁决:Gate-1 evaluation prototype 通过;Gate-1 training execution package 未通过。

---

## 裁决

**评测侧的 Gate-1 原型大体通过,但训练侧还没有通过。现在仍不能批准正式 smoke。**

eval prototype:基本通过;candidate probe:原型通过;eval-side insufficient:通过但规模很小;scorer:基本通过;**answerability 训练组件:不通过**;**replay、dose 和训练执行文件:未交付完整**;**整个包:还不能独立复现训练与评测流程**。

# 这版真正修好的东西

实际检查了代码和数据,运行 scorer:selftest 50/50 pass。有效修改:1. 主评测池随机冻结50 family,不再被 insufficient builder 反向筛选;2. Insufficient 只在26可靠子集上评,26条确实逐题审过,我检查了全部26条,暂未再发现明显可恢复答案或严重病句;3. Candidate 拆成 light/full attempt/controlled contract/NL secondary;4. KEEP/REVISE 比 KEEP/CORRECT 清楚很多;5. 原始生成、逐题评分、模型 hash、chat-template hash、generation config 已保存;6. Paraphrase 50条补齐,数字一致性通过,抽查语义保留良好;7. Token 统计已用实际 Qwen tokenizer。上次评测侧最严重的问题确实被处理了。

# 但训练侧有一个明确的硬错误

审计只人工检查了 26条 evaluation insufficient,但 answerability 训练组件里还有 100 sufficient family + 100 自动生成 insufficient。这100条没有同级审计,而且我检查后仍发现明显错误。

## 1. 删除变量后题目仍然可回答

### gsm_train_06654
"John buys 2 packs of index cards for all his students. He has an unspecified number of classes and 30 students in each class. How many packs did he buy?" —— 问买多少包,第一句已说 2 packs,仍可回答2。删班级数完全没有造成信息不足。

### gsm_train_05079
"They decided to get the large popcorn & an unspecified number of drinks combo meal for $11.00 ... How much will Connor spend?" —— combo 价格固定 $11,几杯饮料不影响总价,被删的是无关变量。

说明当前自动闸门只能检查"数字参与了解题步骤",不能可靠判断删除后**最终问题**是否真的不可回答。

## 2. 训练集中仍有明显病句

gsm_train_00766 "an unspecified number of needs vegan meals";gsm_train_05267 "James bought a gallon of milk for an unspecified amount a bunch of bananas..."(缺连接词/标点);gsm_train_03830 "doubled its previous number of an unspecified number of patients"(语义不成立);另有 "an unspecified number of mgs"、"an unspecified number of Ts-shirts"、"a piece of cloth that is an unspecified number of square inches big"。

这些未必全导致标签错误,但会让 answerability 组件学到明显合成体裁:只要出现 "an unspecified number of" 就拒答。训练后的提升可能只是模板识别,不是真正的 answerability。

## 对这一部分的裁决

**Evaluation insufficient 可以保留;training answerability 不批准用于 smoke 或扩产。** CC 必须:全量审核当前100条 train insufficient;删除仍可回答的样本;修复不自然文本;记录每条人工裁决;给出最终保留率。不能只审 evaluation,不审真正送进 SFT 的训练数据。

# Candidate probe 还剩一个小但真实的模板问题

Prompt 写 "exactly two lines" 但视觉列出三行。应改为:

```text
End your reply with exactly these two lines:
DECISION=<KEEP or REVISE>
FINAL_ANSWER=<integer>
```

scorer 仍接受 KEEP|REVISE|CORRECT;正式 contract 不允许 CORRECT,也不应记 contract_followed;注释残留 KEEP|CORRECT 应清理。不是大 blocker,但正式冻结前必须修。

# Candidate stress 有效了,但还比较浅

base:Original exact .84;wc_light joint .86;wc_attempt joint .80;adoption .06。paired transition:原题对→attempt 后错 4题;原题错→attempt 后恢复 2题——净下降约2题≈4pp。已不是退化 probe,但还不是很强的抗压层。50题 Gate 原型可接受;正式扩产时增加更难但受控的版本(错误过程带合理解释;错误在中间步骤、终值看着合理;候选以较确定语气呈现)。**不要现在为追求低分反复调这50题(会过拟合 Gate 原型);正式版另建 calibration split。**

# Insufficient 的 scorer 最好也有受控主接口

candidate 已改受控输出,insufficient 主指标仍靠自由文本关键词(cannot be determined 等)。"One possible value would be 18, although the information is incomplete." 算不算猜测依赖正则覆盖。正式评测拆成:

主指标受控决策:STATUS=<ANSWERABLE or INSUFFICIENT> / FINAL_ANSWER=<integer or NULL>;报 status accuracy、answer accuracy、joint accuracy、false-abstain。次指标:自由文本 scorer,测接口外泛化。与 candidate 设计一致,减少 scorer 规则塑造曲线。

# 最关键的执行文件实际上还缺失

审计说 DOSE_DEFINITION §4b 已冻结,但 zip 里**没有 DOSE_DEFINITION.md**——无法验证 q_d 怎么算、paired bundle 排序、replay 长度桶匹配、总 target tokens 控制、偏差>2% 如何阻断、嵌套剂量清单如何生成。包里只有4个特殊组件,没有 clean replay prototype、replay carrier pool、replay length bins、dose manifest——而三个 smoke 的第一个就是 pure replay,现在没有可执行的 replay 数据。base_profile_run_v12.json 调用的 gen_predict_lawv1.py 也不在 zip。还缺 TRAIN_CONFIG.yaml、GENERATION_CONFIG.yaml、RUN_MATRIX_smoke.csv、training launcher、environment/requirements、git commit、hashes 汇总 manifest。

即使数据全对,CC 也不能仅靠这个交付重新执行完整流程。如果文件在 repo 其他目录,交付必须写清 repo commit + exact relative path + file hash,不能只在审计文档里声称存在。

# S/R 和 continuous audit 也还没有进入交付

有了 base profile,下一步应冻结 sr_subset_ids.json(base 在主画像上的固定失败题集),再生成 step-assisted / rule-assisted。包里没有。Margin/BPB 模板审计脚本也没有。可不阻塞纯行为 smoke,但不能在 Stage A 前继续缺失。

# 当前分项裁决

| 部分 | 裁决 |
|---|---|
| Main family pool | 通过 |
| Paraphrase prototype | 通过 |
| Distractor prototype | 原型通过,正式版需增加体裁多样性 |
| Format evaluation | 通过 |
| Candidate contract evaluation | 基本通过,修文案与 scorer 枚举 |
| Eval insufficient 26条 | 通过原型 |
| Scorer 自测 | 50/50 通过 |
| Base profile 可审计性 | 基本通过 |
| Selective-revision train prototype | 可进入 smoke 准备 |
| Evidence-robustness train prototype | 可进入 smoke 准备 |
| Format train prototype | 可进入 smoke 准备 |
| Answerability train prototype | **不通过** |
| Clean replay | **缺失** |
| Dose contract | **交付中缺失,无法验证** |
| Training config / run matrix | **缺失** |
| 立即执行3个 smoke runs | **不批准** |
| 扩产2,000条 | **不批准** |

# 建议给 CC 的最小下一条指令(gate1-v1.2.1-exec)

> 1. 全量人工审核100条 training-side insufficient,删除仍可回答和语法异常样本,并提交逐题裁决;不得只审核 eval subset。
> 2. 修正 candidate contract 为明确两行格式,scorer 删除 CORRECT 兼容项。
> 3. 为 answerability 增加受控 STATUS=ANSWERABLE/INSUFFICIENT 主评测,自由文本作为次级评测。
> 4. 将实际 DOSE_DEFINITION.md、clean replay prototype、replay length-bin manifest 和嵌套 bundle manifest 放入交付;不能只在审计中引用。
> 5. 补交 gen_predict_lawv1.py、冻结训练配置、推理配置和 RUN_MATRIX_smoke.csv。
> 6. RUN_MATRIX_smoke.csv 先只包含:pure replay、format low dose、format high dose。Answerability 在其训练数据审核通过前不得进入 smoke。
> 7. 每个 smoke run 必须保存 data/config/eval/scorer hash、训练日志、原始生成和逐题评分。

## 是否可以先跑什么?

在完成 replay 和训练 contract 后,**可以先跑 format 的低/高剂量 smoke**(其数据和 scorer 当前相对最清楚)。但现在这个 zip 本身还不足以启动。最准确的状态:**Gate-1 evaluation prototype 通过;Gate-1 training execution package 未通过。**
