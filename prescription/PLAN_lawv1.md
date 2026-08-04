# PLAN_lawv1 — 收敛版故事的可执行实验计划(2026-08-04 v1)

> 蓝图原文:qc/BLUEPRINT_convergent_v1.md(逐字存档)。
> 本文件回答一个问题:**"我想搞成这样怎么做实验"** —— 把 Phase 1–5 翻译成
> 具体的 run 清单、复用件、预算数学、预注册节点、时间线。
> 铁律照旧:一切数字只认 repo 数据文件;单 seed 臂标注;缺失申报不重构;
> 每个冻结节点 = 一次 commit,预测先于训练。

---

## 0. 一页总览

```
M0 零算力(今天可做)   章程 prereg + Phase-1 归档全量 LODO(fit_pilot v2)
M1 CPU 建设(今天可做) 评测套件 v1(3域×7条件+S/R+压力层)+ 模板审计架 + 组件 builder
M2 GPU Stage A         Reasoning 发现域全网格          ~56 train + 评测
M3 GPU Stage B         Knowledge/IF 缩微确认            ~26 train
M4 零算力              跨域迁移分析(M2/M3 数据重读)     0 train
M5 GPU Phase 4         mixture 开牌(预测先冻结)         ~10 train
M6 GPU Phase 5         新模型 recipe 决战               ~15 train
                                            合计 ≈ 105–120 train run
```

参照:P2a 段1 = 12 train + 12 factorial eval,单台 8 卡机一个工作日内完成
(含事故重跑)。按此吞吐,GPU 总量 ≈ **8–12 台·日**,两台机稳定在手 ≈ 1.5–2 周纯算力。

---

## 1. 资产映射表:新设计 vs repo 现有件(先盘家底再开工)

### 1a. 七条件 ↔ 现有评测机器

| 新七条件 | 现有对应物 | 状态 |
|---|---|---|
| Original | 素题 O_acc(loop3/batch1;16-cell 因子里的 clean 臂) | **REUSE** |
| Paraphrase | 论文 surface-robustness 变体机(paper_v3 画像 93.5 vs 60.6 那套) | **ADAPT**(挪到新题源) |
| Distractor | scenario_repair_v3 failure injectors(干扰注入) | **ADAPT** |
| Wrong candidate | 修复腔 override 臂(P0c/P1 全套 preds+scorer) | **REUSE** |
| Correct candidate | 修复腔 keep 臂(同上) | **REUSE** |
| Insufficient | INSUFFICIENT 8 格 + v3 abstain class + d6 builder | **REUSE** |
| Structured output | Interface 轴 JSON/FREE_TEXT(16-cell 因子) | **REUSE** |
| (二层)S 探针 | v2 CoT 注入;(R 探针)v2.1 Skill/actionized-CoT 注入 | **ADAPT**(改为 failure-conditioned) |
| (压力层)多因子混合 | 16-cell 因子本身就是 2×2×2×2 组合机 | **ADAPT**(挑 3–4 个双/三因子格) |

结论:七条件里 5 条是现成机器,只有 Paraphrase/Distractor 要挪接到新题源。

### 1b. 五组件 ↔ P2a 组件库(prescription/d_components.py)

| 新组件 | P2a 对应 | 改造点 |
|---|---|---|
| Clean replay(placebo) | d0_replay | 无 |
| Evidence robustness | d2_verify + d5_provenance | 合并为一个组件(冲突/干扰/错误中间步) |
| Selective revision | d3_revise | 补齐"正确候选→保留"配对(P2a 版已有雏形) |
| Answerability | d6_abstain | 无 |
| Format/schema | d1_format | 无 |

结论:组件库 ≈ 已建成,主要工作是 evidence 合并 + 各组件扩产到 2000 条。

### 1c. 其余部件

| 新设计部件 | 现有对应 | 状态 |
|---|---|---|
| Phase-1 拟合架(形态库/Huber/LODO) | prescription/fit_pilot.py + results | **扩展**(v2:全量 LODO+基线+rise-fall) |
| 预测冻结→开牌协议 | p2a_h1.py freeze/score 模式 | **REUSE** |
| 多机跑批 | scripts/run_p2a.sh + bringup.sh(本地盘训练/HDFS 搬运/done-marker 全踩过坑) | **REUSE**(改参数) |
| Reasoning 题源 | gsm_repair_v4(GSM8K 移植管线)+ svamp/(持出面) | **REUSE** |
| Knowledge 题源 | wiki2/(2Wiki)+ stratqa/ | **REUSE** |
| IF 题源 | 无(naturalset/ 待盘点) | **NEW**(最大新建件之一) |
| 连续层 margin 评测 + 模板审计 | 无(E5 教训有,架子没有) | **NEW**(第二大新建件) |
| seed 噪声量尺 | genre_scores 3-seed 半距(B±4.0/A1±2.5/C±3.9/弃答±15pp) | **REUSE**(判据基准) |

**两个真正的新建件:IF 域评测 + 模板审计架。其余全是改造复用。**

---

## 2. M0 — 零算力,立即可做(机器死着也不耽误)

### 2.1 实验章程 EXP_CHARTER_lawv1.md(prereg commit,开跑前冻结)

写死四条停止规则(蓝图裁决3原文):
1. **全网格准入**:组件须满足{archive 方向性信号 / pilot 效应 > seed+模板噪声 / 与主 profile 明确对应}之一,否则只跑 {0, mid, high} null check;
2. **Seed 分配**:只在 onset / plateau / 高剂量疑似损伤 / 最终 recipe+主基线 处 +2 seeds;
3. **跨域扩展**:reasoning 域 held-out dose error < seed+模板噪声 且行为方向稳定,才进确认域;
4. **连续指标准入**:模板审计(A–D 四项)通过的 margin/BPB 才进 law fitting 与 optimizer。

外加本组既有铁律:预测冻结 commit 先于训练;单 seed 臂标注;数字只认数据文件。

### 2.2 Phase 1 = fit_pilot v2(归档全量 LODO,纯 CPU)

现状:fit_pilot v1 已做 5 条曲线各 1 个持出点,4/5 过(NOTES_fit_pilot.md)。
v2 扩展(全部在冻结数据上):
- **全量 leave-one-dose-out**:每条曲线轮流持出每个内点(format 4点→2个内点、drills×2、datasize、keep 配比,共 ~10 个持出任务);
- **interpolation / extrapolation 分开报**(持出端点=外推,单独一列);
- **三个哑基线**:nearest-dose / linear / constant,law 形态必须赢过它们才算数;
- **形态库 +rise-fall**(log 二次已探索性验证可拟;datasize 峰在1000、drills-keep 谷在25 两条非单调曲线是它的用武之地);
- **P2a 段2 数据一到即并入**(60/600/2000 × 6 组件 × 16 格 = 归档外最大的新曲线束)。

产出:NOTES_phase1_lodo.md + 一张"法则 vs 哑基线"胜负表。
**判据(章程写死)**:law 中位盲误差 < nearest-dose 基线,且 ≥2/3 曲线在噪声带内 → Phase 2 放行;否则硬停出裁决文档。

---

## 3. M1 — CPU 建设(与 M0 并行)

### 3.1 评测套件 lawv1_eval(冻结后 hash 入 commit)

结构:**同一道底题 × 七条件配对生成**(paired design,底题 ID 贯穿):

| 域 | 题源 | 底题数 | 条件版本 |
|---|---|---|---|
| Reasoning(发现域) | GSM8K(gsm_repair_v4 管线)+ SVAMP 持出面 | 300 | ×7 = 2100 items |
| Knowledge(确认域) | 2Wiki + StratQA | 200 | ×7 = 1400 |
| IF(确认域) | 新建:抽取/分类/改写/约束输出 | 200 | ×7 = 1400 |

- 生成器:Paraphrase 用改写机+答案不变性校验;Distractor 用 v3 injectors;
  candidate 对用修复腔机器;Insufficient 用 d6 删条件配对;Format 用 Interface 轴模板。
- **S/R 二层**(裁决1):只对主画像失败的底题触发,S=给关键步骤,R=给规则;
  报 AssistanceRecovery_S/R = s_assisted − s_unassisted,**不并入主七维均分**;
- **压力层**:每域另配 100 题多因子版(干扰+错误候选+格式约束同时上,
  用 16-cell 组合机现成拼),只做"受控发现是否在自然压力下复现"的验证,不进 law;
- **Retention**:素题全域套卷(三域 Original 合并)+ 训练域外基准,做硬约束指标。

### 3.2 连续层 + 模板审计架(裁决2,NEW)

- margin 评测脚本:对 KEEP/CORRECT/INSUFFICIENT(及各条件的 gold action)
  测 label-continuation logprob margin(vllm prompt_logprobs 或 HF forward,离线可跑);
- 探针变体:3 语义模板(KEEP/CORRECT/INSUFFICIENT;ACCEPT/REVISE/CANNOT-DETERMINE;中文短句)
  × 2 标签置换 × 体裁挪移(自然语言/分类模板/JSON)≈ 8 个变体/判断;
- 报 M̄ 与 Var_k;审计 D(margin↔生成行为对齐)在 base + 2 个已归档 ckpt 上先行体检;
- **三级准入表**(一致+对齐→主读出;一致未跨阈→早期信号;不一致→仅诊断)写进章程。

### 3.3 组件 builder 扩产

d_components.py → lawv1 版:evidence=d2+d5 合并;selective revision 补 keep 配对;
每组件产 2000 条(**剂量=替换等量 replay,总 N 恒 2000**,故 dose-0 = 纯 replay 2000 = placebo 臂,全组件共享)。
与 P2a 的差别要在章程里申报:P2a 是纯组件剂量,lawv1 改为替换式(F/G 分离更干净)。

---

## 4. M2 — Stage A:Reasoning 发现域全网格(GPU)

训练协议冻结(沿 P2a configs):Qwen3-8B,full FT + ds z3,固定 lr/schedule,
总 N=2000 examples,2 epochs,末位 ckpt,默认 seed 42;本地盘训练→cp HDFS(m2 教训)。

| 项 | run 数 |
|---|---|
| 4 特殊组件 × 剂量 {30,60,120,240,480,960,2000} | 28 |
| placebo(dose-0,纯 replay) | 1 |
| 关键剂量补 seed:4 组件 × 3 位置(onset/plateau/high)× 2 extra seeds | 24 |
| placebo 补 2 seeds | 2 |
| base(不训,只评测) | 0 |
| **合计** | **~55** |

评测每 ckpt:reasoning 七条件全套 + retention 套卷 + 连续层探针(通过审计的);
S/R 只在 base 失败子集上跑。产出 = 每组件 × 每 endpoint 的剂量响应向量曲线。

**预注册**:开跑前用 Phase-1 拟合 + P2a 段1 冻结每组件每 endpoint 的
方向预测(+形态猜测),p2a_h1.py 模式 freeze commit。开牌 = LODO 盲误差 vs 噪声量尺。

## 5. M3 — Stage B:确认域缩微(GPU)

n_onset/n_high 取自 Stage A 曲线(不提前定死):
4 组件 × {n_onset, n_high} × 2 确认域 = 16;+ placebo×2域 2 + 最终 recipe/uniform/replay 在两域重复 ~8 → **~26 run**。
只回答三问:方向跨域成立?onset/plateau 迁移?recipe 副作用?

## 6. M4 — 迁移分析(零算力)

M2 的 reasoning 训练件在 M3 确认域评测数据里已经有了跨域读数
(evidence robustness 训在 reasoning → wrong-candidate 在 knowledge/IF 测):
纯重读,产出"通用行为 vs domain-specific"判定表。

## 7. M5 — Phase 4 mixture 开牌(GPU,~10 run)

6 个 mixture(uniform / 按失败频率 / 补最差 / target-optimal / retention-constrained / 故意有害)
× 1–2 seeds。**训练前**用单组件曲线冻结全 endpoint 预测(加性假设 = prereg 假设);
开牌判加性:误差 < 噪声 → optimizer 放行;误差大 → 只补最重要 pairwise 交互(章程限定最多 +6 run)。

## 8. M6 — Phase 5 新模型决战(GPU,~15 run)

held-out 模型(候选:Llama-3.1-8B-Instruct,与 Qwen 家族异源;定稿入章程):
画像(0 train)→ 每组件 2 小剂量 pilot(4×2=8)→ 重标定 → 预测 recipe(冻结)→
recipe 1 次全训 + 基线{uniform, pure replay, 人工比例, 补最差} 4 次 + 关键臂补 seed ~2。
验收指标 = 蓝图十五之4 的全清单(original/worst-condition/paired/insufficient-stop/format/retention)。

---

## 9. 与在跑事项的关系

- **P2a 段2 照旧**(机器活了先跑它):它就是"60 条 pilot 预测 600/2000 排序"的
  H1 检验 = 论文主张3 的第一块证据;其 36 个 ckpt × 16 格全部并入 Phase-1 归档拟合;
- lawv1 的 {30…2000} 8 点网格是 P2a 三点 log 网格的加密版,P2a 的 θ-bracketing
  教训(fit_pilot 唯一翻车点)正是 8 点网格要吃掉的;
- C-18 v1.2(顾问的拟合协议修订)到达后,形态库/区间预测规矩以 v1.2 为准更新本计划。

## 10. 预注册节点清单(每个 = 一次 commit,先于对应训练)

1. EXP_CHARTER_lawv1(停止规则+准入规则+判据) — M0;
2. fit_pilot v2 脚本(=Phase-1 设计) — M0,先 commit 后运行;
3. 评测套件 hash + 生成器版本 — M1 末;
4. Stage A 方向/形态预测冻结 — M2 开跑前;
5. mixture 全 endpoint 预测冻结 — M5 开跑前;
6. 新模型 recipe 预测冻结 — M6 全训前。

## 11. 死活判据(kill criteria,章程原文)

- Phase-1 全量 LODO 输给 nearest-dose 基线 → law 线硬停,论文降级为
  "画像+组件方向效应"(现有 P0c/P1/P2a 证据链仍立);
- 模板审计不过 → 连续层降级为诊断,law 只拟行为层(慢但不死);
- Stage A 曲线全被噪声淹没 → 剂量网格上移/换 N,只重跑一轮,再不行硬停;
- mixture 加性大偏 → 主张4 降级为"pairwise 修正后可预测",范围写小。

## 12. 时间线(以机器复活日为 D0)

| 段 | 内容 | 算力 |
|---|---|---|
| 现在–D0 | M0+M1 全部(章程/Phase-1 LODO/评测套件/审计架/builder) | 0 GPU |
| D0 | P2a 段2(已排队自动跑)+ base 画像 + 审计 D 体检 | 1 机 |
| D0+1 – D0+5 | Stage A 55 run(两机分片,run_p2a.sh 模式) | 2 机 |
| D0+6 – D0+8 | Stage B 26 run + M4 重读 | 1–2 机 |
| D0+9 – D0+11 | M5 mixture 10 run | 1 机 |
| D0+12 – D0+16 | M6 新模型 15 run | 1–2 机 |

GPU 合计 ≈ 8–12 台·日;全程无三方实验、无 agent、无金融域(蓝图禁区照抄)。
