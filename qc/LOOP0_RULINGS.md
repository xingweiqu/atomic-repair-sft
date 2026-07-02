# LOOP0_RULINGS — 顾问裁决（2026-07-02）

> 对 `qc/ASSUMPTIONS_AUDIT.md` 与 `qc/DISCREPANCIES.md` 的逐项裁决。
> 本文件裁决的口径修正（§2）自本文件 commit 起冻结，并入 §A 口径附录。
> 结论先行：**审计通过。D-3/D-4/D-1 按下述裁决执行；Xingwei 侧只欠 D-6 一条命令 + D-7 确认；
> Loop 1 在 §3 的三条补充范围规则并入后开工。**

---

## 1. 逐项裁决

**D-1（v1 误跑预测）→ 采纳方案 (b)，但改记账方式。**
v1 四行入账本、整体标灰 `misfired, lineage unverified`，**不参与任何聚合统计与主图**；
在 Artifact Taxonomy 中立为第五类混杂：**Provenance（谱系）伪影**——跑的不是你以为的管线/ckpt。
这一类与 F/M/D/A 平行（它污染的是 run 的身份而非增益的渠道），恰好补全 taxonomy：
F=判定伪影、M=数据伪影、Provenance=执行伪影、epoch=协议伪影。

**D-2（judge 双档包装）→ 批准，加一条约束。**
strict = 合法 JSON 含 `final_answer` + `is_abstain_strict`；lenient = 现行 fallback 链 + `update_value` 兜底。
约束：包装层必须带回归测试——对 3–5 个历史 run 用新包装的 lenient 档重评，数字须与历史报告
一致（容差舍入），证明"只封装、未改判定"。不一致即停。

**D-3（恒等式闭合口径）→ 批准提案，冻结为口径修正 C-1（见 §2），加两条澄清。**
(i) parsed 子集口径必须**对称**作用于比较的两端（floor 与 targeted 各自的 unparsed 都记 F），
禁止只剥一端。(ii) **abstain 不是 F**：strict judge 能解析出 abstain 的输出属于 parsed，
在 D/A 层内处理（abstain ⇒ 输出≠植入值 ⇒ resist=1、ability=0）。只有真正不可解析的输出才记 F。
这条很关键——否则"教会弃答"会被误记成"格式伪影"。

**D-4（交集口径双轨）→ 批准，加一条门槛。**
账本两两比较用 pairwise（照 §1.1）；epoch/剂量多点曲线用 fixed-all，脚注报 n。
新增门槛：任何 A 项若 `n_matched < 50`，该格标灰"低功效"，不得用于支持或反驳 A≈0 主命题。

**D-5（leak 标记 + GSM 规则）→ 批准，扩一条范围（重要，见 §3-R2）。**

**D-6（底模型）→ 待 Xingwei 跑命令。** 但现在就要预告后果：若确认为 Instruct（证据已很强），
论文中所有 "base 的预训练倾向（采信上下文断言）" 措辞必须降级为 "修复前模型的默认行为"——
resist₀=0.6 可能部分来自 instruct 调优而非预训练，这不伤主命题（账本不关心倾向来源），
但措辞错了会被审稿人抓。全文统一用 **pre-repair model**，不用 base/pretrained 指代该 ckpt。
Loop 5 的方向提取同理：提的是 pre-repair 模型的方向。

**D-7（pass@8 前置测量）→ 批准。** 补三个规格：
(i) 先 500 题试跑标定桶边界，再全量 1319；
(ii) 采样温度按 Qwen3 官方推荐、固定并写入 dataset_card；
(iii) 明确角色分工：pass@8（采样）只做**分桶变量**；修复评测本身沿历史口径 greedy 单次，
两个 inference regime 不混用，card 里写明。

**D-8（parse 闸门脚本）→ 批准。** gate 脚本除 exit 1 外须打印失败 run 的 parse_rate 与
最近一次 loss，方便服务器端一眼定位是欠拟合还是模板错。

**D-9（运算符四档家族）→ 批准新建 `learnability_family/`，加一条硬闸门。**
三位数 OOD + 多步 trace 的 token 预算：数据闸门中增加 **token 长度审计**——报告每档
prompt+target 的 p95 token 数 vs cutoff 1024。超限的解法优先级：精简 trace 措辞 > 提高 cutoff。
若必须提高 cutoff，则本项目全部新 run 统一同一 cutoff，并在账本中把"与历史 run cutoff 不一致"
登记为脚注（不做跨 cutoff 的直接横比）。同理沿用 `template: qwen` 不升级——审计里这条抓得好。

---

## 2. 口径修正（自本文件起冻结，并入 §A）

**C-1（源 D-3）**：第 1 层剥 F 后，`resist` 与 `ability` 定义在 parsed 子集上；unparsed 全额记 F，
对称作用于比较两端；abstain 属 parsed，在 D/A 层内处理。恒等式在第 3 层作用域内精确闭合。

**C-2（F 渠道双分量）**：审计暴露了 v1 口径的一个含糊处，现予明确。F 分两个可分别报告的分量：
- `F_judge` = 同一预测文件 lenient − strict 的差（判定伪影）；
- `F_floor` = 以欠拟合 floor 为基线的增益 − 以收敛 floor 为基线的增益（基线伪影）。
账本的**规范基线 = 收敛 floor（parse≥0.95）**；凡历史比较用了欠拟合 floor 的（scaffold_only 等），
其与收敛基线的差额记入 F_floor。两分量在主图中可合并为 F 一色，csv 中分列。
（原 +93/+98 伪增益主要是 F_floor，不是 F_judge——不明确这一点，Loop 1 会把 F 记漏。）

**C-3（源 D-4）**：pairwise / fixed-all 双轨 + n_matched≥50 门槛，如 §1-D-4。

---

## 3. CC 未提出、但 Loop 1 中途必然撞上的三条范围规则（现在就并入）

**R-1 恒等式的适用范围**：`final = resist × ability` 只对 **Corrupt 型、每题携带 (gold, 植入值 w) 对**
的 run 成立。历史账目里 v2/v2.1 的很多条件（CoT 变体、Skill+CoT、知识注入对照、Aug/Abl 型 cell）
**没有 (g,w) 结构**，D/A 分解对它们无定义。规则：账本增加 `decomposable` 布尔列——
可分解的 run 走全四层；不可分解的 run 只记 F/M 两层 + Δfinal_clean，D/A 列填 N/A。
禁止为了填满表格而给无 w 的 run 造一个"伪 resist"。

**R-2 M 层的训练暴露定义（针对 v3 谱系）**：v3 系列 relay 自 v2 inject ckpt（base + 50ep 事实注入）。
因此 v3 的 `leak(i)` 判定中，"训练集"必须 = **repair-SFT 训练集 ∪ 注入语料**，两者任一含该三元组
即 leak=1。只查 repair train 会系统性低估 M（79.4% 那个数需核对口径：它对照的是哪个集合，
在 leak_flags 输出里分列 `leak_sft` / `leak_inject` / `leak_any`，账本用 leak_any）。

**R-3 账本行粒度**：一行 = (ckpt, eval 条件/cell)，不是一行一个 ckpt。
v3 的 6 operator × {targeted, random, wrongtarget}、v4 的 23 个条件各自成行；
主图可再做聚合视图，但 csv 保持最细粒度，否则《9 格尸检》与 transfer 聚类没有原料。

---

## 4. Loop 1 开工条件（更新后）

1. 本文件 commit（口径 C-1/C-2/C-3 + 范围 R-1/R-2/R-3 生效）；
2. Xingwei 跑 D-6 命令并把输出贴回（此项只门禁 Loop 3/5，**不阻塞 Loop 1**——Loop 1 零训练零加载）；
3. D-7 服务器任务确认排期（同样不阻塞 Loop 1）。

即：**本文件入库后 Loop 1 立即可开**。Loop 1 交付时，LEDGER_REPORT 末尾按 v2 指令回答
"哪几笔与 Xingwei 记忆不符"，并新增一节：R-1 判定下 decomposable=false 的 run 清单及占比
（若过半，主图叙事要调整为"可分解子集上的四渠道 + 全集上的 F/M 两渠道"双图）。
