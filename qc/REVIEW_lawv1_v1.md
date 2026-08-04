# REVIEW_lawv1_v1 — 顾问对 PLAN_lawv1 v1 的审阅(2026-08-04,逐字存档)

> 裁决:故事很强、骨架正确、预注册优于通常论文;**先修六点再开 Stage A**;
> M0/M1 立即可做,但不直接启动 55 个 Stage A runs。
> 执行响应见 PLAN_lawv1.md v2 + 四个新冻结文件(DOSE_DEFINITION /
> TRAIN_EVAL_SEPARATION / APPLICABILITY_MATRIX / UTILITY_AND_BASELINES)。

---

## 总体判断

这个方案已经不是"想法清单",而是一套**基本能执行、能失败、也能形成论文结果的实验计划**。故事、资产复用、预注册、停止规则、发现域—确认域拆分、mixture 开牌和新模型验证都接上了。尤其是:不再把16格包装成能力 taxonomy;S/R 只作为恢复性诊断;continuous metric 先过模板审计;reasoning 做完整发现,其他域只做缩微确认;预测必须在训练前冻结;law 不成立时有明确降级路线。这些设计都很扎实。

但我不会直接按 v1 全部开跑。当前最大的风险已经不是算力,而是:

> **最后拟出来的曲线,究竟是数据组件的剂量响应,还是 token 长度、数据抽样、训练模板和评测模板的响应。**

我认为先修下面六点,再开 Stage A。修完后这会是一个很强的方案。

---

# 一、最大问题:现在的"dose"还没有完全定义干净

当前计划:总训练集固定 2,000 examples;特殊组件替换等量 clean replay;2 epoch;剂量 30…2,000 条。这比"不断加数据、总量也涨"干净很多,但仍有关键混淆:

> 一条 format 数据、一条 selective-revision 数据和一条普通 replay 数据,输出 token 长度可能完全不同。

例如 replay 平均答案150 tokens、format 30、selective revision 250。替换480条后,example 数没变,但 assistant target tokens 变了;特殊组件参与 loss 的 token 比例变了;每类 token 的梯度暴露量变了。横轴 n 就不只是"数据条数"。

## 建议冻结两个剂量定义

主分析使用 q_d = component target tokens / all target tokens;同时报告 n_d = component examples。

训练时至少做到:replay 按输出长度分桶匹配;固定总 assistant target tokens 或 optimizer tokens;所有剂量使用同一个 carrier pool;高剂量通过预先冻结的**嵌套替换**得到(D_30 ⊂ D_60 ⊂ D_120 ⊂ …),从60到120是真正增加60条组件数据,而不是重新随机抽一套。

**这一点不改,剂量曲线的解释会不稳。**

---

# 二、训练数据和评测探针必须做"生成器隔离"

资产复用是优点,但危险:训练组件和 evaluation 使用相同的措辞、标签、schema 或生成逻辑,模型可能只是学会了生成器的体裁。这是"探针带体裁"问题的更大版本;模板审计只处理读出,还没解决 train–eval generator overlap。

## 至少需要四重隔离

| 层面 | 训练 | Evaluation |
|---|---|---|
| 底题 | train item families | 完全未见的 families |
| 数据源 | 训练源 | held-out benchmark/source |
| 生成 prompt | generator A | generator B |
| 表达模板 | schema/措辞 A | schema/措辞 B |

Format 尤其:训练若干简单 JSON schema;测试未见字段名、未见嵌套、未见顺序;另测同 schema 的 in-template 表现。否则看到的可能不是"format control 泛化",而是模型记住了某个 JSON 合约。

Selective revision 的 evaluation 应同时包含:KEEP/CORRECT;ACCEPT/REVISE;opaque labels(A/B/C 且映射置换);自然语言审核结果。

---

# 三、不要强制每个域都做完整"七条件笛卡尔积"

"同一道底题 × 七条件"在 reasoning 上自然,在 knowledge/IF 不一定全部成立:改写任务再做 paraphrase 测的是什么需重新定义;分类任务可能不存在"信息不足"版本;某些 extraction 没有自然的 correct-candidate;knowledge 删证据后模型可能靠参数知识仍知道答案。

改成 **Task–condition applicability matrix**:Reasoning 覆盖全部七项;Knowledge/IF 只对语义成立的条件生成版本。

## Knowledge 的 insufficient 特别小心

不能只删 2Wiki 证据就认为不可答——模型可能本来就知道。更干净:明确"只根据所给材料";用虚构或反事实实体;或写成文档特定事实;删除后程序/人工确认确实推不出。否则 insufficient-stop 混合了 grounded constraint 遵守、参数知识、回答意愿三件事。

## "Deployment stress test" 先改名

计划的压力层是合成受控组合,不是自然 deployment 数据。第一篇论文叫 **Compound perturbation stress test**;除非另加一批人类撰写的自然任务,才用 deployment stress test。

---

# 四、样本量对 5pp 左右的曲线可能偏小

300/200/200 底题:接近50%的二元指标,95%误差约 n=300 ±5.7pp、n=200 ±6.9pp。paired design 降部分噪声,但 wrong-candidate 只统计失败子集、S/R 只在 base failures 上统计、insufficient/format 有效样本被质检过滤、seed 波动本身数 pp(abstain 更高)时会更差。要判断"预测差3–5pp算不算准",200–300 题勉强。

- **方案A(倾向)**:reasoning 600–1,000 families;knowledge/IF 各400–500;stress 100–200。evaluation 主要耗推理不耗训练 GPU;
- 方案B:保留300/200/200,但预注册只判 >7pp 行为变化,小变化靠 continuous signal,CI 按 item family bootstrap,不把3pp写成稳定组件效应。

另外 **S/R 的失败集合必须固定为 base model 在冻结主评测上的失败题集合**,不能每个 checkpoint 重新筛,否则分母变了,AssistanceRecovery 不可比。

---

# 五、Seed 不能完全根据单-seed 曲线事后选择

在 onset/plateau/cliff 补 seed 若是看完默认 seed 后才选,就有选择偏差:单 seed 偶然的峰,恰好在那里补 seed 并称之为 onset。

## 固定重复 + 自适应重复分开

每组件开跑前固定三个重复锚点(如 n=0, 240, 2000 或 0, 120, 960),无论首 seed 结果如何都做 3 seeds。允许再追加一个自适应点,但标注 **adaptive refinement,不作为原始形态的独立确认**。

Stage B 从 Stage A 选 n_onset/n_high 没问题(新域独立确认),但**选择算法必须预先写死**:onset=预测效应首次超过噪声阈值的最小剂量;high=最大预注册剂量;若无 onset 则 mid/high null check。

---

# 六、Phase 1 不适合做整个项目的硬性生死门

archive 本身:剂量点少;协议不一致;pure-component 与 replacement 混合;部分曲线只有3–4点;endpoint/ckpt policy 不统一。四个点上同时比较 saturating/threshold/log-linear/rise-fall 很容易模型选择不稳;rise-fall 少于5个有效剂量几乎没有识别能力。

## Phase 1 的合理定位:决定值不值得进入一个较小的、干净的 prospective pilot

- Phase 1 赢过基线 → 直接进入完整 Stage A;
- 结果混合 → 先跑每组件 {0, 60, 480, 2000} 四点 pilot;
- 明显失败 → 仍允许 format 和已有强信号组件进四点 pilot;
- **真正的 law kill criterion 放在新的 prospective Stage A**。

Archive 可以证明"有可能",但不能替新的严格设计作最终裁决。

另外:C-18 v1.2 到达后不能直接覆盖已预注册的 M0。应在查看对应新结果前提交 **amendment**;保留旧版结果;明确 preregistered / amended / exploratory。

---

# 七、论文 scope 再说准一点

主模型和 held-out 模型都是 instruction-tuned(Qwen3-8B;Llama-3.1-8B-Instruct)。严格说研究的不是"从 base model 开始的一般 SFT scaling law",而是:

> **已有 instruction model 的二次 SFT / targeted adaptation recipe。**

这不弱,反而更贴近现实(企业通常在 instruct model 上做后训练),但论文要主动说清:用 **SFT recipe selection for post-instruction adaptation**。若想保留"通用 SFT"措辞,加一个很小的 base-model miniature(一个组件;三个剂量;一个 base model),只判断形态是否完全不同,不复制完整 pipeline。

---

# 八、Recipe 优化目标现在还不够可执行

U 还没真正定义。看到结果后再决定 endpoint 权重/retention 容忍/worst vs 平均,recipe 就成了事后挑选。

## 不用复杂加权和,采用字典序目标

硬约束:Δs_original ≥ −ε_o;Δs_retention ≥ −ε_r;s_insufficient ≥ ρ。
可行 recipe 中:1) 最大化 worst-condition;2) 再最大化主条件 macro-average;3) 再选数据量更少或更简单的 recipe。

符合故事:不牺牲基本可用性,优先补最脆弱的一块。target-optimal、retention-constrained、补最差等 baseline 也必须在 M5 前写成**确定公式**,不只是名字。

---

# 九、Mixture 改成"判别性选点"

六个 mixture、预测先冻结、误差大补关键 interaction,方向对。但 mixture 不应只选"听起来合理"的 recipe,应选**在不同模型假设下预测差异最大的配方**:

1. clean replay;2. uniform;3. constrained predicted optimum;4. unconstrained target optimum;5. 预测负交互最强的组件对;6. 单组件模型与简单加性模型分歧最大的配方。

一次训练区分:无组件特异效应 / 单组件加性 / pairwise interaction / 优化器是否真有价值。

"最多加6个 interaction runs"只能针对**一个最重要组件对**做校准,不能声称建立完整 pairwise interaction model。Scope 写成 **targeted interaction correction**。

---

# 十、新模型"两个 pilot 点"需要明确迁移假设

两个点不足以从头拟合 threshold/saturation/cliff。只能在以下假设下成立:

> 曲线形状从 Qwen 迁移,只重新标定幅度和横向尺度:G_new_{e,d}(n) = a_{e,d} · G_source_{e,d}(b_d · n)

两个 pilot 才有清楚意义:一个估起效位置;一个估幅度/平台。**迁移假设必须预注册并检验**;若两点与 source shape 明显不符,触发**第三个 calibration dose**,而不是强行输出 recipe。

最终关键比较:predicted recipe 3 seeds;uniform 3 seeds;clean replay 3 seeds;其他人工 baseline 可单 seed。否则"recipe 优于 baseline"只有单 seed,会很可惜。

---

# 收敛版执行方案

## M0–M1:现在就可以做,增加四个冻结文件

1. `DOSE_DEFINITION.md` — example、target token、总 token、step、嵌套替换;
2. `TRAIN_EVAL_SEPARATION.md` — 题源、generator、schema、标签、模板隔离;
3. `APPLICABILITY_MATRIX.csv` — 每个 task type 哪些 perturbation 合法;
4. `UTILITY_AND_BASELINES.md` — recipe 目标、约束、所有 baseline 计算规则。

## Stage A:保留 ~55 runs,但

固定三个 seed anchors;其他点默认单 seed;总 target tokens 匹配;固定嵌套 carrier;主 endpoint 预先指定;同时报行为层和审计通过的连续层。

## Stage B:先零训练评估迁移

先把全部 Stage A checkpoints 直接在 knowledge/IF evaluation 上测一遍(已回答跨域迁移)。然后只有满足以下之一的组件才在确认域训练:reasoning 响应稳定但跨域不迁移;跨域方向一致但幅度需校准;最终 recipe 关键组件。Stage B 从26 降到约 **12–18 runs**。

## Mixture 与新模型

mixture 约10–16 runs;new model 18–22 runs(三个核心 arms 3 seeds)。总规模仍约 **90–110 train runs**,但每个 run 的识别意义更清楚。

---

# 预计最可能的结果

- **Format**:低剂量快速起效后饱和;未见 schema 迁移弱于同模板;高剂量分布偏移;
- **Evidence robustness**:wrong-candidate/distractor 中等收益,跨域不完全;可能伴随更强怀疑倾向;
- **Selective revision**:keep 与 correct 明显 trade-off,balanced pairing 缓和但不消除;
- **Answerability**:insufficient-stop 上升同时 answer rate 下降,清楚的 Pareto frontier;
- **Continuous signals**:部分 endpoint 的 margin/BPB 比 accuracy 平滑;另一些因模板变化失去方向一致性,只作诊断;
- **Mixture**:低中剂量近似加性,高剂量/pure-component corner 明显非加性;
- **最终 recipe**:很可能不是精确比例,而是"每个有用组件给到最低有效剂量,排除无效/有毒组件,其余预算留给多样化 clean replay"。这是很好的论文结果——把 recipe optimization 收敛成可执行原则,而不是装作能精确预测每个百分比。

---

## 最终评价

故事:很强。实验骨架:正确。预注册和失败路径:明显优于通常论文。
当前最需要修的:**dose 定义、train/eval 模板隔离、适用性矩阵、固定 seed anchors、objective 冻结和跨模型校准假设**。
修完这些后建议正式开跑。现在适合立即做 M0/M1,但不建议直接启动55个 Stage A runs。蓝图核心链路已收敛,执行计划需要的是识别层面的最后一次收紧,而不是再扩充 scope。
