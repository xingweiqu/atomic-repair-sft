# CC_INSTRUCTION_C26 — 多域数据落地令(2026-08-06,逐字存档)

> 核心:**不能最后所有正式训练数据都来自 GSM8K。** 当前完成的只是 Reasoning×Format 的发现域曲线,
> 不得称为完整通用 SFT response law。所有实验按 Domain × Component 二维组织;
> recipe 变量 = n_{k,d}(k∈{Reasoning, Knowledge, General IF},d∈{Clean replay, Format, Evidence, Revision, Answerability})。

## 一、先盘清所有已有数据资产 → ALL_DATA_ASSET_INVENTORY.csv

字段:dataset_name / exact_path / version_hash / domain / task_type / available_splits / usable_family_count / current_builder / current_scorer / license_status / possible_role / known_quality_risks。
必须纳入:Reasoning(GSM8K、SVAMP、gsm_repair_v4、loop3/gate1/P2a 资产——旧数据只作 archive 分析不自动混入新训练);Knowledge(wiki2/2Wiki、StrategyQA、repo 其他 Wiki/知识 QA/grounded QA);General IF(naturalset/、抽取、分类、改写、阅读理解、constraint-following、schema 数据;naturalset 不完整须列缺失项,不能用"IF 待建"长期搁置)。

## 二、每个数据集分配明确角色 → DATA_ROLE_MATRIX.csv

角色 ∈ {component training source, clean replay source, in-domain evaluation, cross-dataset holdout, cross-domain evaluation, calibration only, archive analysis only}。示例分工:GSM8K-train=组件训练+replay;GSM8K-test=主评测;SVAMP=Reasoning 外部持出;2Wiki=训练+主评测隔离 split;StrategyQA=Knowledge 外部持出;IF 数据=训练/主评测+持出。所有 family/文档/实体/模板按角色隔离。正式角色按规模、可验证性、泄漏检查冻结,不得由 CC 临时选择。

## 三、Knowledge 不只进评测,也进训练

建 knowledge_{clean_replay,format,evidence,revision,answerability}_2000 五池;**不允许用 GSM8K 生成所谓 Knowledge 组件**。Knowledge Format=知识/给定材料 QA 上的 JSON/固定字段/citation 字段/短结构化答案;Evidence=错误候选事实/冲突证据/无关 Wiki 段落/相似实体或时间混淆/错误 supporting passage;Revision=正确知识回答保留、错误回答或依据修正;Answerability=文档特定事实/虚构或局部实体/grounded-only 指令/删除必要 supporting evidence 后确实不可推出(防参数知识使标签不成立)。

## 四、General IF 建真实组件池

覆盖 extraction/classification/rewriting/reading comprehension/constraint following/structured response;先建 condition applicability matrix(逐任务,不机械全条件);再建 if_{clean_replay,format,evidence,revision,answerability}。

## 五、一域密集、两域稀疏

Reasoning 继续 discovery(全 8 点网格全组件);Knowledge/IF 每组件只跑 {0, n_onset, n_high}(onset 按冻结算法从 Reasoning 曲线选出)。两域必须有**真实训练数据**,不只拿 Reasoning ckpt 评测。每组件两类跨域证据:零训练迁移(Reasoning ckpt→K/IF 评测)+ 域内缩微训练(K/IF 组件→K/IF 评测)。

## 六、最终 mixture 含三域

recipe = 3×5 矩阵 n_{k,d} 整体优化(15 变量第一版可约束:行为组件用跨域平衡 bundle 或按单域 pilot 定 domain ratio;clean replay 也三域共同组成)。禁止最终 mixture 只有 GSM8K。

## 七、GPU 连续运行顺序更新

1. Reasoning Evidence full grid;2. Reasoning Revision full grid;3. Reasoning Answerability full grid;4. Knowledge/2Wiki evaluation+base profile;5. General IF evaluation+base profile;6. 所有 Reasoning ckpt 补跑 K/IF 零训练评测;7. Knowledge 各组件 placebo/onset/high;8. IF 各组件 placebo/onset/high;9. 三域统一拟合;10. multi-domain mixture;11. held-out model multi-domain recipe。CPU builder 与 GPU 并行:GPU 跑 Reasoning 时 CPU 建 Wiki/IF;Wiki eval 完成即给已有 ckpt 排跨域评测;不等全组件结束才开多域。

## 八、禁止

用剩余 2,817 GSM families 生成**三域**全部组件;把 SVAMP 称为第二个 domain;只在 Wiki/IF 评测不建训练组件;最终 mixture 只有 GSM8K;Wiki 原文无控制混入 SFT;为"全都加"破坏 train/eval 隔离;未盘点数据被静默忽略。

## 总要求(原文)

> "所有数据都加进来"是指所有计划中的任务域都必须进入正式训练、评测和最终 recipe,而不是把所有文件无差别拼接。Reasoning 使用 GSM8K/SVAMP;Knowledge 必须落地 Wiki/2Wiki、StrategyQA 等现有资产;General IF 必须完成 naturalset/现有 IF 数据盘点。任何在 repo 中与这三域相关的数据必须进入资产清单,并被明确分配为训练、评测、持出或 archive 角色,不得静默遗漏。
