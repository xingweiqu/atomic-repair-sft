# CC 指令 v2：Gain Accounting（FMDA）—— Loop 工程版

> 【固化说明】本文件为顾问 v2 指令逐字存档(2026-07-01/02 由 Xingwei 在会话中提供)。
> §A 口径附录 = qc/INSTRUCTION_v1.md §1,冻结。

> 取代 v1。故事定义、四渠道口径、分解恒等式与 v1 相同（附在文末 §A，勿改动口径）。
> v2 的变化：整个项目改为 **Loop 结构**，每个 Loop 有入口条件、自检闸门、验收报告；
> 新增 **Loop 0 资产质检**（对齐"指令假设的"与"仓库实际的"）；
> 明确 **分工协议**：CC 本地做盘点/生成/质检/评分/写代码/push；训练在 Xingwei 的服务器，
> CC 的交付物必须做到 **pull 下来不改一个文件就能跑**。

---

## 工作模式（先读三遍）

1. **Loop 纪律**：每个 Loop = 入口条件 → 执行 → 自检闸门 → 输出 `qc/LOOP{n}_REPORT.md` → Xingwei sign-off → 才进下一个 Loop。禁止抢跑，禁止跨 Loop 合并提交。
2. **不脑补原则**：本指令中任何关于仓库现状的描述都是"顾问的假设"，不是事实。凡与仓库实际不符：停，记入 `qc/DISCREPANCIES.md`（写清：指令假设了什么 / 实际是什么 / 影响哪个后续 Loop / 建议方案），等裁决。**禁止为了让流程走通而悄悄替换口径。**
3. **可追溯**：每个数字、每个结论标 `[branch] path:line`（沿 SETTING.md 格式）。
4. **硬停条件**（任何 Loop 中触发即停 + 报告，不许自行圆故事）：
   干净测量中 A 显著非零；账本 residual > 3pp 且无解释；泄漏检测在"应为零"的数据上非零；预注册预测未命中。

---

## Loop 0 — 资产质检（Assumption Audit）【零算力，最先做，1–2 天】

**目的**：后续所有 Loop 都要复用旧资产。先逐项核对顾问的假设 vs 仓库现实，防止"想象的管线"和"实际的管线"是两套东西。

逐项核对下表，每项给证据路径与结论（✅ 符合 / ⚠️ 部分符合需适配 / ❌ 不符）：

| # | 指令的假设 | 需核实的问题 |
|---|---|---|
| A1 | 存在最终版 strict judge（含 abstain 修正） | 是哪个文件？ERRATUM 修正是否已合并进主评分路径？能否同时以 lenient / strict 双模式重评同一份预测（F 渠道需要）？ |
| A2 | v0–v5 各 run 的**预测 JSON 原文件**仍在 | 逐 run 列清单：有原文件（可重评入细账）/ 只剩汇总 md（只能入粗账）。 |
| A3 | `bprime/leakage_audit.md` 的泄漏规则可脚本化、可输出 per-item leak 标记 | 现在是文档还是可执行代码？三元组重叠规则能否泛化到 GSM 数值/模板重叠？ |
| A4 | resist / ability 判定与 matched-subset 逻辑已有实现 | 是成型代码还是散在分析笔记？matched-subset 的交集口径与 v1 §1.1 是否一致？ |
| A5 | v3 合成运算符生成器可参数化改造为"可调可学性家族"（Loop 2B 的地基） | 生成代码在哪？运算符定义是数据文件还是硬编码？操作数范围可否参数化（OOD 切分需要）？ |
| A6 | epoch 对等（8/8）与收敛闸门（parse≥0.95）有现成 config 模板 | `configs/v4/epoch_sweep/` 现状？v5 的 8/8 协议 config 在哪？ |
| A7 | 底模型确切型号（SETTING UNVERIFIED #3） | Base 还是 Instruct？给出 config 级证据。**此项不关闭，Loop 3/5 不得启动。** |
| A8 | v4 GSM 资产可复用：Corrupt 注入器、eval 集、base pass@k 缓存 | pass@k 有无缓存？没有则 Loop 2A 需先补测（列入服务器任务）。 |
| A9 | v5 逐行超参（SETTING UNVERIFIED #5） | 顺手关闭。 |

**产出**：`qc/ASSUMPTIONS_AUDIT.md`（上表逐项）+ `qc/DISCREPANCIES.md`。
**闸门**：❌ 项全部有 Xingwei 裁决后，Loop 1 才开。

---

## Loop 1 — 账本重建（零算力）

**入口**：Loop 0 sign-off。
**内容**：v1 的 Phase 0 原样执行——盘点 → 统一 strict judge 重评（A2 中有原文件的 run）→ per-item 泄漏标记 → 按 §A 四层记账。
**产出**：`ledger/inventory.md`、`ledger/master_ledger.csv`、`fig_ledger.png`（四色堆叠条）、`ledger/LEDGER_REPORT.md`。
**闸门**：覆盖 ≥90% 历史 run；每行 residual <3pp 或有解释；只剩粗账的 run 显式标灰。
**给 Xingwei 的验收问题**（写进报告结尾）：账本上哪几笔与你记忆中的数字不一致？——这些不一致优先当作质检信号处理，而非直接改账。

---

## Loop 2 — 数据工程（三个子 Loop，每个都是 generate → gate → audit → sign-off）

**入口**：Loop 1 sign-off（账本决定还缺什么数据；若 Loop 1 推翻主命题，本 Loop 设计要重议）。
**通用规则**：每个子 Loop 交付时附 (i) 闸门自检报告 (ii) 100 条分层抽样的人工抽检模板（含题面/gold/植入值/leak 标记/桶或档位），Xingwei 抽查通过才算 sign-off。数据一律带 `dataset_card.md`（生成参数、闸门结果、体量、切分定义）。

### Loop 2A — Tier 1：GSM 按 base 能力分桶（真实域脊柱）
- base per-item pass@8 → 4 桶：[0–25], (25–50], (50–75], (75–100]%。pass@8 若无缓存（A8），先产出服务器测量任务并入 RUNBOOK。
- 桶间 **推理步数分布须报告 KS 检验**；不平衡则做步数 matched 采样，或将步数登记为协变量（防"缺口效应"被"难度效应"顶替）。
- 体量：每桶 eval ≥500（matched-subset 预算后 ≥300）、train 1–2k；Corrupt 注入沿 v4 注入器。
- 闸门：泄漏检测阴性（阴性对照入账本）；植入错值 type-match；注入前后 gold 不变的程序化校验。

### Loop 2B — Tier 2：可调可学性运算符家族（本论文的核心新数据资产）
基于 A5 的生成器改造，四个档位 + OOD 切分：
- 档位 **a** 纯查表（无规则，仅有限对定义）｜**b** 单步规则（如 a⊕b=a+b+1）｜**c** 两步组合｜**d** 三步组合。
- **OOD 切分（M/A 的设计级分离，最重要）**：train 操作数 ∈[0,99]；eval-ID＝同范围**未见组合**；eval-OOD＝[100,999]。见过组合上的增益记 M，未见/OOD 上的增益才有资格记 A。
- 闸门：干净闸门（base zero-shot ≈0，逐档报告）；gold 由生成器程序保证（生成器即 oracle）；给出"构造性零泄漏"的证明脚本（train/eval 组合集合交集=∅ 的断言测试）。
- **校准品（审计仪器的标定，随本 Loop 一并产出）**：
  - M 校准：三份毒数据，蓄意向 train 泄漏 eval 答案 0% / 10% / 30%，用于验证账本 M 读数随已知剂量线性；
  - F 校准：欠拟合 floor config（对齐旧 3ep/loss2.53 形态）正式收编为 F 阳性对照。
- 体量：每档每切分 eval ≥500，train 2k；全部程序化生成。

### Loop 2C — Tier 3：预注册域筛选
- 候选：日期/日历推理、单位换算应用题、简单代码 bug 定位。写一个筛选脚本：测 base ability 是否落 30–70%、Corrupt 是否可程序化注入，输出对比报告，**由 Xingwei 拍板选域**（CC 不自选）。选定后数据走 2A 同款闸门。

---

## Loop 3 — 训练代码与 push（交付服务器）

**入口**：Loop 2 对应子集 sign-off + A7 关闭。
**内容**：
1. 新分支 `gain-accounting-v1`：LLaMA-Factory configs（沿 SETTING：全参 SFT、ZeRO-3、lr 1e-5、bf16、cutoff 1024、seed 42；**floor 与 targeted epoch 严格对等**；headline 条件加 seed 43/44）、predict 脚本、结果打包脚本。
2. `RUNBOOK.md`：服务器端逐条命令——pull → 逐 config train → predict → 打包预测 JSON 回传的确切路径。按"复制粘贴即可跑"标准写，含每步预期产物与失败自查点。
3. 本地 scorer / ledger / dose-response 分析脚本：先在**伪造小样本**上跑通单测（dry-run 报告入 qc/），保证服务器结果回来当天可出图。
4. **预注册**：Tier 3 训练 config 提交前，`prereg/PREREGISTRATION.md` 必须先单独 commit（预测式：ΔfinaI ≤ (0.99−resist₀)×ability₀ + 0，代入实测 base 数），commit hash 即时间戳；RUNBOOK 中 Tier 3 的训练命令注明"仅在该 commit 之后执行"。
**闸门 / 验收标准**：Xingwei 在服务器 `git pull` 后**不修改任何文件**即可按 RUNBOOK 顺序执行。做不到即打回。

---

## Loop 4 — 回收与记账（服务器结果回传后）

- strict 评分 → 四层记账入主账本 → 产出：`fig_dose_response.png`（Tier 1 四桶 + Tier 2 四档两条主线：D 增益 vs 缺口、A vs 缺口，叠 v3/v5 端点锚，v3 标"M 污染仅示意"）、校准品验证图（M 读数 vs 已知泄漏剂量）、预注册命中报告。
- epoch-sweep（既有 pending）结果并入：D 低 epoch 到账、A 全程平。
- 产出 `qc/LOOP4_REPORT.md`：主命题在新数据上的存活状态 + 论文各 section 的图表落位清单。

---

## Loop 5 — Steering vector（独立支线，Loop 2 起可并行，单卡零训练）

按 v1 Phase 3 执行（成对样本≥200/类、逐层扫描、α 曲线：resist / matched ability / 普通题退化）。
入口条件仅 A7（底模型确认）。产出 `steering/REPORT.md` + `fig_steering.png`。

---

## §A 口径附录（与 v1 相同，冻结）

- 渠道定义、F/M 前置闸门 + D/A Shapley 分解恒等式、`F+M+D+A+residual=Δfinal_raw`（residual<3pp）、
  matched-subset 口径、v3 的 A 列标"上界，受 M 污染"——全部沿 v1 §1，此处不再重复；如需修改口径，先提案后冻结，禁止执行中漂移。
- 论文骨架沿 v1 §6；新增：§3 增加"校准品标定"小节；§4 的 x 轴由 Tier 1 桶 + Tier 2 档共同构成；
  附录新增《9 格尸检》：用 v3/v4 transfer matrix 聚类展示手画分类在干预结构下的坍缩（零算力，Loop 1 后即可做）。
