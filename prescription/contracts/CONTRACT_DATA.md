# CONTRACT_DATA — 数据契约(lawv1;2026-08-04 draft;Gate-3 冻结)

> 状态标记:[FROZEN]=本文件即定稿;[PROPOSED]=CC 已做决策待 Gate-1 确认;[PENDING]=显式未决,不阻塞 Gate-1。

## 1. 数据集选择

### Reasoning(发现域)[PROPOSED — Gate-1 决策项]

| 项目 | 决定 |
|---|---|
| Training source | GSM8K `main` **train** split(HF `openai/gsm8k`) |
| Main evaluation | GSM8K `main` **test** split(families 与 train 零交集,天然隔离) |
| External evaluation | SVAMP(HF `ChilleD/SVAMP`,全量持出,只评不训) |
| Split unit | family_id = GSM8K/SVAMP 单题(底题);一题所有条件版本同 split |
| Version | 下载时记录 HF revision + 文件 sha256 → `data/lawv1/source_manifest.json` |
| License | GSM8K MIT、SVAMP MIT — 均允许衍生训练数据 |
| Usable count | GSM8K train 7,473 / test 1,319;SVAMP 1,000;过滤规则(§1.1)后实数在 build 时写入 source_manifest,预计 >85% 存留 |

规模分配(冻结):eval 底题 = GSM8K-test 先到先得取前 800 过滤存活题 + SVAMP 前 200(external 面);train 侧组件构造用 GSM8K-train,与 eval 零 family 交集(不同 split 保证)。

**1.1 过滤规则**:答案为单一数值;题干 ≤ 300 tokens;程序可验证(gold 可解析为数);去重(题干 32-gram 指纹)。

### Knowledge(确认域)[PENDING — Stage B build 前决策,不阻塞 Gate-1]
候选:2Wiki dev(repo wiki2/ 已有)+ StrategyQA;insufficient 按 APPLICABILITY_MATRIX 的 adapted 规则。决策走 amendment。

### IF(确认域)[PENDING — 同上]
候选源清单:抽取=SQuAD v2 段落改造;分类=AG-News/TREC;改写/约束输出=自建模板任务。决策走 amendment。

## 2. 数据隔离(全部 [FROZEN])

1. 同一 family_id 绝不跨 train/dev/test;
2. 同一底题的 paraphrase/candidate/insufficient/format 版本必须同 split;
3. 训练与评测 generator prompt 不同套(A/B,文本入 repo:`prescription/generators/A/`、`/B/`);
4. 训练与评测不共享固定措辞、标签映射、JSON schema(细则见 TRAIN_EVAL_SEPARATION.md);
5. 每条数据(训练+评测)必须带字段:`family_id, source_id, source_split, generator_id, generator_version, condition/component, template_id`;
6. build 完成后跑 8-gram 碰撞扫描(白名单=模板骨架词),报告入 qc/,碰撞清零后才可冻结。

## 3. 组件构造规范(4 特殊组件 + carrier;全部 [PROPOSED],Gate-1 原型审计后冻结)

通用规则:输出保留简短推理(≤120 target tokens 软上限,answerability 的拒答例外见下);全组件目标长度分布对齐 replay 桶分布(JS<0.1,见 DOSE_DEFINITION §4);组件内 8-gram 重复率 ≤5%;与评测 overlap = 0 family;自动验证 100% 通过 + 人工抽检(Gate-1:20/组件;扩产:50/组件)通过率 ≥95% 才冻结。

### 3.1 selective_revision
- 底题 + 候选答案(带一步理由)→ 判断并给终答;
- 比例:correct : wrong candidate = **50 : 50**,同底题成对(同 family 两条都在训练集);
- wrong candidate 生成:对 gold 解法程序化腐蚀,4 错误类型均匀:①末步算术 off-by-one/量级;②取错操作数;③单位/比例滑移;④漏一步中间量。禁止 LLM 自由编错(保可控可验);
- correct 侧 target 必须含显式判断短语(训练体裁 A:"候选正确,保留。"),wrong 侧含"候选有误,修正:"+ 正确推导;
- 自动验证:重算 gold;wrong candidate ≠ gold;target 终答 == gold。

### 3.2 evidence_robustness
- 3 子型均匀:①无关干扰句(同域实体+数字,与解无关);②错误中间断言("有人算出中间量=X",X 为腐蚀值);③冲突陈述(两句矛盾,一句为真);
- target:忽略/指出干扰,独立解题得 gold;②③型 target 须含一句显式否定错误信息;
- 自动验证:重算 gold;干扰值不出现在 target 终答。

### 3.3 answerability
- 比例:sufficient : insufficient = **50 : 50**,同底题成对;
- insufficient 构造:删除一个解题必需数值(程序确认删除后不可解:solver 依赖图检查);
- insufficient target = 定式拒答体裁 A:"缺少[量名],无法确定。"(不给猜测值);sufficient target = 正常解;
- 自动验证:sufficient 侧终答==gold;insufficient 侧 target 不含任何数值猜测。

### 3.4 format
- 训练 schema 集 A(k=4,冻结):`{"answer": int}`;`{"result": int, "unit": str}`;`{"final_answer": int, "confidence": "high|low"}`;`<answer>int</answer>` 标签式;
- 每条 = 底题 + schema 指令 → 合规输出;4 schema 均匀;
- 自动验证:parser 通过 + 字段齐 + 终答==gold。

### 3.5 carrier replay(placebo/被替换池)
- 源 = loop3 cleanreplay 世系多任务池;不足 2000 条时按其构造法扩产(同 generator、同任务配比),扩产部分标 `carrier_ext`;
- 冻结为 2000 条,分 5 长度桶(<50/50-100/100-200/200-400/≥400 target tokens),桶内移除序冻结。

## 4. Dose 数据池([FROZEN],同 DOSE_DEFINITION)

每组件 2000 条池,seed=20260804 洗牌一次,剂量=前缀嵌套 D_30⊂D_60⊂…⊂D_2000;替换按 token 记账同长度桶移除 carrier;每臂产 `data_manifest.json`(n_d/q_d/tokens/桶分布/池 hash)。

## 5. Gate-1 原型配额([FROZEN])

- 评测:每条件 **50** 题原型(reasoning 7 条件,同 50 个底题 family 贯穿)+ scorer 跑通;
- 训练:每组件 **200** 条原型 + 自动验证报告 + 人工抽检 20 条/组件记录;
- 交付形式:`prescription/gate1/` 下 jsonl + 审计 md,供确认后才扩产。
