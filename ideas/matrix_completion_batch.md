# 矩阵补格批(封箱令下入 ideas/;待正式解冻方可执行;2026-07-20)

> 触发:Xingwei "那你全都做了吧"。按 data-freeze 规则(谁提都一样)先入册,
> 解冻需一句正式确认(建议连带顾问知会);解冻后 PREREG 先 commit 再上卡。

## 可填格(5 个,约半天卡)

| 格 | 做法 | 成本 |
|---|---|---|
| 5×Mistral-GSM steering | 自提方向(M1 W 标签)+ 扫描 + 资格判据 | 推理数小时 |
| 5×Qwen-2Wiki / SVAMP / StratQA steering | 冻结 d_plain@L12 打在各域 W 探针(杠杆域迁移测试,纯推理) | 各 <1h |
| 3×2Wiki drills | 补 g?_drl25 一臂(600 条 bare-answer drills,e2/e4)+ 双体裁 | 2 训 |

预测草案(解冻后冻结):杠杆域迁移 HIT(方向不依赖域)/ Mistral 提取存疑
(O_answered .606 低依从,同 32B instrument-limited 风险)/ 2Wiki drills 缺席
(知识域延续四连缺席)。

## 永久不可填(Scope 定死,解冻也不做)

- 32B 行 1-4:全参训练不可行、LoRA 破坏口径(C-16 明文);
- 2×SVAMP:format 病灶缺席(该模型-域对上无病可修,逻辑上不可测)。

## 建议(CC,不拍板)

矩阵灰格现已是 Scope 卖点("preregistered boundary, not unrun backlog"),
CZ 复审在途;补 5 格加固有限、延误确定。**建议不解冻**,除非 CZ 终审点名要。
