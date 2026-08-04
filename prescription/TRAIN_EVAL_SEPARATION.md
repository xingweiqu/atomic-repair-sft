# TRAIN_EVAL_SEPARATION — 训练/评测生成器隔离冻结文件(lawv1;2026-08-04 draft → 章程 commit 时冻结)

> 回应 REVIEW_lawv1_v1 第二条:防止"模型学会的是生成器体裁"。模板审计管读出层,
> 本文件管 train–eval generator overlap。

## 1. 四重隔离总表

| 层面 | 训练侧 | 评测侧 | 执行手段 |
|---|---|---|---|
| 底题 families | GSM8K-train 派生 families(+合成世界) | GSM8K-test 未见 families + SVAMP(全持出);2Wiki/StratQA 评测 split | family-ID 全局登记表,build 时硬去重;冻结前跑 8-gram 碰撞扫描 |
| 数据源 | 训练源清单 A(冻结) | held-out benchmark/source 清单 B(冻结) | 两清单不相交,入 manifest |
| 生成 prompt | generator A(现有 builder 措辞) | generator B(独立重写的 prompt 措辞;可行时换生成模型) | 两套 prompt 文本入 repo,diff 可查 |
| 表达模板 | schema/标签/措辞集 A | 集 B + 同模板对照子集 | 见 §2–3 |

## 2. Format 组件专项

- 训练:k=4 个简单 JSON schema(字段名集 A、扁平结构、固定顺序);
- 评测主指标:**未见 schema**(新字段名、嵌套、乱序、新标签词);
- 评测对照:**同 schema in-template** 子集单独报——两者差值 = "记住合约 vs 泛化 format control" 的直接读数;
- JSON validity 判定用程序 parser,与生成器无共享文本。

## 3. Selective revision 评测标签变体(全部报,主指标取多变体均值)

1. KEEP / CORRECT(与训练同风格,作 in-template 对照);
2. ACCEPT / REVISE;
3. opaque 标签 A/B/C × 2 组置换映射;
4. 自然语言审核句(无标签词,由 scorer 判类)。

## 4. 逐条件隔离要点

- Paraphrase:评测改写由 generator B 产出+答案不变性校验;训练侧(如用)另用 generator A;
- Distractor:评测干扰体裁 ≠ 训练 evidence 组件的干扰体裁(不同插入位置/文风/来源句式);
- Candidate 对:评测候选来源 = base model 真实错答(自然错误),训练候选 = builder 合成错误;两者体裁天然分离,保持;
- Insufficient:评测删条件的措辞/位置模式与 d6 训练模板不同套;
- S/R 探针:assist 文本由 generator B 写,不复用训练 CoT 模板句式。

## 5. 冻结前审计

- 训练池 × 评测池 8-gram 字符串碰撞扫描,碰撞率报告并清零(模板骨架词除外,白名单入库);
- 每条件抽 20 例人检 train/eval 体裁可区分性,记录入 qc/;
- 以上全部通过后评测套件 hash 冻结(预注册节点3)。
