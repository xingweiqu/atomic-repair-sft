# CC_INSTRUCTION_C22 — Gate-1 审计裁决:骨架通过/数据未通过;gate1-v1.1 整改单(2026-08-05,逐字存档)

> 裁决:Gate 1A 工程骨架通过;Gate 1B 数据与评分质量未通过。禁止扩产、禁止正式训练。
> 执行响应:prescription/gate1/ v1.1(本文件 8 点整改)→ base profile → 3 smoke runs。

---

这次我按"**CC 能不能据此正确执行**"来检查。

## 结论

这份 `gate1.zip` 说明 CC 基本理解了 Gate 1 的工作方式:没有直接开55个训练;先做了50个题族 × 7条件;先做了4组件 × 200条训练原型;写了 builder、scorer、自动检查和审计样本;train/test 题族隔离;训练端 generator A、评测端 generator B 分开;scorer 可以运行,现有自测是16/16通过。

我实际检查后,800条训练数据来自600个独立题族,各组件之间也没有复用题族,这一点做得不错。

但是,**目前只能算"Gate 1 骨架通过,数据质量未通过"**。不能批准扩产到每组件2,000条,更不能开始正式剂量训练。

# 一、最严重的问题:Insufficient 数据还不合格

审计文件里说4个缺陷已修复并复检通过,但完整数据里仍然有明显错误,例如:

- `every second glass costs only some% of the price`
- `their ages are in the ratio of some:11`
- `wrote some/5 times more articles`
- `costs an unspecified amount.00 per carton`
- 训练 target:`The problem does not specify the number of available.`

这些不是偶发的小措辞问题,而是说明当前生成器只是把数字机械替换成 `some`,没有理解这个数字是什么类型:百分比;时间;比例;金额;数量;分数。

更关键的是,当前自动验证只是检查:被删掉的数字字符串是否还出现在题面中。这不能证明题目真的不可解。可能存在:该数字可以由其他条件推出;删除的不是必要变量;题目发生了语法破坏,但模型依然能猜出原题;原始 GSM8K 题被模型记忆。

### CC 必须改成类型化删除

至少分别处理:`60%` → "an unspecified percentage";`7:11` → "an unspecified ratio";`5:00 PM` → "an unspecified time";`$4.00` → "an unspecified price";`20 chickens` → "an unspecified number of chickens"。

并且对每个 insufficient 样本保存:

```json
{"removed_variable": "...", "variable_type": "...", "dependency_path": "...", "why_unanswerable": "..."}
```

正式扩产前,insufficient 必须经过依赖检查或人工确认,而不能只靠字符串检查。

# 二、Distractor 现在测的是"识别提示词",不是真正抗干扰

当前评测 distractor 经常写 `Unrelatedly, ...`、`which had nothing to do with the errands`;训练 target 又直接写 `The extra remark is irrelevant to the question.` 这已经明确告诉模型:下面这句话没用,请忽略。因此它测的不是模型能否从混合信息里识别无关证据,而是能否读懂 `Unrelatedly`。

此外还有生成错误:`The's cousin collected 13 stamps`;`Every noticed 13 pigeons`。而且大量 distractor 都优先使用数字13,容易形成固定模板和数字伪特征。

### 正确做法

Distractor 应该:表面上与题目主题相关;不明确写"无关";数值和实体自然变化;不改变正确答案;需要模型自己判断是否参与计算。例如原题是购买16个杯子,可以加入:"商店当天还售出了13个盘子,每个盘子售价4美元。"这比"无关地,图书馆有13本书"更像真实干扰,也没有直接泄露它是无关信息。

# 三、Selective revision 的任务定义目前不一致

Prompt 写 `Candidate answer to check: 50 (reasoning given: worked through the steps)`,但实际并没有提供 candidate reasoning,只有一个候选答案。因此现在做的其实是 **candidate-answer verification**,不是 **revision of an existing reasoning attempt**。两个任务要选一个:

- 选项 A:只检查候选答案——删掉假装存在的那句,组件改名 `candidate_verification` 或 `selective_acceptance`;
- 选项 B:真正做 selective revision——提供完整候选 attempt(Candidate reasoning + Candidate final answer),正确候选保持,错误候选只修改必要部分。这样才真正测:保留正确过程;修正错误过程;不做无必要重写。

我更建议选 B,因为这更符合你原来 keep/repair 的故事。

# 四、Scorer 可以运行,但目前会产生关键误判

16个 self-tests 全部通过,但补对抗例子马上出问题:

1. **否定候选后重算正确被算成 keep**:`The candidate is wrong. Recalculating gives 18. Final answer: 18` → K1=1, cls=keep_correct。因为只看最终答案。至少拆成 `final_correct` / `explicit_keep` / `keep_joint = final_correct AND explicit_keep`;真正的 preserve 指标用 `keep_joint`;
2. **带猜测的拒答算成正确 abstain**:`It cannot be determined exactly, but I would guess 18.` → insufficient_stop=1。代码只排除 `Final answer: <number>`,没排除其他形式的具体猜测。这会严重污染 answerability 指标;
3. **acc_exact 和 acc_loose 完全相同**:两者都用同一个 extract_loose(),只是两个名字;
4. **False-abstain 没有真正计算**:`1 - answered(original)` 是 proxy;没有输出数字可能是真拒答/格式坏/空输出/截断/没抽取出来,不等同于 false abstain。

### Scorer 至少要补的对抗单测

correct candidate 被否定但最终答案正确;insufficient 中拒答后又猜数字;原题明确拒答;输出同时出现 candidate 和 gold;JSON 内容正确但 schema 错;JSON schema 正确但内容错;多个 final answer;boxed answer 与最后数字冲突;空输出、截断和乱码。不能只靠当前16个 happy-path 测试。

# 五、Wrong candidate 的错误类型太机械

目前错误候选主要来自 gold±1、gold×10、某个中间结果。50个评测题里31个是±1、8个是×10。例如 gold=3, candidate=30;gold=64, candidate=640。这类错误太明显,容易让模型通过数值异常而不是重新验证题目。

正式版至少应有固定错误 taxonomy:算术错误;运算符错误;漏掉一个步骤;使用错误中间值;单位错误;比例方向错误;off-by-one;合理但来自错误假设。并记录每种错误的比例。最好让 wrong candidate 能对应一条具体错误推理,而不只是给一个随机错误数字。

# 六、Format 组件中存在无意义字段监督

A2 的 unit 无论题目问什么都固定 `"units"`;A3 的 confidence 永远 `"high"`。这会让模型学到 unit 永远填 units、confidence 永远填 high,不是真正的 schema following。处理:要么删除语义字段只保留纯格式结构;要么正确提取题目的单位;confidence 要么有真实定义和变化,要么不要加入。

# 七、训练 target 本身也需要清洗

训练数据直接继承 GSM8K 原始 reasoning,仍有残渣,例如 `He is going to hike 8*=40 hours`。build_gate1.py 只过滤注入的 intermediate expression,没验证整段 target reasoning 的合法性。正式数据至少需要:最终答案验证;每个可解析算式执行验证;过滤残缺表达式;对未能解析的 reasoning 做人工抽查;或只保留经过程序重构的简洁 reasoning。

# 八、所谓 token 统计目前不是 token 统计

build_stats 的 `train_target_len_tokens_approx` 实际是 `len(target.split())` 空格词数,不是 Qwen tokenizer token 数。format 2.8 / evidence 65 只能说明长度严重不均,不能用于训练预算控制。正式版必须用最终模型 tokenizer 统计:input tokens;target tokens;total tokens;每组件分布;每个 dose 的总 target-token exposure。

# 九、现在还缺哪些东西,不能训练?

冻结的正式数据集选择;base model profile;S/R failure subset;模板审计结果;完整训练 config;generation config;scorer version hash;dose/replay carrier;RUN_MATRIX.csv;三个端到端 smoke run。因此不能从"prototype 生成成功"直接跳到"扩产到2,000条,然后跑55个训练"。

# 裁决表

| 部分 | 裁决 |
|---|---|
| 目录和交付结构 | 通过 |
| 可复现 builder | 通过 |
| train/eval split 隔离 | 通过 |
| generator A/B 初步分离 | 通过 |
| 组件和条件覆盖 | 原型通过 |
| Paraphrase | 已知不合格,待重做 |
| Distractor | 不通过 |
| Insufficient | 不通过 |
| Selective revision 定义 | 待澄清 |
| Format 数据质量 | 待修改 |
| Scorer | 骨架通过,逻辑未通过 |
| 扩产到正式数据 | 暂停 |
| 正式训练 | 禁止启动 |

准确地说:**Gate 1A——工程骨架通过;Gate 1B——数据与评分质量未通过。**

# 给 CC 的下一步指令

> 当前 Gate-1 工程骨架通过,但不批准扩产或正式训练。请提交 `gate1-v1.1`,完成以下修改:
> 1. 将 insufficient 改为类型化变量删除,修复百分比、比例、时间、金额和分数等语法,并为每条样本记录不可解依据;
> 2. 将 distractor 改为未显式标注"无关"的、主题相关但答案无关的信息,消除固定数字和实体模板;
> 3. 明确 selective revision 是 candidate verification 还是 full-attempt revision;若保留 revision,必须提供候选 reasoning;
> 4. 为 wrong candidate 建立错误类型 taxonomy,并生成可解释、合理的错误过程;
> 5. 修复 scorer:区分 final-correct 与 explicit-keep,拒绝"abstain 后猜答案",实现真正的 exact/loose 与 false-abstain;
> 6. 清洗 target reasoning 中的残缺算式;修复 format 的 unit 和 confidence 字段;
> 7. 使用正式 tokenizer 输出 input/target token 分布,而不是 whitespace word count;
> 8. 新增至少30个 adversarial scorer tests,并提交随机抽样而非"每类前5条"的人工审计。
>
> 完成后先运行 base profile;确认各条件不退化,再进行 pure replay、低剂量 component、高剂量 component 三个端到端 smoke runs。未经再次确认,不得生成正式2,000条组件池或启动 Stage A。

这次 CC 的执行方向已经对了,但审计结论写得比实际数据成熟度更乐观。下一步不是换故事,也不是扩大实验,而是把这套 prototype 真正修到可以信任。
