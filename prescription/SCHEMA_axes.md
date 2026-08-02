# 五轴标注 Schema v1(C-18 P0a;冻结前挂 DRAFT,构念审计过后冻结)

> 每条评测项 = 五元组标签。旧二分(plain/repair genre)按此显式落位——
> 这张表本身回答"旧二分混杂了什么"。

## 轴定义

**Operation**(题目要求模型做什么):
- SOLVE 从零解题;VERIFY 判断给定解/断言对错;REVISE 修正给定的错解;
- PRESERVE 确认并保留给定的对解;ABSTAIN 识别不可答并拒答。

**Evidence**(上下文携带什么):
- CLEAN 无额外信息;IRRELEVANT 无关干扰;CONFLICTING 与正解冲突的断言;
- INCORRECT 错误的中间值/结论(可采纳型);INSUFFICIENT 信息不足以作答。

**Interface**(输出契约):FREE_TEXT / SHORT(只给答案)/ JSON / MC(选择题)/ TOOL。

**Source**(正解信息来自哪):PARAMETRIC(模型参数)/ IN_CONTEXT(题面自含)/
RETRIEVED_EVIDENCE(检索文档)/ MIXED。

**ScoringTarget**:FINAL_ANSWER / DECISION(keep-update-abstain 类)/
PROCESS(步骤/验证行为)/ END_TO_END_TEST(代码域)。

## 旧资产落位(P0a 重标的答案先写死做核对锚)

| 旧集 | Operation | Evidence | Interface | Source | Scoring |
|---|---|---|---|---|---|
| plain O 探针 | SOLVE | CLEAN | FREE_TEXT | IN_CONTEXT | FINAL_ANSWER |
| W1/W2 探针 | SOLVE | INCORRECT | FREE_TEXT | IN_CONTEXT | FINAL_ANSWER |
| F 探针 | SOLVE | CLEAN | JSON | IN_CONTEXT | FINAL_ANSWER |
| repair 腔 480 | VERIFY+REVISE/PRESERVE | INCORRECT/CLEAN | JSON | IN_CONTEXT | DECISION+FINAL |
| abstain 子集 | ABSTAIN | INSUFFICIENT | JSON | IN_CONTEXT | DECISION |
| 2Wiki W-桥 | SOLVE | CONFLICTING | FREE_TEXT | PARAMETRIC | FINAL_ANSWER |
| natural set | (逐条,五轴重标 P4) | | | | |

**旧 genre 二分的混杂显式化**:plain→repair 同时改变了 Operation(SOLVE→VERIFY/REVISE)、
Evidence(CLEAN→INCORRECT)、Interface(FREE_TEXT→JSON)、Scoring(FINAL→DECISION)
四个轴——P0c 的方差分解就是把旧结论摊到这四轴上。

## P0b 16 格 factorial(2×2×2×2,GSM 底题 matched variants)

- Evidence ∈ {CLEAN, INCORRECT};Operation ∈ {SOLVE, VERIFY};
- Interface ∈ {FREE_TEXT, JSON};Answerability ∈ {ANSWERABLE, INSUFFICIENT}。
同 family 内:数字/知识点/gold 不变;INSUFFICIENT 变体 = 删除一个必要数量
(validator:删除后方程不可解);逐格构念审计 100 条 ≥70%,撑不起 16 格的
底题整 family 弃,目标 ≥300 完整 family。
