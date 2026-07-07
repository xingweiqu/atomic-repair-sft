# CC_INSTRUCTION_C10 — Repair Transfer Matrix 主实验启动(2026-07-10)【逐字存档】

> 背景:Paper 2 叙事升级为 "From Atomic Diagnosis to Targeted Repair"(军令状五行见
> 组会文档 v2 第一节)。核心新实验 = Repair Transfer Matrix,三世界双向预注册。
> 本指令覆盖:入库、数据工程、训练队列、图任务。既有纪律(三闸门/脊点选点/预注册先行/
> 硬停)全部沿用。BIG_PICTURE 增补一节引用本指令(§3 主图更换为 Transfer Matrix)。

## 1. 入库(今天,零算力)
- paper/PAPER_CONTRACT.md:军令状五行 + non-claims 三条,逐字取自组会文档 v2 第一节,commit 冻结。
- prereg/PREREG_transfer_matrix.md:三世界判读规则冻结(TransferRatio 定义、<0.35 World A、
  >0.7 World B、K/R 高而 H 不对称 World C、0.35–0.7 灰区如实未决;Gain=脊点 ckpt corrupt repair
  score 相对该域 floor;Gain(i,i)<5pp 该行无定义标灰;RepairUtility=TargetGain−λ·(素题损伤+出血+无效),
  λ∈{0.5,1,2};硬停=负迁移<−10pp)。
- 措辞:一律 Repair Transfer Matrix,禁称 capacity-specific matrix;C-7 沿用。

## 2. 数据工程(本地并行,generate→gate→audit→sign-off)
2a K-Cor 干净真实域(Wikidata 1-hop 放量,Corrupt=植入错断言,type-match 闸门,实体不相交+
   逐题泄漏标记;construct=resist+recall,账本 A 列标"能力=事实召回非过程";train 1-2k/eval≥500;
   schema 与 R-Cor 完全一致)。
2b H-Cor=2Wiki(若未拍板,本项为唯一阻塞置顶提醒):桥注入器+Aug 探针孪生+泄漏说明;体量同 2a。
2c Natural corrupted-context set(100-200 条,四来源,标注 schema 含映射格+理由;
   双标注重叠 50 条算一致率;仅生态效度不入训练)。

## 3. 训练队列(等 2a/2b 闸门):六臂(K/R/H-Cor targeted + generic SFT + format-only +
   clean-replay),每 epoch 存 ckpt,脊点三闸选点,seed 42(对角+generic 加 43/44);
   评测列:三域 repair score+decision margin+三域素题+出血+无效+四科分解;
   R-Cor targeted 若与 E1b n300 配置一致可复用 ckpt(审计确认)。

## 4. 图任务:fig_transfer_matrix(数据回来后)+ 顾问三世界示意图入 figs/ 归档;
   fig_ledger K/M 拆色重制;Natural set 桑基图/表。

## 5. 汇报节律:每子件独立 notes;矩阵完成先出 NOTES_matrix_raw(纯数字+规则逐条判定),
   世界结论由 Xingwei/顾问裁决,CC 不宣布胜出。
