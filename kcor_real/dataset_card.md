# dataset_card — K-Cor 干净真实域(C-10 §2a;源偏差见 qc/DISCREPANCIES D-10)

| 字段 | 值 |
|---|---|
| **construct** | **resist+recall**(抵抗错误断言 + 从参数记忆恢复已存事实)——账本 A 列对本格标注"能力=事实召回,非过程",禁止与 R-Cor 的 A 跨格混比(C-10 原文) |
| 事实源 | LAMA/T-REx(Wikidata 1-hop,12 个高覆盖关系,问题模板逐关系手写) |
| 注入 | 同关系宾语池采样 type-matched 错值(构造性 type-match 闸门)+ claim 引入语 train/eval 措辞不交叠 |
| schema | 与 R-Cor(v4 actionized)逐字节同构:同 instruction 框架、同 input 框架、同 JSON 输出字段(prereg 排除格式混杂要求) |
| 切分 | **subject 实体不相交**(断言);(relation, subject) 唯一;eval 泄漏标记随生成写出(预期 0) |
| 体量 | train 1500 / eval 600(≥500 spec) |
| 反向干净闸门 | 本格希望 base **认识**这些事实(gold 恢复靠参数记忆)——`kcor_knownness_probe.json` 素题探针测 base 已知率,作 covariate 报告,不筛题 |
| regime | 评测 greedy 单次;脊点三闸选点 |
| 预注册 | prereg/PREREG_transfer_matrix.md(已冻结) |
