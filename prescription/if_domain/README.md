# prescription/if_domain — General IF 域数据池(canonical;2026-08-12,evidence 扩产 + IF eval 原型后)

> 本 README 是 if_domain 目录的**唯一身份文件**。每个文件的身份/规模/来源/批复状态/风险以此处为准。
> 全部构建确定性:C-31 四条线 seed **20260819**;evidence 正式池新行 seed **20260821**;IF eval 原型 seed **20260822**;旧 v2 proto seed 20260818;v0.1 proto seed 20260817。
> 构建顺序(池间隔离依赖 manifest 注册表,须按序重建):
> `build_if_answerability_pool.py` → `build_if_evidence_v2_1.py` → `build_if_format_pool.py` → `build_if_clean_replay_pool.py` → `build_if_evidence_pool.py` → `build_eval_if_proto.py`。

## 1. 现役池(训练侧 4 条线 + 评测原型)

| 文件 | 身份 | n | 来源 | 批复状态 |
|---|---|---|---|---|
| `if_answerability_pool.jsonl` | **正式池** component=answerability | 2000(1000 同段落 answerable/insufficient 配对 family;800 core 对 + 200 struct 对) | SQuAD-v2 train(CC BY-SA 4.0) | ✅ C-31 已批扩产(C-30 #4 构念) |
| `if_evidence_pool.jsonl` | **正式池** component=evidence_robustness(v2.1 全机制扩产) | 2000(500 suggestion 配对 family=1000 行;Note 三类 167/167/166;distractor 500) | SQuAD-v2 train | 🟠 C-31 line 2 扩产(v2.1 修复已落实,本次自证合规;待复核) |
| `if_format_pool.jsonl` | **正式池** component=format(F-A 路线) | 2000(SQuAD 抽取 1000:A1/A2 各 500;AG-News 分类 1000:A3/A4 各 500,label 各 250) | SQuAD-v2 train + AG-News train(fancyzhx/ag_news) | ✅ C-30 #1 批 F-A |
| `if_clean_replay_pool.jsonl` | **正式池** control=clean_replay(R-A 路线) | 2000(CREPE-normal 800 + SQuAD plain 700 + AG-News plain 500) | CREPE train(纯 normal 行)+ SQuAD-v2 + AG-News | ✅ C-30 #2 批 R-A |
| `eval_if_proto.jsonl` | **IF formal eval 原型**(eval-only,永不训练)generator=B | 950(6 任务形态 × 各 50 family × 适用条件;19 个形态×条件格,见 §1.5) | SQuAD-v2 **dev** + AG-News **test** + CREPE **test** | 🟠 C-30 #9 多任务形态覆盖;原型待复核 |

细节:

- **answerability**:v2 proto 240 行(seed 20260818)**逐字并入**(question id 不重复;仅补 `meta.origin` 与 insufficient 行的 `meta.subtype`)。所有 insufficient 行带 `meta.subtype ∈ {no_answer_in_passage(800), missing_field(200)}`,missing_field(结构化必填字段缺失型)占 insufficient 的 **20%**。拒答/NULL 目标为固定体裁(无答案泄漏,build 断言)。
- **evidence 正式池**(`if_evidence_pool.jsonl`,seed 20260821,builder=`build_if_evidence_pool.py`):沿 v2.1 **全部机制**(builder 直接 import v2.1 的模板/质检门/选段逻辑,不重写):①suggestion_correct/suggestion_wrong **成对同模板**(逐 family 断言两侧为同一模板实例、措辞零真伪线索);②三类中性 `Note:`(correct/irrelevant/conflicting),conflicting 过 v2.1 语言质检门(digit+首字母大小写实体匹配/可打印无 markup/长度差 ≤3 词),**不过检 family 弃用并入账**(本次弃 328:大小写 275、乱码 45、替换失败 8);③distractor_passage 行为不变。比例保持 v2.1 的 2:1:1。**v2.1 proto 240 行逐字并入**(同 answerability 并入模式,仅补 `meta.origin`);新行 context 与全部既有 IF 池(answerability/format/replay/两个 v2 proto/v2.1)零交集。上下文扫描弃件:41 无合格证据句、30 已被用作 donor。scorer 金标自评 2000/2000(build 内断言)。
- **evidence v2.1**(对 C-30 🟠 两点修复,替代 `if_evidence_v2_proto.jsonl`;**已逐字并入正式池**,保留原文件作对账):
  - ① wrong_span 改**成对**:同 family 两行 `suggestion_correct`(建议=gold,目标=确认并引证)/`suggestion_wrong`(建议=同段落 plausible 错 span,目标=驳斥并引证);两侧 prompt 模板逐字相同,措辞不带真伪线索(build 逐 family 断言)。60 family × 2 = 120 行。
  - ② conflict 改三类 note(`note_correct`/`note_irrelevant`/`note_conflicting` 各 20),去掉 "Unverified note" 固定标签 → 中性 `Note:`;三类共用同一 prompt 模板。conflicting 文本过语言质量检查(实体类型匹配 digit+首字母大小写 / 可打印无乱码无 markup / 与原句长度差 ≤3 词);**不过检 family 弃用**(本次弃 43:大小写型不匹配 39、乱码字符 4,记录在 manifest)。
  - ③ `distractor_passage` 60 行,行为与 v2 不变。
- **format**:训练 schema 集 A 四式轮转(A1 `{"answer": str}` / A2 `{"answer": str, "evidence_span": str}` / A3 `{"label": str}` / A4 `label: X` 行式);目标全部程序可验证(build 用与 scorer 同构的 validator 重解析断言)。评测须用 disjoint 的 schema 集 B;**IFEval = eval-only holdout,永久禁训**(C-30 #1)。
- **clean_replay**:plain 自然语言目标、无 schema、无组件表面(build 断言组件标记词不出现);CREPE comment 清洗后 ≤600 字符句边界截断(control 不要求可验证);5 长度桶分布入 manifest(<50:1477 / 50-100:440 / 100-200:83 / 其余 0)。

### 1.5 IF formal eval 原型(`eval_if_proto.jsonl`,C-30 #9)

- **形态×条件矩阵**(每格 50 行;条件适用性按形态语义,不机械全乘,理由入 manifest):

| 形态 | 来源(split) | original | format 契约 | candidate KEEP/REVISE | insufficient | STATUS 成对 | 行数 |
|---|---|---|---|---|---|---|---|
| extraction | SQuAD-v2 **dev** | 50 | 50(B2) | 50+50 | 50(dev unanswerable,同段落) | 50+50 | 350 |
| classification | AG-News **test** | 50 | 50(B4) | 50+50 | —(无 insufficient 侧) | — | 200 |
| reading QA | CREPE **test** normal / SQuAD **dev** unans | 50 | — | —(=revision 形态) | 50(按规格取 SQuAD-v2 dev unanswerable) | — | 100 |
| revision/correction | CREPE **test** fp(提供候选) | — | — | 50+50(候选=correction→KEEP / 候选=presupposition→REVISE) | — | — | 100 |
| constraint following | SQuAD-v2 **dev** | 3 约束变体:word_limit 50 / answer_prefix 50 / uppercase 50 | — | — | — | — | 150 |
| structured response | SQuAD **dev** 25(B1)+ AG-News **test** 25(B3) | — | 50 | — | — | — | 50 |

- **措辞 = generator-B**,与训练 A 措辞分离(硬断言两道:任何训练 A prompt 模板的 ≥4 词字面块不出现在任何 eval prompt;A/B 模板文本词级 6-gram 零共享);训练的 `Note:` / "Unverified note" 表面不出现。schema **B 系** = B1 `{"final_answer"}` / B2 `{"final_answer","support_quote"}` / B3 `{"category"}` / B4 `category = <label>` 行式(key 与措辞均与训练 A 系分离);STATUS/FINAL_ANSWER 行键保留(契约本体,scorer 依赖),包装措辞换 B 说法。candidate 契约 = `DECISION: KEEP|REVISE` + `FINAL:` 两行,keep/revise 两侧同模板(逐 family 断言仅候选值不同)。
- **隔离**:SQuAD 只用 dev split(训练全部 train;context hash 与全部训练注册表交集 0,断言);AG-News test(与训练 train hash 交集 0);CREPE test(与 replay/revision-proto train id 交集 0);naturalset(其 CREPE 行本身来自 test split)按 source_id + normalized text 双重排除;eval 内部 family 跨形态零复用。全部 registry 入 `eval_if_proto_manifest.json`,并已登记进池注册机制(未来任何训练池构建自动排除)。
- **判定**:全部行为级,`if_scorer.py`(为 eval 就地扩:schema B 系 / candidate_contract / reading_qa attempt-refusal / constraint 三变体 / classification / SQuAD dev 多参考 gold_aliases;selftest 60/60);950 条参考 target 自评 950/950(build 内断言 + CLI batch 复核)。
- **抽读**:`AUDIT_SAMPLES_IF.md` 每形态×条件随机 3 条(19 格 × 3 = 57 条,全文)。

## 2. 隔离与校验(每池 build 内置硬断言,全部通过)

- **池间零 context 交集**:训练侧各池 + `if_revision_proto` 两两在 {SQuAD context_hash(含 distractor/irrelevant-note donor)、AG-News 文本 hash、CREPE family} 三个键上交集为 0(独立复核脚本亦过)。例外按设计:`if_evidence_pool` ⊇ `if_evidence_v2.1_proto`(逐字并入,registry 为其超集,build 断言恰等于并入部分);eval 原型与全部训练注册表交集 0(split 级 + hash 级双保险)。
- **target 无泄漏**:拒答/NULL 固定体裁;wrong span ≠ gold 且无互相子串;distractor 段落不含 gold;conflicting note 替换成功且不含 gold;evidence 链(gold∈ev∈ctx∈target)逐行断言。
- **8-gram 骨架外重复**(family 级):四池全部 0.0。
- **配对完整性**:answerability 每 family 恰 2 行(一答一拒);evidence suggestion 对 60/60 完整。
- **naturalset 隔离**:normalized text + source_id 双重断言。
- **manifest**:每池 `*_manifest.json` 含 sha256、id registry(SQuAD context/question id/title、AG-News 行号+文本 hash、CREPE id)、长度桶、subtype 计数——**未来任何 IF 评测构造必须排除这些 registry**(eval_if_proto 已按此构造);SQuAD dev split 只用于 eval,训练侧保持未动。
- **scorer 回归**:训练池 gold target 自评 —— answerability 2000/2000、evidence v2.1 240/240、evidence 正式池 2000/2000、format 2000/2000、replay 1200/1200(800 ELI5 control 不计分);eval 参考 target 950/950,0 fail。

## 3. 评分器

`if_scorer.py` — 行为级(非 target 字面比对):answerable 抽取匹配(SQuAD 式 norm:小写去冠词去标点,短回答允许包含)/insufficient 拒答标记 + NULL 判定/struct 行 STATUS+FINAL_ANSWER/evidence = 答案正确 **且** 引证证据句(≥8 token 连续片段)、suggestion_wrong 另须终答段不承接错误建议、distractor 另须点名正确段落/format 四 schema 严格校验(首个 JSON 块抽取、key 集精确、label 精确;A4 行式)/replay 分类关键词判定。
Eval 扩展(2026-08-12,就地补):gold_aliases 多参考(SQuAD dev)/schema **B1–B4**(key 集与 A 系互斥,A 键在 B 行判错、反之亦然)/candidate_contract(DECISION 行 + FINAL 行,meta.final_kind ∈ gold|label|free)/reading_qa(attempt vs refusal)/constraint(word_limit / answer_prefix / uppercase)/classification(cls_plain 关键词)。
**selftest 60/60 通过**(`python3 if_scorer.py`;正负例覆盖全部分支含全部 eval 扩展);批量:`python3 if_scorer.py POOL.jsonl RESP.jsonl`。

## 4. 归档/辅助文件(非现役)

| 文件 | 身份 |
|---|---|
| `if_evidence_v2_proto.jsonl` | **已被 v2.1 替代**(seed 20260818 归档;其 context 允许被 v2.1 复用,不参与池间交集检查) |
| `if_answerability_v2_proto.jsonl` | 已**并入**正式池(保留原文件作对账);其 240 id 在正式池恰出现一次 |
| `if_evidence_v2.1_proto.jsonl` | 已**并入** `if_evidence_pool.jsonl`(保留原文件作对账);其 240 行在正式池恰出现一次(§1 表中同时列出以示待复核身份) |
| `if_revision_proto.jsonl` | [PROPOSED] CREPE 扩产暂停(C-30 #6:50-family passage-support 人审未做) |
| `premise_validity_aux_proto.jsonl` / `suggestion_pressure_aux_proto.jsonl` | 辅助 probe,**永久定格不升格**(C-31) |
| `build_if_proto.py` / `build_if_v2.py` | 旧 proto builder(v2.1/正式池 builder 通过 import 复用其索引与 span 工具,保证兼容) |
| `if_build_lib.py` | 共享库(AG-News/CREPE 加载、长度桶、跨池 registry 排除、manifest/sample 写出);POOL_FILES 注册表现含 6 项(四池 + evidence 正式池 + eval 原型),后建者自动排除先建者 registry |
| `if_proto_manifest.json` / `if_v2_manifest.json` | 旧 proto manifest(registry 仍然有效,新池构建时全部排除) |
| `IF_SOURCES_PROPOSAL.md` | C-28 提案存档(C-30/C-31 裁决已覆盖其待决项) |

## 5. 风险清单(冻结前须知)

1. **AG-News 许可**:HF fancyzhx/ag_news 无正式 LICENSE 文件(学界通用研究使用);冻结前回查。文本含来源性 HTML 实体残渣,已清洗(`#39; #38; quot;` 等),全池残留 0。
2. **CREPE 许可**:镜像无显式 LICENSE(Yu et al. 2023 公开研究发布);replay 用 normal 行,风险同 revision 线,冻结前回查原 repo。
3. **证据句截断**:evidence/format 的 evidence_span 取含 gold 的句子,句切分在缩写(p.m. / D.C. 等)处会截断,个别引证句不完整(不破坏 gold∈ev∈ctx 断言,但引证观感受损);扩产前可换 abbreviation-aware 切分。
4. **conflicting note 残余语病**:质量门挡 digit/大小写/乱码/长度,不挡**性别/单复数一致**(抽读见 1 例 "Christopher Hitchens … as she put it");扩产前如需更严可加代词一致检查。
5. **SQuAD 预训练暴露**:作为训练载体可接受(测 schema/行为服从非知识),IF 评测不得落在本 registry 内的 family(§2)。
6. **答案可评性**:replay SQuAD 侧已过滤无 ASCII 字母数字的退化 span(如 `⟨е⟩`);answerable 侧 gold 偶见推导型数字(如 "6" 源自 26 June 的 SQuAD 官方标注),token 级 norm 匹配不受影响。
7. **evidence 正式池 8-gram 残留 1 对**(family 级 dup rate 0.0007=1/1500):`squadv2_ctx_22f5efa83378` 与 `squadv2_ctx_1054740d5f3b` 的证据句为语料级近重复(足球俱乐部奖杯清单两段),非模板重复;如需绝对 0 可加语料 8-gram 互斥筛。
8. **eval reading_qa original 的判定是 attempt 级**(非内容匹配):CREPE 自由问答无程序可验证 gold,original 侧只判"真作答"(无拒答标记且 ≥10 词),insufficient 侧判拒答——两侧成对构成选择性拒答行为;CREPE passage 对 comment 的支持率问题(C-30 #6)因此不承重,但**不可**据此格声称内容正确性。个别 CREPE comment 携带 "Edited for content." 一类论坛残留(参考 target 噪声,不影响判定)。
9. **eval SQuAD dev 多参考答案**:抽取匹配接受 `meta.gold_aliases` 任一(dev 官方多标注);B2 support_quote / word_limit 参考仍以首标注为准。
10. **AG-News test parquet** 本次经 huggingface_hub 下载(7.6k 行),许可风险同 §5.1;evidence 干扰(distractor/note)形态未进本 eval(不在 C-30 #9 六形态内),将来单建时须按 C-31 用不泄露"恰一段相关"的 B 模板。

## 6. 复现

```bash
cd prescription/if_domain
python3 build_if_answerability_pool.py   # 2000, merges v2 proto ids
python3 build_if_evidence_v2_1.py        # 240 proto v2.1
python3 build_if_format_pool.py          # 2000
python3 build_if_clean_replay_pool.py    # 2000
python3 build_if_evidence_pool.py        # 2000, merges v2.1 proto rows (seed 20260821)
python3 build_eval_if_proto.py           # 950 eval proto (seed 20260822)
python3 if_scorer.py                     # selftest 60/60
```

前置:HF cache 有 `rajpurkar/squad_v2` train+validation parquet、`fancyzhx/ag_news` train+test parquet、`tasksource/CREPE` snapshots(train/dev/test jsonl;AG-News 两个 parquet 均经 huggingface_hub 下载)。
每训练池另出 `sample10_*.md` 随机抽样(subtype 全覆盖);eval 抽读见 `AUDIT_SAMPLES_IF.md`。
