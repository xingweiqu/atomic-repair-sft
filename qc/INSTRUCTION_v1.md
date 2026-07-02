# CC 指令：Gain Accounting（FMDA）—— Paper 2 主线重构

> 【固化说明】本文件为顾问 v1 指令逐字存档(2026-07-02 由 Xingwei 在会话中提供)。
> v2 指令(qc/INSTRUCTION_v2.md)的 §A 口径附录即本文 §1,冻结,禁止执行中漂移。

> 角色：你是本项目的执行工程师。仓库 `atomic-repair-sft`，分支 v3=`scenario-repair-v3-targeted-operators`、
> v4=`scenario-repair-v4`、v5=`scenario-repair-b-prime`。所有训练在服务器（LLaMA-Factory 全参 SFT），
> 本地只做生成/验证/评分/分析。本指令定义新主线：**把"修复训练的涨分"按四个渠道记账**。
> 执行顺序严格按 Phase 0 → 1 → 2 → 3；Phase 0 不花算力，先出账本再决定后续。

---

## 0. 故事定义（写任何代码前先读懂这一节）

**研究问题**：微调（repair SFT）带来的涨分到底从哪来？

**核心命题（可证伪）**：在我们的受控实验中，全部增益可被以下四渠道完全解释，且能力项 ≈ 0：

| 渠道 | 定义 | 本项目中的既有证据 |
|---|---|---|
| **F** Format | 学会输出格式/通过解析 | 欠拟合 floor 伪增益 +93/+98，收敛后消失 |
| **M** Memorization | 背下了 train 中出现的答案 | v3 泄漏（79.4% 三元组重叠）→ ability=1.00 是背表 |
| **D** Decision | 行为倾向被翻转（如拒绝植入错值） | v3/v4 均可教：resist 0.6→0.99 |
| **A** Ability | 真正学会了 base 不会的本事 | 所有干净测量中 ≈ 0（ability\|resist flat ~0.35） |

**交付物**：(1) 一张主账本表（每个历史 run 的增益四渠道分解）；(2) 一份"增益审计协议"
（任何"我修好了模型"的宣称如何验账）；(3) D 渠道剂量-响应曲线 + A 恒零平线；
(4) 一次预注册预测（事前写下增益上限，再训练验证）；(5) steering vector 机制证据（D 渠道 = 表征中的一个方向）。

**叙事纪律**：论文按定律体写（先命题、每节一条证据链），不按编年体写。三次勘误
（floor / 泄漏 / abstain judge）统一收进附录《Artifact Taxonomy》，正文只以"F/M 渠道的鉴定实验"身份出现。

---

## 1. 口径与恒等式（所有数字必须服从这一节）

### 1.1 测量定义

对 Corrupt 型任务（题面植入错值 w，gold 为 g），每题记录三元组（g, w, model_output）：

- `parse` = 输出可被 strict judge 解析出 final_answer（布尔）
- `resist` = final_answer ≠ w（决策层）
- `ability` = 在 resist=1 的子集内 final_answer == g（能力层，**分母必须是 matched-subset**：
  比较两个 checkpoint 时用二者共同 resist 成功的题目交集）
- `leak(i)` = 题目 i 的答案支撑（三元组/事实/数值组合）出现在训练集（布尔，规则见 1.3-M）

### 1.2 分解恒等式（账本的数学骨架）

由于 not-resist 时输出=植入错值≠gold，故 `final_acc = resist × ability|resist`。
两 checkpoint（floor→targeted）之间的增益用对称（Shapley）分解：

```
Δfinal = Δresist · (ability₀+ability₁)/2   ← D 渠道入账
       + Δability · (resist₀+resist₁)/2    ← A 渠道入账
```

F 与 M 作为**前置闸门**逐层剥离，而不是加法项：

```
第0层  原始增益 Δfinal_raw（宽松 judge，全量题）
第1层  strict-parse 重评 → Δfinal_strict；差额记入 F
第2层  剔除 leak=1 子集 → Δfinal_clean；差额记入 M
第3层  对 Δfinal_clean 应用 1.2 恒等式 → 拆成 D 与 A
```

**验收规则**：每个 run 必须报告 `F + M + D + A + residual = Δfinal_raw`，residual 需 < 3pp 并解释来源。

### 1.3 各渠道的操作化测量

- **F**：同一预测文件分别用 lenient judge 与 strict judge（v3.1 修复后的版本，含 abstain 修正）打分，差值即 F。
  另报 parse_rate 与 training loss 作为欠拟合旁证（阈值沿用：parse < 0.95 即标记 floor 不合格）。
- **M**：复用并泛化 `bprime/leakage_audit.md` 的规则——v3 域：eval 三元组 ∈ train 三元组集合即 leak=1；
  GSM 域：最终数值+关键中间值组合的 n-gram 重叠 + 同题模板检测。输出 per-item leak 标记文件。
- **D**：Δresist（targeted vs floor，epoch 对等条件下）。
- **A**：matched-subset Δability。**注意 D-19(c)**：v3 的 matched ability 仍受泄漏污染，
  账本中 v3 的 A 列必须标注"上界，受 M 污染"，干净 A 证据仅来自 v4/v5。

---

## 2. Phase 0 — 零算力：历史数据全部入账

**目标**：不跑任何训练，把 v0–v5 所有既有 (run, condition) 的增益按上述四层记账。

步骤：

1. **盘点**：扫描各分支的 `comparison_*.md` / `REPORT_*.md` / 预测 JSON，产出
   `ledger/inventory.md`——每行一个 run：分支、ckpt、epoch、eval 集、judge 版本、预测文件路径。
   缺预测原文件而只有汇总数字的 run 单独标记（这些只能入"粗账"）。
2. **重评**：对有预测文件的 run 统一用最终版 strict judge 重跑评分（保证全账本同一把尺）。
3. **泄漏标记**：对 v3 全部 eval 题生成 per-item leak 标记；GSM 域跑重叠检测（预期 leak≈0，作为阴性对照写入账本）。
4. **出账**：`ledger/master_ledger.csv`，列：
   `run_id, domain, floor_type, epochs, Δfinal_raw, F, M, D, A, residual, notes`。
5. **主图**：`fig_ledger.png` —— 每个 run 一根堆叠条（F/M/D/A 四色），
   预期视觉结论一眼可读：v3 的条大部分是 M+D，v4 的条几乎全是 D，A 色在所有条中 ≈ 0。
6. **报告**：`ledger/LEDGER_REPORT.md`，含每笔账的出处（[branch] path:line，沿用 SETTing.md 的可追溯格式）、
   residual 解释、以及一节《本账本立即推翻/支持的旧结论清单》。

**Phase 0 验收（DoD）**：master_ledger 覆盖 ≥ 90% 历史 run；每行 residual < 3pp 或有解释；
fig_ledger 中 A 通道在所有干净测量中 |A| < 2pp。若 A 显著非零 → 停下，向 Xingwei 报告（这将改写主命题）。

---

## 3. Phase 1 — 剂量-响应：D 曲线与 A 平线（约 1–2 轮训练）

**目标**：把 v3/v4 两个端点变成一条曲线：x = base 能力缺口，y = 可入账的 D 增益；A 全程为零。

设计：

1. **分桶**：对 GSM8K（或 GSM-hard/MATH 子集混入以拉开难度），先用 base 模型测 per-item pass@8，
   按 base ability 分 4 桶：[0–25%], (25–50%], (50–75%], (75–100%]，每桶 ≥ 300 题（eval ≥ 100/桶）。
2. **注入**：每桶按 v4 流程注入 Corrupt 扰动（植入错中间值），构造 targeted 训练集与 eval。
3. **控制变量**：floor 与 targeted epoch 严格对等（沿 v5 的 8/8 协议）；收敛闸门 parse ≥ 0.95；
   泄漏检测跑一遍（预期阴性）；seed 42，headline 桶补 3 seed。
4. **产出**：`fig_dose_response.png` —— 两条线：
   D 增益 vs base 能力缺口（预期单调上升后饱和），A vs 缺口（预期全程 ≈ 0 的平线）。
   同图叠加 v3（缺口=100%）与 v5（缺口=0%）作为两端锚点，v3 点标注"M 污染，仅示意"。

**判读**：单调 → 命题升级为定量律"可入账增益 = f(决策缺口) 且 A=0"；
非单调/A 非零 → 如实报告，这是边界发现而非失败。

---

## 4. Phase 2 — 预注册预测（1 轮训练，封顶石）

**目标**：证明账本有预测力，不只是事后解释。

1. 选一个未碰过的新域（候选优先级：a. 单位换算类应用题；b. 日期/日历推理；c. 简单代码 bug 定位。
   选择标准：base ability 可测且落在 30–70%，Corrupt 扰动可程序化注入，与既有域结构不同）。
2. **训练前**测 base 的 resist₀ 与 ability₀，按 1.2 恒等式**写下预测**：
   `预测 Δfinal ≤ (0.99 − resist₀) × ability₀ + 0`（D 封顶 0.99 取自 v4 经验值，A 项预注册为 0）。
3. 将预测写入 `prereg/PREREGISTRATION.md` 并 git commit（commit hash 即时间戳），然后才允许开跑训练。
4. 训练→评测→按四层记账，报告预测区间命中与否。

**判读**：命中 → 摘要里可写"the ledger predicts"；未命中 → 分析哪个渠道超预算（最可能是 M 或 F 漏检），
这本身是审计协议的案例研究。

---

## 5. Phase 3 — Steering Vector：D 渠道的机制身份证（零训练，单卡）

**目标**：证明 D 渠道之所以便宜可注入，是因为它在表征空间里近似一个方向。

1. 工具：nnsight 或 TransformerLens 加载 base（确认底模型确切型号——这是 SETTING #3 的 UNVERIFIED 项，先补）。
2. 样本对：从 v4 base 预测中取 resist=1 与 resist=0 的题各 ≥ 200，在植入错值 token 之后的位置取残差流激活，
   difference-in-means 得到候选方向；逐层扫描。
3. 干预：推理时按系数 α 加方向，测三条曲线 vs α：resist、ability|resist（matched）、普通题 acc（退化检查）。
4. **判读**：若存在 (layer, α) 使 resist ≥ 0.9 且 ability 平、普通题不退化 → "targeted SFT ≈ 一个方向"，
   D 渠道获得独立于训练管线的机制证据（免疫泄漏/floor/epoch 全部混杂）；
   若推不动 → 报告"D 非线性可控"，同样入论文（机制边界）。
5. 产出：`fig_steering.png` + `steering/REPORT.md`。

---

## 6. 论文骨架（定律体）

- **标题方向**：*Where Do Fine-Tuning Gains Come From? A Gain Accounting for Repair Training*（备选 *No Free Ability*）
- §1 引言：修复训练的通用实践 → 涨分≠修好 → 四渠道命题 + 审计协议预告
- §2 口径与恒等式（本指令 §1）
- §3 证据一：账本（Phase 0 主表主图；F/M 的两次鉴定实验即原勘误，以正面身份出现）
- §4 证据二：剂量-响应（Phase 1）
- §5 证据三：预注册预测（Phase 2）
- §6 证据四：机制（Phase 3 steering + epoch-sweep 的"D 低 epoch 到账、A 恒零"）
- §7 讨论：与 superficial-alignment / SFT-as-elicitation / Physics-of-LLM 知识注入的关系；
  对实践的三层处方（Access→prompt；Decision→轻量注入；Ability→换模型或接工具）
- 附录：Artifact Taxonomy（floor/泄漏/judge/epoch 四类混杂：触发条件+检测方法+本项目案例）、SETTING、全部账目出处
- **与 Paper 1 的接口**：Paper 1 产出诊断（哪个 capacity 坏）→ 本文产出账本（修它能买到什么）；
  9 格降级为"初始探针集"，capacity 的原子性由干预传递结构定义（transfer matrix 聚类作为 §3 的支撑分析，
  用 v3/v4 既有 transfer 数据直接跑，零算力）。

---

## 7. 执行纪律

1. Phase 0 完成并经 Xingwei 审核前，不启动任何训练。
2. 一切数字可追溯：`[branch] path:line`；judge 版本、seed、epoch 写入每张表的脚注。
3. epoch-sweep（既有 pending）照跑，结果并入 §6 而非独立章节。
4. 遇到 A ≠ 0、residual > 3pp、预注册未命中三种情况：停、报告、不自行圆故事。
5. 待补齐的 SETTING UNVERIFIED 项（底模型型号、v5 超参）在 Phase 0 期间一并解决。
