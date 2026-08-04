# PLAN_lawv1 — 收敛版故事的可执行实验计划(v2.1,2026-08-04)

> **v2.1(C-21)**:执行细则下沉到五份 contract(prescription/contracts/:DATA / TRAIN /
> EVAL / ANALYSIS / RUNBATCH),写到 CC 零研究判断可执行;正式训练前置三道 Gate
> (原型→smoke→冻结),**禁止从 PLAN 直接跳到 Stage A 网格**。指令存档 qc/INSTRUCTION_C21.md。

> v1 → v2:吸收顾问审阅 qc/REVIEW_lawv1_v1.md 全部十条。蓝图原文:qc/BLUEPRINT_convergent_v1.md。
> v2 变更摘要:①剂量改双定义(token 份额主轴)+嵌套替换恒 token 预算;②train–eval 四重生成器隔离;
> ③七条件笛卡尔积改 applicability matrix;④评测规模升方案A;⑤seed 锚点先固定后自适应;
> ⑥Phase-1 从生死门降为软闸门(law kill 移到 prospective Stage A);⑦scope 定名 post-instruction
> adaptation;⑧目标函数字典序冻结;⑨mixture 判别性选臂;⑩新模型迁移假设预注册+核心臂 3 seeds。
> 铁律照旧:数字只认数据文件;预测冻结先于训练;单 seed 臂标注;缺失申报不重构。

---

## 0. 一页总览

```
M0 零算力(今天可做)   章程 prereg(含 4 冻结文件)+ Phase-1 归档全量 LODO(软闸门)
M1 CPU 建设(今天可做) 评测套件 v1(applicability matrix 制导)+ 模板审计架 + 组件 builder(嵌套剂量)
M2 GPU Stage A         Reasoning 发现域全网格          ~47–55 train
M3 GPU Stage B         先零训练跨域评测,再条件化补训   ~12–18 train
M4 零算力              跨域迁移判定(并入 M3 第一步)     0 train
M5 GPU Phase 4         mixture 判别性开牌               ~10–16 train
M6 GPU Phase 5         新模型决战(核心臂 3 seeds)       ~18–22 train
(可选)base-model 缩微  1 组件×3 剂量×1 base model        3 train
                                            合计 ≈ 90–114 train run
```

参照:P2a 段1 = 12 train + 12 factorial eval ≈ 单台 8 卡机一个工作日(含事故)。
GPU 总量 ≈ 9–13 台·日。评测量升级后推理成本上升,但评测走 vllm 吞吐,不是瓶颈。

**Scope 定名(写进论文)**:研究对象是 **SFT recipe selection for post-instruction
adaptation**(Qwen3-8B 与 Llama-3.1-8B-Instruct 均为 instruct 模型上的二次 SFT),
不泛化声称"一般 SFT scaling law";可选 base-model 缩微仅判形态异同,不复制管线。

---

## 1. 资产映射表(v1 不变,节录)

七条件里 5 条复用现有机器(16-cell 因子/修复腔/abstain/interface),Paraphrase/Distractor
挪接新题源;5 组件 ≈ P2a d_components(evidence = d2_verify+d5_provenance 合并);
真正新建件 = IF 域评测 + 模板审计架。fit_pilot/p2a_h1/run_p2a.sh/bringup.sh 全复用。
**v2 新增约束**:复用件全部过 TRAIN_EVAL_SEPARATION.md 的四重隔离改造后才能上岗。

---

## 2. M0 — 零算力,立即可做

### 2.1 实验章程 EXP_CHARTER_lawv1.md(prereg commit)

内容 = 四条停止规则(准入/seed/跨域/连续指标,v1 原文)+ **四个冻结文件**:

1. `DOSE_DEFINITION.md` — 双剂量定义(q_d token 份额主轴 + n_d 条数)、恒 token 预算、
   同长度桶替换、嵌套前缀剂量(D_30⊂D_60⊂…)、单一 carrier pool、dose_manifest.json;
2. `TRAIN_EVAL_SEPARATION.md` — 底题/数据源/生成 prompt/表达模板四重隔离,
   format 未见-schema 主指标 + 同-schema 对照,selective revision 四标签变体,8-gram 碰撞扫描;
3. `APPLICABILITY_MATRIX.csv` — 8 个 task type × 7 条件的合法性表(yes/adapted/no+理由),
   knowledge 的 insufficient 用 grounded-only+虚构实体+程序确认;
4. `UTILITY_AND_BASELINES.md` — 字典序目标(硬约束 ε_o/ε_r/ρ 数值定稿)、
   组件→endpoint 映射、六个判别性 mixture 臂公式、新模型迁移假设与 seed 配置。

**Amendment 协议**:章程 commit 后,C-18 v1.2 等任何修订不得覆盖已注册内容;
须在查看对应新结果前提交 amendment commit,旧版结果保留,
所有产出标注 preregistered / amended / exploratory 三态。

### 2.2 Phase 1 = fit_pilot v2(归档全量 LODO;定位:**软闸门**)

扩展项(v1 原文):全量 LODO、interp/extrap 分列、nearest/linear/constant 哑基线、
形态库+rise-fall(申报:<5 有效剂量点时 rise-fall 无可靠识别力,只作探索性)、
P2a 段2 数据一到即并入(标注设计类型:纯组件剂量,非替换式)。

**v2 判据(替换 v1 硬停条款)**——Phase 1 决定的是"值不值得进 prospective pilot",
不裁决 law 生死:
- 赢过哑基线 → 直接进完整 Stage A;
- 结果混合 → 每组件先跑 {0, 60, 480, 2000} 四点 pilot,再决定全网格;
- 明显失败 → 仅 format 及有 archive 强信号的组件进四点 pilot;
- **law 的真正 kill criterion 放在 prospective Stage A**(见 §11)。

---

## 3. M1 — CPU 建设(与 M0 并行)

### 3.1 评测套件 lawv1_eval(方案A 规模;冻结后 hash 入 commit)

**同一底题 family × 适用条件配对生成**(按 APPLICABILITY_MATRIX,不强制笛卡尔积):

| 域 | 题源 | 底题 families(v2 升级) | 条件版本 |
|---|---|---|---|
| Reasoning(发现域) | GSM8K(gsm_repair_v4)+ SVAMP 持出面 | **600–1000** | 全 7 条件 |
| Knowledge(确认域) | 2Wiki + StratQA | **400–500** | 6 yes + insufficient=adapted |
| IF(确认域) | 新建:抽取/分类/改写/约束输出 | **400–500** | 按矩阵逐行 |

- CI 一律 item-family bootstrap;3pp 级差异不写成稳定组件效应(章程写死);
- **S/R 二层**:失败集合 = **base model 在冻结主评测上的失败题集,一次冻结全程共用**
  (所有 ckpt 用同一分母,AssistanceRecovery 才可比);assist 文本 generator B 产出;
- **压力层改名 Compound perturbation stress test**(合成受控组合,非自然 deployment;
  每域 100–200 题,不进 law);
- Retention 套卷:三域 Original 合并 + 训练域外基准(硬约束用)。

### 3.2 连续层 + 模板审计架(v1 原文不变)

3 语义模板 × 2 标签置换 × 体裁挪移 ≈ 8 变体;报 M̄ 与 Var_k;三级准入表;
审计 D(margin↔行为对齐)在 base + 2 归档 ckpt 上先行体检。

### 3.3 组件 builder(按 DOSE_DEFINITION 重造)

- 每组件 2000 条池,冻结种子洗牌,剂量=前缀(嵌套);
- 恒总 target tokens,同长度桶替换 replay;各组件池长度分布与 replay 桶分布对齐
  (JS<0.1 软约束,做不到如实申报);
- selective revision 补齐 keep 配对;evidence = d2+d5 合并;
- 产出 dose_manifest.json(每臂 n_d/q_d/tokens/steps)入冻结 commit。

---

## 4. M2 — Stage A:Reasoning 发现域全网格(GPU)

训练协议(v1 不变):Qwen3-8B,full FT + ds z3,固定 lr/schedule,2 epochs,
末位 ckpt,本地盘→HDFS。**剂量按 DOSE_DEFINITION 执行,主轴 q_d。**

| 项 | run 数 |
|---|---|
| 4 特殊组件 × 剂量 {30,60,120,240,480,960,2000}(单 seed) | 28 |
| placebo(dose-0 纯 replay) | 1 |
| **固定 seed 锚点**(开跑前写死,与首 seed 结果无关):每组件 n∈{240,2000} 各 +2 seeds | 16 |
| placebo +2 seeds | 2 |
| 自适应加密:每组件 ≤1 点 ×2 seeds,标注 **adaptive refinement**(不作原始形态独立确认) | ≤8 |
| **合计** | **47–55** |

评测每 ckpt:reasoning 全 7 条件 + retention + 通过审计的连续层探针;
S/R 只在冻结的 base 失败集上跑。

**预注册(节点4)**:开跑前冻结每组件×每 endpoint 的方向/形态预测(fit_pilot v2 + P2a 依据)。
**law kill criterion(真正的,prospective)**:Stage A 全量 LODO 中位盲误差不优于
nearest-dose,且固定锚点 3-seed 带内无稳定方向 → law 线硬停,
论文降级"画像+组件方向效应"(P0c/P1/P2a 证据链仍立)。

---

## 5. M3 — Stage B:先零训练迁移评测,再条件化补训

**第一步(0 train,即原 M4 提前)**:全部 Stage A ckpt 直接过 knowledge/IF 评测套件
→ 得到完整跨域迁移表("reasoning 训的行为是否跨域"就此回答)。

**第二步(条件化训练,准入规则章程写死)**——组件满足以下**任一**才在确认域训练:
1. reasoning 响应稳定但跨域不迁移(判"domain-specific 还是通用"需域内对照);
2. 跨域方向一致但幅度需校准(recipe 要用跨域幅度);
3. 是最终 recipe 的关键组件(r* 中 q_d 非零)。

剂量选择算法(预先写死):onset = 预测效应首超噪声阈值的最小剂量;high = 最大预注册剂量;
无 onset → {0, mid, high} null check。规模:**~12–18 run**(上限 26 保留为硬顶)。

---

## 6. M5 — mixture 判别性开牌(GPU,~10–16 run)

六臂按 UTILITY_AND_BASELINES.md §3 公式机械解出(clean replay / uniform /
constrained r* / unconstrained optimum / max-negative-interaction pair / max-disagreement),
同成本(特殊份额对齐 Q*);r* 与 uniform 各 +1 seed。
**训练前**冻结全 endpoint 加性预测(节点5)。开牌:误差<噪声 → optimizer 放行;
误差大 → **targeted interaction correction**(只校准一个最重要组件对,≤6 run,
不声称完整 pairwise model)。

## 7. M6 — 新模型决战(GPU,~18–22 run)

held-out 模型:Llama-3.1-8B-Instruct(章程定稿)。
1. 画像(0 train)→ 2. 每组件 2 剂量 pilot(4×2=8)→ 3. 按预注册迁移假设
   G_new(n)=a·G_source(b·n) 重标定 → **触发规则**:两点与 source 形状残差>噪声
   → 加第三 calibration dose(≤4)而非强行出 recipe → 4. recipe 预测冻结(节点6)→
5. 训练:predicted recipe ×3 seeds、uniform ×3、clean replay ×3、
   人工比例 ×1、fix-worst ×1(单 seed 臂标注)= 11 → 6. 全指标验收(蓝图十五之4 清单)。
合计 8 + (0–4) + 11 ≈ **19–23 run**。

**(可选)base-model 缩微**:1 组件(format)× 3 剂量 × 1 个 base model,
只判形态是否与 instruct 模型定性不同,exploratory 标注,3 run。

---

## 8. 与在跑事项的关系(v1 不变)

P2a 段2 照旧(机器活了先跑):= "60 条 pilot 预测 600/2000 排序"的 H1 检验、
主张3 第一块证据;36 ckpt 并入 Phase-1(标注纯组件设计)。
C-18 v1.2 到达 → 走 §2.1 amendment 协议,不覆盖已注册内容。

## 8b. Gate 执行顺序(v2.1;细则在 CONTRACT_RUNBATCH §5)

Gate 1:数据源确认 + 7×50 评测原型 + 4×200 训练原型 + scorer 单测 + 审计报告
(+GPU 后补:base profile、模板审计初测)→ **用户确认后才扩产**;
Gate 2:3 个 smoke train 全链路(placebo / evid-60 / evid-2000),核 loss mask、
token 账、渲染一致、12 文件、实测成本;
Gate 3:全 hash + RUN_MATRIX.csv + GPU-hour 实测重估 → 预注册 commit → 才开 Stage A。

## 9. 预注册节点清单(每个 = 一次 commit,先于对应训练)

1. EXP_CHARTER_lawv1 + 四冻结文件(DOSE_DEFINITION / TRAIN_EVAL_SEPARATION /
   APPLICABILITY_MATRIX / UTILITY_AND_BASELINES,ε_o/ε_r/ρ 数值定稿) — M0;
2. fit_pilot v2 脚本 — M0,先 commit 后运行;
3. 评测套件 hash + 生成器版本 + 隔离审计报告 + base 失败集冻结 — M1 末;
4. Stage A 方向/形态预测 + seed 锚点 + dose_manifest — M2 开跑前;
5. mixture 六臂配比 + 全 endpoint 加性预测 — M5 开跑前;
6. 新模型迁移标定 + recipe 预测 — M6 全训前。

## 10. 死活判据(v2 修订)

- ~~Phase-1 输基线→硬停~~ → Phase-1 只做软闸门分流(§2.2);
- **law kill(prospective)**:Stage A LODO 不优于 nearest-dose 且锚点 3-seed 无稳定方向
  → law 线硬停,降级画像论文;
- 模板审计不过 → 连续层降级诊断,law 只拟行为层;
- mixture 加性大偏 → targeted interaction correction 后仍大偏 → 主张4 降级
  "recipe 原则"(每个有用组件最低有效剂量+排毒+replay 兜底);
- 新模型 pilot 与 source 形状不符且第三点仍不符 → 主张3 的跨模型部分如实报 negative。

## 11. 时间线(以机器复活日为 D0)

| 段 | 内容 | 算力 |
|---|---|---|
| 现在–D0 | M0+M1 全部(章程+四冻结文件/Phase-1 LODO/套件/审计架/builder) | 0 GPU |
| D0 | P2a 段2(自动)+ base 画像 + 失败集冻结 + 审计 D 体检 | 1 机 |
| D0+1 – D0+5 | Stage A 47–55 run(两机分片) | 2 机 |
| D0+6 – D0+8 | Stage B:全 ckpt 跨域评测(0 train)→ 条件化补训 12–18 | 1–2 机 |
| D0+9 – D0+11 | M5 mixture 10–16 | 1 机 |
| D0+12 – D0+17 | M6 新模型 19–23(+可选缩微 3) | 1–2 机 |

GPU 合计 ≈ 9–13 台·日。无三方实验、无 agent、无金融域(蓝图禁区照抄)。
