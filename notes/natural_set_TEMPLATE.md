# Natural corrupted-context set — 采集与标注模板(C-10 §2c)

体量 100–200 条;仅生态效度,不入训练。双标注:CC + Xingwei 各标,重叠 50 条算一致率。

## 每条记录 schema
| 字段 | 说明 |
|---|---|
| source_type | user_question(带错前提的真实用户问题)/ rag_passage(检索段落含错断言)/ agent_log(错读日志或报错)/ dialog_carryover(多轮前文错误结论污染) |
| raw_text | 原文(脱敏) |
| wrong_claim | 其中的错误断言(原文摘录) |
| gold | 正确答案/事实 |
| mapped_cell | K-Cor / R-Cor / H-Cor |
| mapping_reason | 一句话:为什么映射到这个格 |
| annotator | cc / xw |

## 采集来源候选(登记用)
- user_question:ShareGPT/WildChat 公开集里带错误前提的提问;论坛问答(StackExchange 含错假设的题)
- rag_passage:检索增强样例中含过时/错误断言的段落
- agent_log:公开 agent 轨迹集(SWE-bench 轨迹、AgentBench 日志)中的错读/报错
- dialog_carryover:多轮对话集中前轮错误结论被后轮引用的片段
