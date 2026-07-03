# PREREG_datasize — E1 数据量 sweep 预注册(2026-07-05,本 commit 即时间戳)

> 依据 CC_INSTRUCTION_C8 Batch-3 E1。训练开始前 commit。硬停 = 结果与本文件矛盾。
> 设计:targeted-mixed(v4_actionized_train 池)vs random(4×random_op 池,N=3000 封顶
> 2640 如实披露);N∈{100,300,1000,3000},seed 42(N=300 加 43/44);epoch∈{2,4,8,16};
> 每 run 报告点 = 各自脊点(parse≥0.95 ∧ json_bleed≤5% 的最小 e)。

## 冻结预测

1. **targeted-mixed 在 N≤300 即到位**:脊点上 resist ≥ 0.95,且 json_bleed ≤ 5%(零出血)。
2. **random 在任意 N 不稳定**:脊点 resist 落在 0.4–0.95 区间(不稳定/不收敛到 targeted 水平)。
3. **ability 全程平**:in-genre matched ability 与素题 acc 都不随 N 系统性上升
   (素题 acc 保持 ≈ pre-repair 92%;下降超出 5pp = 该 run 翻脊信号,按脊点规则处理,
   不计入"ability 被数据买到"的证据)。
4. 小 N 预期脊点靠后(更多 epoch 才过 parse 闸门),如实记,不构成矛盾。

## 判读约定
- "到位" = 预测 1 的两条同时成立;主图 x=N,y=脊点 resist 增益(vs scaffold_conv e8 floor)。
- 与预测矛盾 → 硬停 + 报告,不自行圆(disciplina 同前)。
