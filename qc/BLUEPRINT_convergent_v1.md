# BLUEPRINT_convergent_v1 — 收敛版故事定稿(2026-08-04,Xingwei 粘贴,逐字存档)

> 存档说明:以下为 Xingwei 转来的收敛版故事全文(含三点非小修补的裁决),
> 逐字保留(粘贴产生的 markdown 断行/`===` 残留一并保留)。
> 执行计划见 prescription/PLAN_lawv1.md。铁律 0 照旧:本文中的一切数字
> 只作叙事参考,不作数据来源;репо 数据文件才是数字的唯一来源。

---

可以。现在把前面所有讨论收敛后,整个故事应该这样讲。

# 一、我们真正想解决什么问题

我们的目标不是做一个更复杂的 benchmark,也不是给模型发明一套"16种能力"。

我们真正想解决的是:

> **给定一个基础模型和有限的训练预算,应该使用哪些类型的 SFT 数据、每种用多少,才能训练出一个整体更好的模型?**

现在的 SFT 往往还是经验式的:

* 人工挑数据;
* 人工设比例;
* 训练一次;
* 看 aggregate benchmark;
* 不好再返工。

但我们并不知道:

* 某类数据多少条开始起效;
* 什么时候已经饱和;
* 继续增加是否会带来损伤;
* 提升一个目标时会不会破坏其他表现;
* 对一个模型有效的 recipe,是否适合另一个模型。

所以我们想把 SFT 从:

> 试配方、看结果

变成:

> **先诊断模型,再测训练响应,最后反推配方。**

---

# 二、为什么原始 benchmark 不够?

原始 benchmark 通常只告诉我们:

> 模型在这批题上答对了多少。

例如两个模型在一个 reasoning benchmark 上都是80%。

但它们可能完全不同。

模型 A:

* 原题会做;
* 换一种说法就容易错;
* 给一个错误候选答案后容易被带偏。

模型 B:

* 对改写和错误候选都很稳定;
* 但信息不足时总是强行猜答案;
* 要求 JSON 输出时经常失败。

虽然两个模型原始分数相同,但显然不应该使用同一套 SFT recipe。

因此,单一 benchmark 分数不能直接告诉我们:

> 下一轮应该训练什么。

---

# 三、Evaluation 应该分成两个维度

这里最重要的是把 **任务本身** 和 **测试条件** 分开。

## 1. Task domain:模型在做什么

第一版可以先覆盖三类通用任务:

### Reasoning

* 数学问题;
* 逻辑推理;
* 多步问题求解。

### Knowledge

* 常识问答;
* STEM知识;
* 长尾事实;
* 专业知识判断。

### General instruction following

* 信息提取;
* 分类;
* 阅读理解;
* 改写;
* 约束输出。

暂时不引入:

* agent;
* tool use;
* web search;
* repository editing;
* 长流程任务;
* 金融垂直领域适配。

因为我们的主题是**通用 SFT**,不是 agent training,也不是 domain adaptation。

---

## 2. Perturbation condition:模型在什么条件下完成任务

对于同一道题,构造几个受控版本。

### Original

原始干净问题。

测模型是否具备基础任务能力。

### Paraphrase

只改变措辞,不改变信息和答案。

测模型是否依赖原题表述。

### Distractor

加入无关但看起来相关的信息。

测模型能否选择真正有用的信息。

### Wrong candidate

提供一个错误候选答案或错误中间结果。

测模型会不会被错误信息带偏。

### Correct candidate

提供一个正确候选结果。

测模型能否保留正确结果,而不是为了"修改"而乱改。

### Insufficient information

删除回答所必需的信息。

测模型是否知道当前无法确定,而不是强行猜测。

### Structured output

保持任务内容不变,但要求 JSON、schema 或特定格式。

测模型能否按照指定接口稳定调用已有能力。

这些不是七种独立的基础能力,而是:

> **对同一个任务施加的受控测试条件。**

---

# 四、我们得到的不是一个总分,而是 Failure Profile

对每个模型,我们同时测:

s_0(m) = [s_original, s_paraphrase, s_distractor, s_wrong-candidate, s_correct-candidate, s_insufficient, s_format]

这里的 s 就是评测分数。

例如:

| Evaluation               |   分数 |
| ------------------------ | ---: |
| Original                 | 0.80 |
| Paraphrase               | 0.77 |
| Distractor               | 0.61 |
| Wrong candidate          | 0.34 |
| Correct candidate        | 0.85 |
| Insufficient information | 0.20 |
| Structured output        | 0.48 |

这个模型的情况就很清楚:

* 基础任务能力还可以;
* 很容易被错误候选带偏;
* 信息不足时容易乱答;
* 结构化输出不稳定。

这就是训练前画像,或者叫:

> **Fine-grained failure profile。**

它回答的是:

> 模型具体在哪种使用条件下不稳定。

---

# 五、受控测试和真实压力测试是什么关系?

我们的 story 可以分成两层。

## 第一层:Controlled perturbation

一次只改变一个因素。(原题 vs 改写;无候选 vs 错误候选;信息充分 vs 信息不足;自然语言 vs JSON。)

这层的作用是:**清楚定位模型为什么失败。** 它强调可解释性和因果控制。

## 第二层:General deployment stress test

在更自然的通用任务中,同时加入多个现实条件(用户先给出一个错误理解;输入里有无关信息;某个必要条件缺失;要求固定格式;需要检查已有答案而不是重新回答)。

这不是金融业务,也不是 agent。它只是模拟普通模型真实使用时的压力:输入没有 benchmark 那么干净,模型还能不能稳定工作?

这层的作用是:**确认受控扰动中发现的问题,在更自然的使用场景下仍然真实存在。**

Controlled perturbation → 定位失效原因;Deployment stress test → 验证失效具有现实意义。

---

# 六、然后我们设计 SFT 数据组件

Fine-grained evaluation 只能告诉我们哪里有问题,不能直接告诉我们该训练什么。因此下一步要建立候选 SFT component library。第一版可以只做四到五种组件。

## 1. Clean instruction replay

普通、正确、多任务的 SFT 数据。两个作用:作为通用 SFT baseline;估计 ordinary SFT 本身会怎样改变模型。这就是 placebo 或 clean replay。因为普通 SFT 即使没有特殊设计,也可能:提升一般指令执行;改变回答倾向;损害信息不足时停止回答的行为。

## 2. Evidence robustness

训练样本中加入:无关信息;错误候选;冲突陈述;错误中间步骤。要求模型独立判断,不盲从输入。目标是提高:抗干扰;错误信息验证;conflict robustness。

## 3. Selective revision

成对构造两类数据:候选正确应该保留;候选错误应该修正。目标不是教模型"总是修改",也不是"总是接受",而是:根据候选本身是否正确决定保留还是修改。

## 4. Answerability

构造信息充分和信息不足的配对样本。信息充分时正常回答。信息不足时明确表示:无法确定,缺少必要信息。目标是保护模型的回答边界,避免 SFT 后形成:用户问了,就必须给一个具体答案。

## 5. Format/schema

要求模型输出:JSON;固定字段;指定标签;特定 schema。目标是训练模型把已有判断稳定映射到指定接口。

---

# 七、我们的实验变量是什么?

一个完整 SFT recipe 不只是"用了哪类数据":

r = { n_1,...,n_D; N; steps; order }

其中 n_d = 第 d 类数据有多少;N = 总训练规模;steps = 训练强度;order = 训练顺序或 curriculum。

第一阶段先收紧,只研究:数据组件 d;数据剂量 n;固定总训练预算和训练协议。后面再扩展到 mixture、总预算、训练顺序。

---

# 八、我们提出的 Scaling Law 假设是什么?

假设:同一种 SFT 数据随着剂量增加,对模型表现的影响不是随机的,而是可能呈现可预测的响应趋势。

训练后重新测相同的 evaluation profile s(m,r);训练造成的整体变化 Δs(m,r) = s(m,r) − s_0(m)。

关键:**Δs 是一个向量,而不是一个目标分数。** 例如一类数据可能产生

Δs = [+0.02, +0.03, +0.25, +0.30, −0.05, −0.35, +0.10]

它可能提高错误候选鲁棒性、提高修正错误结果,但严重损害信息不足时停止回答。所以不能只说"这个组件提高了25个百分点",必须说"它把整个模型画像推向了哪个方向"。

---

# 九、为什么 clean replay 必须单独建模?

模型训练后的变化至少有两部分:普通 SFT 效应 + 特殊组件额外效应。

Δs_e(m,d,n,N) = F_e(m,N) + G_{e,d}(m,n)

其中 F_e(m,N) = 同等预算的普通 clean SFT 对指标 e 的影响;G_{e,d}(m,n) = 特殊组件相对 clean replay 的额外影响。

例如:base 的 insufficient-stop 是0.46;clean replay 后变成0.06;某个特殊组件后变成0.15。那么这个特殊组件相对 base 仍然下降了,但相对 clean replay 实际上改善了 0.15−0.06=+0.09。

如果没有 placebo,我们可能错误地认为特殊组件损害了 insufficient-stop。实际上主要损伤来自 ordinary SFT,特殊组件只是部分修复了它。

---

# 十、单组件剂量响应可能是什么形状?

不同组件不必共享同一种曲线。可能出现:

- **Saturation**:少量数据快速起效,随后边际收益下降(format 很可能属于这一类);
- **Threshold**:低剂量几乎没作用,超过某个临界点后快速变化;
- **Null effect**:相对 clean replay 没有稳定额外收益;
- **Damage/cliff**:低剂量还稳定,高剂量突然造成损伤。

因此,我们不是先宣布一个公式,而是比较几个简单候选形态。真正的验证不是拟合训练点,而是:**留出一个剂量,只用其他剂量预测它。**

---

# 十一、PPL、BPB 和行为评测怎么放?

两层 evaluation:

## 连续响应层

target-only NLL;BPB;correct-action margin。例如对 KEEP / CORRECT / INSUFFICIENT 三个动作,测正确动作相对其他动作的 log-probability margin。这类指标连续、对小剂量变化敏感、比 accuracy 更适合拟合曲线。

## 行为验收层

final accuracy;paired accuracy;JSON validity;correct-candidate preserve;wrong-candidate repair;insufficient-stop;original benchmark retention。这层回答:模型最终实际生成时,到底有没有做对。

**BPB/margin 用来看到平滑的学习趋势,行为指标用来决定模型是否真的变好。** 不能只优化 PPL 或 BPB,因为 loss 下降不保证实际生成行为同步改善。

---

# 十二、从单组件走向 mixture

如果每个组件的响应可以近似组合:Δs_mix ≈ F(N) + Σ_d G_d(n_d)。

但这只是待验证假设。真实情况可能存在交互:Δs_mix = F(N) + Σ_d G_d(n_d) + Σ_{d<d'} I_{dd'}(n_d,n_{d'})。

实验上先用单组件曲线预测 mixture,然后训练开牌。如果误差小,可以直接用单组件 pilot 搜索 recipe。如果误差大,只补最重要的 pairwise interaction。

---

# 十三、最后怎么反推 SFT recipe?

r* = argmax_r U(s_0(m) + Δŝ(m,r)) s.t. Cost(r) ≤ B;
硬约束:s_original(m,r) ≥ s_original(m,0) − ε;s_retention(m,r) ≥ ρ。

在固定预算下,最大化整体表现,但不能明显破坏原始 benchmark,也不能让保护指标跌破底线。最终输出的不是一句"多加 verification 数据",而是一套具体方案,例如:clean replay 1,200条;evidence robustness 240条;selective revision 480条;answerability 120条;format 60条;固定2个 epoch。

---

# 十四、完整实验计划

## Phase 1:现有数据验证趋势

利用现有 archive(format;drills;keep;clean replay;balanced mixture)做:leave-one-dose-out;interpolation 与 extrapolation 分开;accuracy、BPB、margin 同时拟合;target 和 collateral endpoints 同时预测;与 nearest-dose、linear、constant baseline 比较。目标:判断局部 component–dose response 是否真的可预测。

## Phase 2:重新跑干净的单组件剂量实验

任务域:Reasoning;Knowledge;General instruction following。
组件:Clean replay;Evidence robustness;Selective revision;Answerability;Format。
剂量:n ∈ {0,30,60,120,240,480,960,2000} 起步。
对每个剂量:固定总 examples 或 tokens;特殊组件替换等量 clean replay;固定训练 steps;固定 checkpoint policy;关键点补3个 seeds。
目标:得到每个组件对每个 evaluation endpoint 的局部响应曲线。

## Phase 3:检验跨任务迁移

例如:在 reasoning 数据上训练 evidence robustness;在 knowledge 和 extraction 上测试 wrong-candidate robustness。如果只在训练域改善,说明它仍然是 domain-specific SFT。如果跨域改善,说明它更接近通用 instruction behavior。

## Phase 4:Mixture prediction

设计少量代表性 mixture:uniform;按 failure frequency;只补最差指标;target-optimal;retention-constrained;deliberately harmful mixture。训练前先冻结预测,之后训练开牌。

## Phase 5:新模型 recipe 验证

在一个没有参与完整拟合的新模型上:1. 跑训练前 failure profile;2. 每个组件只跑两个小剂量 pilot;3. 重标定响应参数;4. 预测最优 recipe;5. 一次完整训练;6. 与 uniform、clean replay、人工比例等 baseline 比较。最终看:original benchmark;held-out perturbation;worst-condition;paired selective revision;insufficient-stop;format compliance;retention。

---

# 十五、论文真正要证明什么?

1. 原始 benchmark 不足以决定 SFT recipe(相同总分的模型可能有不同 failure profile);
2. 不同 SFT 组件具有不同剂量响应(有的快速饱和,有的无效,有的高剂量有害);
3. 训练前画像和小剂量 pilot 能预测训练结果(不是事后解释,而是预测 held-out dose、mixture 和新模型);
4. 预测生成的 recipe 确实训练出更好的模型(相同预算下:目标行为更好;worst-condition 更好;原始能力不明显下降;信息不足边界和 retention 得到保护)。

---

# 十六、最终 Big Picture

General Benchmark → Controlled Perturbation Diagnosis → Small-Dose SFT Pilots → Multi-Dimensional Response Law → Constrained SFT Recipe

> 原始 benchmark 告诉我们模型会不会做;受控扰动告诉我们模型在什么条件下会坏;小剂量 SFT 实验告诉我们不同数据和剂量如何修复这些问题;response law 用来预测收益和副作用;最后在预算与保留约束下反推出训练配方。

一句话概括:**我们不是为了做一个更细的 benchmark,而是把细粒度 evaluation 变成一种训练诊断工具,用少量 SFT pilot 预测数据类型和剂量对模型整体行为的影响,并据此设计通用 SFT recipe。**

---
---

# 附:三点裁决(同日粘贴,非小修补,直接写进实验设计)

## 1. S/R 探针保留,但不并入主七条

S = 给出关键步骤或中间支架;R = 给出可用规则、原则或解题方法。它们测的是**干预后的可恢复性**(Failure → Provide Step/Rule → Recovery?),与主七条(自然状态和常见输入压力)性质不同。

Profile 分两层:
- **主画像 Unassisted robustness profile**:定义训练目标、拟合 response、recipe 优化、跨模型比较;
- **可选诊断 Assistance-recoverable probes**:区分 (1)完全不会 (2)知道但无法自主调用 (3)给步骤能做 (4)给规则能迁移 (5)给帮助仍不行。

派生量:AssistanceRecovery_S = s_step-assisted − s_unassisted;AssistanceRecovery_R 同理。

用途:给帮助也恢复不了 → 需要领域内容或完整推理轨迹;给一点帮助就能恢复 → 只需 elicitation/scaffolding/format/verification 数据。但 S/R 不参与主七维 profile 的平均分。

结构:Main Failure Profile + Optional Recoverability Profile。

## 2. Margin/NLL 模板敏感性 = 连续指标进入主实验前的准入审计(不是 limitation)

M(x) = log p(a_gold|x) − max_{a≠gold} log p(a|x) 可能同时受标签 token 数、frequency、大小写、位置、前缀措辞、冒号/换行/JSON、训练中是否见过同类模板、某 action 天然易续写等影响。E5→E5b 教训:**连续读出只有通过模板控制后,才能被解释为行为响应。**

四项模板审计:
- **A 语义等价模板复现**:同一判断至少3种表达(KEEP/CORRECT/INSUFFICIENT;ACCEPT/REVISE/CANNOT DETERMINE;中文自然语言版)。方向只在一个模板成立就不算稳定响应;
- **B 标签置换**:标签映射随机交换(A=KEEP…),再换一组;暴露 token 偏好;
- **C 体裁控制**:同一语义放入普通自然语言/简短分类模板/JSON/与训练体裁不一致的模板;
- **D 连续指标与生成行为对齐**:corr(M(x), 1[generation correct]);margin 跨0时行为 accuracy 是否真的变化。

报告方式:报多模板均值 M̄(x) 与模板间方差 Var_k[M_k(x)],区分剂量响应 vs 模板响应。

三级准入:多模板方向一致+行为对齐 → 主要曲线读出;多模板一致但行为未跨阈值 → 早期学习信号;模板间方向不一致 → 只作诊断,不进入 law/recipe。

## 3. Phase 2 规模必须砍:Discovery domain full grid,confirmation domains sparse validation

5 comp × 8 dose × 3 domain = 120 起步会失控(还没算 seeds/mixture/held-out model/模板审计/重跑)。

### Stage A:Reasoning 作为发现域
理由:答案易程序验证;wrong candidate/missing info/step assistance 易受控生成;BPB/margin/accuracy 都清楚;已有 archive 主要在此域。
特殊组件 4 个(clean replay 是对照):4×7=28 非零 run + replay controls;seeds 只补 onset/plateau/high-dose 三区 ×2 seeds = 24。合计约 **55–65 runs**(5 特殊组件则 +13–15)。

### Stage B:Knowledge 和 General Instruction 缩微确认
只验证:方向跨域成立?onset/plateau 位置迁移?reasoning 选出的 recipe 在其他域的副作用?
每组件只跑 n ∈ {0, n_onset, n_high}(取自 reasoning 阶段,不提前固定死):4×2×2=16 runs;最终 recipe/uniform/clean replay 重复验证 +10–15。
单模型主实验合计约 **70–90 runs**。

### 预算数学写进实验章程(开跑前冻结的停止规则)
- **全网格准入**:组件需满足 archive 方向性信号 / pilot 效应超 seed+template noise / 与主 profile 明确对应 之一,否则只跑 {0, mid, high} null check;
- **Seed 分配**:只给 初次离开0处 / 预测平台处 / 高剂量疑似损伤处 / 最终 recipe 与主要 baseline 补 seed;
- **跨域扩展**:reasoning 中 held-out dose error < seed/template noise 且行为方向稳定,才进其他域;
- **连续指标准入**:只有通过模板审计的 BPB/margin 才能进 response-law fitting 和 recipe optimizer。

### 收紧后的完整链路
Unassisted Failure Profile (+Optional Assistance-Recoverability) → Reasoning-Domain Full Response Discovery → Template-Audited Continuous Signals → Sparse Cross-Domain Confirmation → Mixture Prediction and Recipe Selection

最终判断:S/R 探针保留为二级恢复性诊断;模板敏感性升级为正式准入审计;Phase 2 改为一个发现域全网格、两个确认域缩微,实验前冻结预算与停止规则。
