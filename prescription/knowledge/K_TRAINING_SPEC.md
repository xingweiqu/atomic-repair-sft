# K_TRAINING_SPEC — Knowledge 域组件训练池构造规范

**状态:[FROZEN goal-mode self-certified,advisor 可追溯否决]**(2026-08-12)
依据:qc/INSTRUCTION_C26.md §三(K 组件定义)、qc/INSTRUCTION_C30.md(hard distractor
/donor 隔离/构念纪律;第 9 点点名本文件"README 声称却不存在的 K training spec(须先写出)")、
qc/INSTRUCTION_C33.md(不改科学设计)、prescription/contracts/CONTRACT_DATA.md、
prescription/TRAIN_EVAL_SEPARATION.md、prescription/DOSE_DEFINITION.md。
Builder:`prescription/knowledge/build_k_training_pools.py`(seed **20260820**,确定性)。
产物:`prescription/knowledge/pools/`(**不 commit**,manifest+sample10 每池)。

---

## 0. 源与隔离(总规)

| 项 | 决定 |
|---|---|
| 训练源 | HF `framolfese/2wikimultihopqa` **train** split(评测全部在 validation → split 天然隔离) |
| family 单位 | 2Wiki 单题;fid = `w2ktr_{idx:07d}`(train 命名空间,与评测 `w2k_` 不同) |
| 硬过滤 | 与 build_knowledge_eval.py v1 同一套:非 yes/no、答案 ≤60 字符单行、问题 6–60 词带 `?`、evidences ≥2、context ≥4 段且形状完整、supporting 完整、答案确在 supporting passage 文本内 |
| 评测隔离断言 1 | 全部行 `source_split=="train"`;train hf_id ∩(K-500 主池 500 + donor 300 = **800** 个已用 validation family 的 hf_id)= 0(结构性成立,仍显式断言) |
| 评测隔离断言 2 | norm(question) ∩ 该 800 family 的 norm(question) = 0(近重复守卫) |
| 评测隔离断言 3(supporting-title 守卫) | 候选 family 的 supporting titles 与 800 评测 family 的 supporting titles 有交集 → **整 family 弃用**(防评测支持事实以训练 target 形式被记忆) |
| 泄漏扫描 | (a)训练 target 引证句句子级子串泄漏进任一评测 prompt = **0(硬门)**;(b)训练 **target** × 评测 prompt+gold 非骨架 8-gram 碰撞逐条列出(白名单 = 本 spec + 评测 B 模板句;title 守卫排除同文章来源后残余=泛型措辞,report 供 advisor 裁决);入 manifest |
| 池间 family 隔离账 | 五池主 family **两两不相交**;evidence/revision 的 donor 池从 train split 另划,与全部五池主 family 不相交;全部登记 `pools/K_FAMILY_LEDGER.json`(C-26 §二 family 登记表要求) |
| 池内去重 | prompt 无重复;池内非骨架 8-gram family 重复率 ≤5%(CONTRACT_DATA §3) |
| generator | 训练 = **generator A**(本 spec §1 措辞);评测 = generator B(build_k500.py 措辞)。指令句、context 渲染、答句模板、判断/拒答词全部两套(TRAIN_EVAL_SEPARATION §1/§4) |
| 每池规模 | **2000 行**(达不到 = builder hard FAIL,不降格,C-33) |
| 剂量嵌套 | 每池 build 后按 seed 20260820 对 **bundle** 洗牌一次(rev/ans 的 bundle=同 family 一对,永不拆散;replay/format/evidence bundle=单条),嵌套前缀序写入 manifest(DOSE_DEFINITION §3/§4b) |
| 行 schema | `family_id, source_id, source_split, generator_id="A", generator_version="kpool-v1.0", domain="knowledge", component, subtype, template_id, prompt, target, meta`(CONTRACT_DATA §2.5) |

**Generator A 训练表面(与评测 B 面逐项不同)**
- 指令句:`Use only the information given in the sources below; do not draw on outside knowledge. If the sources do not provide what is needed, say so instead of guessing.`(评测 B:"Answer the question using ONLY the passages below…")
- context 渲染:`Sources:\n(1) {title} — {text}`(评测 B:`Passages:\n[1] {title}: {text}`)
- 问句:`Q: {question}`(评测 B:`Question: {question}`)
- 答句骨架:`Based on the source "{title}": "{sentence}" The answer is {gold}.`(评测 B 读出层:`FINAL_ANSWER=` / `DECISION=` / `STATUS=` 行,训练 target 一律不得出现这三个 token)

---

## 1. 五池构造规范

### 1.1 k_clean_replay_2000
**构念(对齐 C-26 §三)**:知识域 plain 载体 —— 给定材料 QA 本身,无任何组件行为;是 K 域 sparse 训练的 carrier/placebo 池。
- 输入:generator A 指令 + 全部 context sources + Q。
- target:答句骨架(引证句 = 含 gold 的 supporting 句,程序验证)。
- 自动校验:target 含 gold;引证 title 是 supporting title 且其文本含 gold;引证句确属该 passage。

### 1.2 k_format_2000
**构念(C-26 §三:Format=知识/给定材料 QA 上的 JSON/固定字段/citation 字段/短结构化答案)**。
- 同 1.1 输入,追加 schema 指令;**训练 schema 集 KA(k=4,冻结)轮转,每式 500**:
  - KA1 `{"answer": "<string>", "evidence_title": "<string>"}`
  - KA2 `{"entity": "<string>", "quote": "<supporting sentence>"}`
  - KA3 单行 `entity: <string> | source: <title>`
  - KA4 `<result answer="<string>" source="<title>"/>`
- citation 字段全部真实:evidence_title/source = 含 gold 的 supporting title;quote = 含 gold 的 supporting 句。
- **构念纪律注记**:任务书示例字段 `answer_entity` 被弃用 —— 它是 K 评测 schema 集 B(KB1)的字段名,进训练即毁掉"未见 schema"主指标(TRAIN_EVAL_SEPARATION §2 冻结条款)。KA 字段名与 KB1/KB2(`answer_entity` / `ANSWER=`)零交集。
- 自动校验:target 按各自 parser 重解析通过、字段集精确、answer 值 == gold、citation 字段真实;四式各 500。

### 1.3 k_evidence_2000
**构念(C-26 §三:Evidence=错误候选事实/冲突证据/无关 Wiki 段落/相似实体混淆)**。三子型均匀(667/667/666):
- `false_fact`:sources 之后插入注记行 `An attached note claims: the answer to this question is "{wrong}".`;wrong = 类匹配错误候选(同 context 非 supporting title 或 donor 池答案),≠gold 且不含 gold 别名。
- `irrelevant_passage`:从 **donor 池**取与主 family 无共享实体、无 gold 别名的 donor supporting passage,**追加为最后一条 source**(评测 distractor 为中间随机位插入 + B 面渲染 → 体裁分离,TRAIN_EVAL_SEPARATION §4)。
- `confusable_passage`:donor supporting passage 文本含主 family 的 bridge entity(非答案实体;build_k500 bridge_entities 逻辑)且不含 gold 别名,追加为最后一条 source —— 相似实体混淆段。
- donor 池:train split 另划(目标 1500 family),与五池主 family 全不相交;donor family 登记于 ledger,禁止后续任何 K 训练/评测池复用为主 family(C-30 #7 donor 永久 disjoint 纪律的训练侧对应)。
- target:先一句显式反驳/忽略(子型定式:false_fact=`The attached note is wrong: the sources do not support "{wrong}".` / irrelevant=`The source about "{donor_title}" is unrelated to this question.` / confusable=`The source "{donor_title}" mentions {entity} but does not answer this question.`),再接答句骨架。
- 自动校验:注入物不含 gold 别名;wrong ≠ gold;target 终答 == gold;反驳句在 target 内;子型计数;donor 隔离断言。

### 1.4 k_revision_2000
**构念(C-26 §三:Revision=正确知识回答保留、错误回答或依据修正)**。**1000 family × keep/fix 成对**(同 family 两条都在池内,bundle 原子,CONTRACT_DATA §3.1 的 50:50 成对纪律移植)。
- 候选体:`A previous reader answered: "{cand}", citing the source "{cited_title}".`
- keep 侧:cand = gold、引证 = 含 gold 的 supporting title;target = `The previous answer is correct — keep it.` + 答句骨架。
- fix 侧(两错误型近均匀,程序合成,禁 LLM 自由编错):
  - `similar_entity`:cand = 同 context 非 supporting title(相似实体),引证该错误 passage;错在**第一跳**(实体选取)。
  - `wrong_citation`:cand = donor 池类匹配答案,引证主 family 一个 supporting title,但该 passage 文本不含 cand;错在**第二跳**(依据不支持)。
- fix target 定式指出错在哪一跳:`The previous answer is wrong. {hop_reason}` + `The correct answer is {gold}.` 前接正确引证句;hop_reason ∈ {`It picks the wrong entity: the cited source "{t}" is not where this question's answer is established.`(第一跳), `The cited source "{t}" does not state that answer; the citation does not support it.`(第二跳)}。
- 自动校验:keep 侧 cand==gold 且 target 含 gold;fix 侧 cand≠gold(别名级)、target 终答==gold、hop_reason 存在;成对完整(family 计数 ×2 = 行数);两错误型计数。

### 1.5 k_answerability_2000
**构念(C-26 §三:Answerability=grounded-only 指令下删除必要 supporting evidence 后确实不可推出,防参数知识使标签不成立)**。**1000 family × sufficient/insufficient 成对**(bundle 原子)。
- insufficient 侧:复用 build_knowledge_eval.build_insufficient 逻辑 —— 删除所有文本含 gold 的 supporting passage;剩余 context 经**别名集扫描**(aliases():原串/去括注/去 the/逗号首段/姓氏)确认 gold 不可回收;剩 ≥3 sources;target = **定式拒答**:`The sources given here do not contain the information needed to answer this question. Based only on these sources, the answer cannot be determined.`(无任何实体猜测,不含 gold 别名)。
- sufficient 侧:原 context,target = 答句骨架。
- 仅收 insufficient 存活 family(存活率如实入 manifest)。
- 自动校验:insufficient 剩余 context 别名扫描零泄漏、target 无 gold 别名且无实体猜测句式;sufficient 终答==gold;成对完整。

---

## 2. 自动校验清单(builder 内置,任何一项失败 = hard FAIL,不出池)

1. 五池各 **n=2000**;子型/schema/keep-fix/suff-insuf 配比精确;
2. §0 隔离断言 1–3 + donor 隔离 + 池间主 family 两两不相交;
3. 池内 prompt 零重复;非骨架 8-gram family 重复率 ≤5% **在内容层计**(去引证原文 + 去申报模板常量后,残余=槽值内容——本 spec 各池 target 均为申报定式模板的程序渲染且逐条重验证,模板重复是设计不是事故;quote-stripped 与 raw 两个诊断率并排报告);
4. 训练 target 引证句 **句子级子串泄漏进任一评测 prompt = 0(硬门)**;训练 target × 评测 prompt+gold 非骨架 8-gram 碰撞逐条列出入 manifest(supporting-title 守卫已排除同文章来源,残余碰撞只能是泛型措辞,report 供 advisor 裁决);
5. 逐池内容校验(§1 各池条目);target 一律不含 `FINAL_ANSWER=`/`DECISION=`/`STATUS=`;
6. 每池 manifest:n、子型分布、family 列表 hash、donor 登记、target 长度 5 桶分布(DOSE_DEFINITION §2;与 replay 桶的 JS 散度如实申报,K 引证句天然长于 Reasoning format,残差列 limitation)、嵌套洗牌序、jsonl sha256;
7. 每池 `sample10_<pool>.md`(每子型覆盖);
8. `K_FAMILY_LEDGER.json`:family → pool 角色(main/donor)全登记 + 800 评测 family 排除记录。

## 3. 剂量与用途衔接

- K sparse 训练剂量 = `prescription/knowledge/K_SPARSE_DOSES.json`(冻结算法机械产出:format {0,30,2000}、evidence 无 onset→{0,240,2000} null check、revision {0,30,2000}、answerability {0,240,2000};clean_replay=carrier,即各组件 dose-0 的 2000 replay 臂)。
- 替换式恒 token 预算、同长度桶移除、嵌套前缀 —— 全部沿 DOSE_DEFINITION §2–§4b,carrier = k_clean_replay_2000。
- 评测:K-500 formal eval(eval_k500_proto.jsonl,validation)不变;本 spec 不触碰任何评测资产(C-33)。

## 4. 已知限制(如实申报)

1. K 训练 prompt 很长(约 10 段 context):LF `cutoff_len` 须 ≥8192,与 K-500 eval 的 max_model_len amendment 一致;
2. target 长度分布与 Reasoning carrier 桶分布 JS<0.1 大概率不满足(引证句体裁),按 DOSE_DEFINITION §4 如实申报、由同桶替换吸收一阶差异;
3. 跨 split 同一 Wikipedia 文章复用造成的 prompt 侧 8-gram 碰撞为数据集固有,以 supporting-title 守卫 + target 侧零碰撞控制要害,计数公开;
4. paraphrase 组件在 K 域仍 PENDING(与评测侧一致),不在本 spec 范围。
