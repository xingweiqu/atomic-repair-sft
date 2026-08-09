# CC_INSTRUCTION_C30 — IF/K 审核包裁决:部分批准,构念漂移纠正(2026-08-10,要点存档)

核心原则:**先定义行为构念 → 再找/造匹配数据**;禁止"找到 FalseQA 就把 false premise 叫 Answerability / 找到 sycophancy 就把 user suggestion 叫 Evidence"。Format 是最干净模板:跨域保持组件语义不变,只换任务内容。

## 十点裁决(逐字执行)
1. ✅ if_format 批 F-A(SQuAD v2+AG-News 载体;train schema A/eval schema B;IFEval eval-only);
2. ✅ if_clean_replay 批 R-A(CREPE-normal+SQuAD plain+AG-News plain);
3. ✅ TruthfulQA 永久禁训;
4. 🔴 FalseQA 不得作核心 if_answerability(false-premise≠information sufficiency);降级 secondary premise-validity stress;**核心 IF Answerability = SQuAD-v2 answerable/unanswerable + 必填字段缺失型结构化任务**(answerable 侧 FalseQA 答案质量已见问题);
5. 🟠 sycophancy 不得作核心 if_evidence(测的是 suggestion-pressure,无 evidence);保留为辅助 cross-task probe;**核心 IF Evidence 必须真含 evidence**(阅读理解 + plausible wrong span / topic-related distractor passage / conflicting statement,正确证据仍在);
6. 🔴 CREPE revision 暂停扩产:先随机 50 family 人工标 passage 支持率(A 明确支持/B 相关不可推/C 无关),A率≥80% 才准 grounded;否则去 passages 改 question+candidate selective revision 或换源(样本已见 3 例"passages 不支持却标 KEEP");
7. 🟠 K eval v1 = prototype 身份;正式版必修:distractor donor 与 main-eval **永久 disjoint 池**(当前 50/50 donor 出自同池,30 unique,破坏 family 独立性);random 无关 donor 改 same-entity/same-relation/plausible-conflict **hard distractor**(现版 10 篇无关→11 篇无关,压力过弱,可解释 K-distractor 对 evidence 无响应);
8. K wc_attempt 现状=answer+citation,非 full attempt:改名 wrong_candidate+citation,或补真两跳推理链(否则跨域 construct mismatch);
9. 重交完整 audit pack:三个 200 条 proto JSONL、builder、manifest、scorer、以及 README 声称却不存在的 K training spec(须先写出);
10. 修正前不启动 IF 正式剂量训练。
