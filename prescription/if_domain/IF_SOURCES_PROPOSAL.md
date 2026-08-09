# IF_SOURCES_PROPOSAL — General IF 域五池数据源方案(C-28 P0;2026-08-09)

> 状态:**全部 [PROPOSED],等待批准后才进 CONTRACT_DATA amendment 冻结**。
> 本文件只做决策提案;三个可立即构造的池已按本提案落原型 200 条
> (`if_{revision,answerability,evidence}_proto.jsonl`,builder `build_if_proto.py`,
> seed 20260817,自动校验零错误)。if_format / if_clean_replay 全仓无源,只给候选方案。
> 组件命名遵循 C-28 ①:3/4 intervention components + clean replay 为 control,不同级。

## 0. 原料现状(已实际打开核对字段)

| 源 | 位置 | 实际规模/字段 | 许可 |
|---|---|---|---|
| CREPE (tasksource 镜像) | HF cache `datasets--tasksource--CREPE`(train/dev/test = 3462/2000/3004) | train 纯 false-presupposition 907 条,全部带 `presuppositions`+`corrections`+25 段 `passages`;train∩test id 交集=0(已验证) | 公开研究发布(Yu et al. 2023;镜像无显式 LICENSE 文件 — 冻结前须回查原 repo,标风险) |
| FalseQA | `naturalset/raw/test.csv` 1374 行 | **687/687 label=1/0 按位置成对**(第 i 行 ↔ 第 687+i 行为同题真/假前提改写,mean Jaccard 0.69,已验证);label=1 答案为 list 字面量(gold 驳斥),label=0 为普通答案字符串 | thunlp FalseQA(ACL 2023);**只有 test split 在本地**,冻结前应下载 train/dev |
| sycophancy-eval answer | `naturalset/raw/syco_answer.jsonl` 7268 行 | 1817 base 题 × 4 模板(无压/否认正确/主张错误/主张正确);base = trivia_qa 1000 题 + truthful_qa 817 题,全部带 correct/incorrect_answer | meg-tong/sycophancy-eval(MIT) |
| natural_set_v1 | `naturalset/natural_set_v1.jsonl` | 已消耗 CREPE-test 50 / FalseQA 30 / syco 30 —— 全部按 family 从训练池排除(已实现) | — |

可用 family 上限(过滤后实测):CREPE-train fp **905**;FalseQA 成对 **597**;
syco trivia_qa **972**(TruthfulQA 全排除,理由见 §3)。

## 1. 逐池方案

### 1.1 if_revision(selective_revision)[PROPOSED — 原型已落]

- **源**:CREPE train 纯 fp 行。prompt = 2 篇按内容词重叠度选出的去 markup passages + 问题 + 候选回答;成对:keep 侧候选 = gold correction,fix 侧候选 = 标注的 false presupposition 以陈述句形式作为回答;fix target 引用 gold correction。
- **规模**:905 family × 2 = 1810 行上限(<2000;按 C-28 ⑦ 以 q_d 为跨组件主轴,不与 2000 池按条数横比)。
- **泄漏**:train split 与 naturalset 消耗的 test split 天然隔离;dev 留作域内主评测(§4)。

### 1.2 if_answerability [PROPOSED — 原型已落]

- **源**:FalseQA 位置成对 (i, i+687)。同一 family 两行:false_premise 侧 target = 定式体裁 "The question rests on a false premise. {gold 驳斥}";answerable 侧 = 数据集普通答案。
- **规模**:597 pair × 2 = 1194 行上限。**补源提案**:下载 FalseQA train(≈1867)/dev(≈491) 扩池并把本地 test 让位给评测;次选从 CREPE fp 行补 answerability 面(C-28 已裁定 pool 级跨组件共享 family 允许,recipe 级同 family 只留一个版本)。
- 对应 K 域 grounded-answerability 纠正(C-28 ⑤):FalseQA 的"不可答"由前提虚假性而非材料删除承载,防参数知识破坏标签的问题不存在,但 gold 驳斥为自由文本 → 需行为级 scorer(§3 风险)。

### 1.3 if_evidence(evidence_robustness)[PROPOSED — 原型已落]

- **源**:sycophancy-answer,**仅 trivia_qa base**;两子型:assert_wrong("I think the answer is {incorrect}")与 deny_correct("I don't think the answer is {correct}");target = 显式否定压力 + 正确答案(gate1 evidence "显式否定错误信息" 体裁的 IF 对应)。
- **规模**:972 family;原型 1 行/family(100+100);扩产可 2 子型/family 成对 → 1944 行。可加第三子型 no-pressure control(原模板 `{question}`)作为组件内配对 control。
- **排除 TruthfulQA base(817 题)**:TruthfulQA 是通用标准评测集,训进 SFT 会污染一切后续 truthfulness 评测;此为硬排除建议。

### 1.4 if_format [PROPOSED — 全仓无源,两条候选路线]

- **F-A(推荐)自建 schema 载体**:载体任务 = SQuAD v2 可答子集抽取式 QA(HF `rajpurkar/squad_v2`,train 86k/dev 12k,CC BY-SA 4.0,与 CONTRACT_DATA §1 IF 候选清单一致)+ AG-News 分类(120k,常用研究许可需下载时核对);训练 schema 集 A(k=4,与 Reasoning format 同构:`{"answer": str}` / `{"answer": str, "evidence": str}` / `<answer>…</answer>` / `answer: …`),自动校验 = parser 通过 + 字段齐 + 抽取值==gold span/label。评测用 schema 集 B(disjoint 措辞与结构),满足 TRAIN_EVAL_SEPARATION。
  - 泄漏风险:SQuAD 深度进入各家预训练;作为**训练载体**可接受(测的是 schema 服从不是知识),但 IF format 评测应落在 CREPE-val 载体或 SQuAD-dev 持出 family 上,并跑 8-gram 碰撞扫描。
- **F-B 公开 IF 数据集**:IFEval(google,541 prompt,Apache-2.0)可程序验证但规模小且是社区标准评测——**建议只作 IF 域 cross-dataset holdout(eval-only),禁止训练**;Conifer / Tulu-3-IF 类为 LLM 生成、目标不可程序验证、许可混杂 → 不推荐进正式池。
- 裁决请求:批准 F-A(SQuAD v2 + AG-News 载体、schema A/B 分离)+ IFEval 冻结为 eval-only holdout。

### 1.5 if_clean_replay [PROPOSED — 全仓无源,两条候选路线]

- **R-A(推荐)域内自建 plain 池**:与组件池同分布族但 family 不相交的"无组件结构"任务:CREPE normal 行(2535)阅读理解简答 + SQuAD v2 plain QA(无 schema 指令)+ AG-News plain 分类,按 loop3 cleanreplay / lawv1 carrier 的角色构造:2000 条,5 长度桶,桶内移除序冻结(DOSE_DEFINITION §4,与组件池 JS<0.1 长度对齐)。理由:replay 是 control/被替换池,必须与组件池同域同分布,引入外部通用 SFT 数据会造成分布混淆。
  - 注意:CREPE normal 行的参考回答是 Reddit ELI5 `comment`(冗长、口语、无验证)→ 建议 replay 侧允许(control 不要求可验证),但 clip + 长度桶控制。
- **R-B 公开数据集**:databricks-dolly-15k(CC BY-SA 3.0,人写,含 closed_qa/extraction/classification/summarization 类目,天然 IF 流量)。风险:被广泛用于各家 SFT,Qwen3 预训练大概率见过(replay 异常易 → control 失真);风格与组件池异质。→ 仅作 R-A 不足时的补充类目。
- 裁决请求:批准 R-A 为主,R-B 补充与否留待 pilot。

## 2. Condition applicability matrix(逐任务型;C-26 §4 要求,不机械全条件)

✓=适用 △=改造后适用(附做法) ✗=不适用(不硬造)

| 任务型 | clean_replay(control) | format | evidence | revision | answerability |
|---|---|---|---|---|---|
| extraction(SQuAD v2 式) | ✓ | ✓ schema 输出 | △ 干扰段落/塞入错误 span 建议 | ✓ 候选 span keep/fix | ✓ **原生**(SQuAD v2 unanswerable) |
| classification(AG-News/TREC) | ✓ | ✓ label schema | △ 用户主张错误 label(syco 型) | ✓ 候选 label keep/fix | △ 界外/歧义样本,标签脆弱 → pilot 后再定 |
| rewriting/correction(CREPE) | ✓ | △ 输出包裹 schema | ✗ 无可验证事实压力面 | ✓ **原生**(gold corrections;已落原型) | △ fp 检测面(与 revision 共 family,recipe 级去重) |
| reading comprehension(CREPE passages / QA) | ✓ | ✓ | ✓ 冲突/干扰段落;syco 压力(已落原型) | ✓ | ✓ FalseQA 假前提(已落原型);△ 删支撑段落式留给 K 域,避免与 grounded-answerability 构念重复 |
| constraint following(长度/关键词/语言约束,自建可验证) | ✓ | ✓ **原生**(即组件本体;IFEval 只作 holdout) | ✗ | △ 候选违约输出 → 修复 | ✗ |
| structured response(JSON/表格生成) | ✓ | ✓ 原生 | ✗ | △ 修复畸形 JSON | △ 必填字段缺失 → 显式声明缺失,不硬编 |

## 3. 三大质量风险(原型已暴露,冻结前须处理)

1. **CREPE 证据链弱**:passages 是检索段落,不保证蕴含 correction(已做 markup 过滤+重叠度选段,但仍非蕴含保证);correction 本身源自 Reddit 评论区共识,事实性未独立核验。→ 扩产前抽 50 条人工审 passage-support 率,<80% 则 revision 池降级为 "question+candidate"(去 passages)体裁。
2. **表面捷径**:revision 池 fix 侧候选=复述题内前提、keep 侧候选=反驳题内前提 → 可能学到"候选反驳问题即 keep"的立场捷径而非核对;if_evidence 同理存在"题内出现 I think → 否定它"的模板捷径(deny_correct 子型压力值=正确答案,可部分对冲)。→ 扩产时加 no-pressure control 子型 + assert_correct(应 keep)子型做对冲,评测侧换 B 套措辞。
3. **自由文本目标不可机械验证**:三池 target 均非数值/span,现有 lawv1_score 不适配(C-28 ④ strict=0 仪器报警的同类问题);FalseQA answerable 侧部分答案质量低(已过滤 <10 字符,仍有弱答案)。→ 正式 IF eval 冻结前必须先定行为级 scorer(premise-flag 检出 / pressure-resist / correction-content 三个判定器),否则曲线不可读。

## 4. Train/eval 隔离方案 [PROPOSED]

1. **CREPE**:train=组件池;**validation(2000,fp 544)冻结为 IF 域内主评测**(训前冻结 id 清单);test=archive(50 id 已被 naturalset 消耗)。
2. **FalseQA**:pair 为 family 单位(两侧同 split)。现 597 可用 pair:若批准下载 train/dev → train/dev 训练、本地 test 整体转评测;否则自分区 400 train / 197 eval(seed 20260817 洗牌后前缀),naturalset 30 题 family 全排除(已实现)。
3. **sycophancy**:family=base 题,**4 模板变体同 split**(防同题跨 split);trivia_qa 972 可用 family 自分区(建议 700 train / 272 eval);评测侧压力措辞换 B 套(不与训练模板共措辞,CONTRACT_DATA §2.3/2.4)。
4. **跨工具**:三池 train-proto family 清单已写入 `if_proto_manifest.json`,未来任何 IF 评测构造必须排除;natural_set_v1 全 200 题永久排除;IFEval(若批准)为 eval-only holdout;正式池冻结前跑全仓 8-gram 碰撞扫描(白名单=体裁骨架,报告入 qc/)。
5. **跨组件**:pool 级共享 source family 允许(C-28 已裁定),recipe/mixture 级同 family 最多一个版本。

## 5. 待裁决清单

| # | 事项 | 建议 |
|---|---|---|
| 1 | if_format 路线 | F-A(SQuAD v2+AG-News 载体,schema A/B 分离) |
| 2 | if_clean_replay 路线 | R-A(域内 plain 池:CREPE-normal+SQuAD+AG-News) |
| 3 | IFEval 角色 | eval-only cross-dataset holdout,禁训 |
| 4 | TruthfulQA base | 永久排除出训练 |
| 5 | FalseQA train/dev 下载 | 批准(服务器 xwqu-lq 代理,`source ~/atomic_env.sh`) |
| 6 | 三个原型池体裁 | 按 §3 风险处理后扩产;先过 20 条/池人工抽检(CONTRACT_DATA §3 通用规则) |
