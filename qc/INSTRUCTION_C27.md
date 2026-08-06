# CC_INSTRUCTION_C27 — SFT Response Law figure pack(2026-08-06,逐字存档)

> 生成"SFT Response Law|当前结果、完整实验计划与连续执行状态"figure pack。
> 原则:1) 所有数值从冻结 JSON/CSV/Parquet 或 run manifest 读取,禁止手工填数;
> 2) 每图交付 PNG(≥1600px)+ PDF/SVG + 绘图脚本 + source_data + README(输入文件/commit/字段/复现命令);
> 3) 白底黑灰主色+单一强调色,无 3D/渐变/装饰;4) smoke/prototype/正式结果明确区分;
> 5) 缺失数据空白或 "pending",不得补数或推测。

八张图:
- **Fig 1** 整体故事与实验 DAG:General benchmark → Controlled perturbation diagnosis → Small-dose pilots → Multi-dimensional response law → Constrained multi-domain recipe;并画 CPU 数据建设/GPU 训练/GPU 评测/分析/mixture/held-out model 并行依赖。
- **Fig 2** Domain×Component 状态矩阵:行 Reasoning/Knowledge-Wiki/General IF;列 Clean replay/Format/Evidence/Revision/Answerability;状态 完成/建设中/待冻结;每格标训练源、主评测源、external holdout;GSM8K/SVAMP 只能标 Reasoning;Wiki/2Wiki/StrategyQA 单列 Knowledge。
- **Fig 3** Format 正式剂量响应主图:x=0..2000,第二横轴 q_d;四 panel:fmt contract_exact / fmt MAIN / original retention / wc_attempt joint;标 base、matched replay/placebo、3-seed 锚点误差条;注明 2,000-example carrier、packed、恒 30 updates、预算校验通过。
- **Fig 4** Format 响应向量热图:行=dose,列=endpoint,数值统一 component−matched replay;区分 target gain/无明显变化/collateral;不得混 vs-base 与 vs-replay 口径。
- **Fig 5** Format 高剂量 collateral 拆解:wc_attempt 的 contract_followed/decision_correct/final_answer_correct/joint/adoption 各剂量趋势+3-seed 范围;判定高剂量下降来自接口/判断/内容/seed 方差。
- **Fig 6** LODO 与哑基线:每个 held-out dose 的预测 vs 真实;law vs nearest-dose vs linear/log-linear vs constant;interp/extrap 分开;每法 MAE + 是否入噪声带。
- **Fig 7** Margin probe v2 模板审计:semantic template / opaque-label mapping / NL-分类-JSON genre 下的 margin;必须真标签语义置换;报多模板均值、模板间方差、margin-行为对齐;v1 的 T2/T3 bug 只作仪器故障说明不混入正式结果。
- **Fig 8** 完整执行状态与预计 run 数:Reasoning full-grid / Reasoning external eval / Knowledge cross-domain eval / IF cross-domain eval / Knowledge sparse training / IF sparse training / Mixture / Held-out model;标 completed/running/pending、实际完成与预计剩余 run 数、当前 GPU queue;SVAMP 不算第二个 domain。

另生成 SUMMARY_CURRENT_STATE.md:1) 冻结资产+hash/commit;2) 已完成结果;3) 在跑任务;4) Knowledge/IF 缺的 dataset decisions;5) 后续 run matrix;6) blocker 与 hard-stop;7) 各图源数据路径。

完成 figure pack 后继续原实验队列,不因画图停止训练;绘图与分析走 CPU,GPU 保持训练/评测队列运行。
