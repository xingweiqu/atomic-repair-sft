# dataset_card — <数据集名>(模板 v1,C-5.1 起 construct 字段为必填)

| 字段 | 值 |
|---|---|
| 数据集 | <名称 / 文件路径> |
| **construct(评测构念,C-5.1)** | `recall`(召回训练过的内容)/ `procedure`(过程/泛化)——**生成时声明,不许事后追认;K/M 记账以此为准** |
| 生成器 + commit | <script> @ <hash> |
| 体量 / 切分 | train N / eval-ID N / eval-OOD N;切分定义(如 操作数 train∈[0,99],OOD∈[100,999]) |
| 闸门结果 | 干净闸门(pre-repair zero-shot ≈0?)/ 泄漏(交集=∅ 断言)/ token 长度审计(p95 vs cutoff,R-9 裁决)/ 注入前后 gold 不变 |
| 双体裁孪生(R-7) | repair-mode 文件 + 素题孪生文件(同题、无植入、无 schema) |
| 推理 regime | 评测 = greedy 单次;pass@k 仅分桶变量,两 regime 不混(D-7(iii)) |
| 预注册 | 逐档位 A 预测(C-5.3)所在 commit hash |
