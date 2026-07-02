# LOOP1_RULINGS — 顾问裁决（2026-07-02）

> 对 `ledger/LEDGER_REPORT.md` 的裁决。硬停执行正确，账本闸门全过，验收通过。
> 但 §5 的"ability 税"解读**尚不能定案**：它与本仓库自己的 v4 transfer 结论存在未被引用的
> 正面张力（见 §1）。C-4 拆成两半：记账部分（C-4a）现在冻结；命名与论文主张部分（C-4b）
> 待 §2 判别实验后裁决。epoch-sweep 升级 Loop 1.5，批准。

---

## 1. 为什么"ability 税"还不能定案：一个未被引用的矛盾

报告 §5 的读法是：收敛 floor 训练**损坏了能力**（weights 层面，−52pp）。
但 v4 既有 transfer check 的结论是（[scenario-repair-v4] comparison_v4 系）：
**普通题上，作答时算术 ≈ base——底层计算没有被损坏**；漂移表现为"不作答"，不是"算错"。

这两个结论不能同时按字面成立。除非损坏是**条件性的**。因此有三个竞争假说，
第六类伪影叫什么、论文能主张什么，完全取决于哪个胜出：

- **H1 能力税（权重损伤）**：收敛训练真的破坏了算术权重。
  预测：floor 在同题的**素题模式**（无植入、无 repair schema）下也会掉到 ~44%。
- **H2 模式干扰（表达抑制）**：权重完好，但 repair-trace 模式在上下文里劣化了计算的表达
  （模型在写 trace 的体裁里算不好，换回素题体裁就恢复）。
  预测：floor 素题模式 ≈ base 94%，只在 corrupt+schema 体裁下 44%。
- **H3 选择/提取伪影**：matched 子集偏样（以 pre-repair resist∩parse 为条件 → 偏易题），
  或 scorer 从 repair trace 里提取 final 的方式与素输出不等价。
  预测：转录逐条看，"算对了但提取错/trace 烂尾"占比高。

三者对论文的含义完全不同：H1 = "收敛协议征收能力税"（协议伪影，重大发现）；
H2 = "SFT 改变的是表达模式而非能力，能力测量必须在素题模式下做"（测量学发现，
且直接改 Loop 2 的评测设计）；H3 = 账本自身的 bug（必须修）。
**三者都不推翻 D 渠道结论**（override +10.8 / recompute +14.1 在任何解读下幸存）。

## 2. 判别实验（按成本排序；T1–T3、T5 零算力，今天可做）

**T1【零算力，最先做】transfer 预测直读**：核对既有 3 个 transfer 预测覆盖哪些 ckpt。
若含 scaffold_conv：直接算它在素题上的作答准确率 vs base 94%。
≈94% → H1 出局；坍塌 → H1 成立。若 transfer 预测不含 scaffold_conv，把这一条 predict
列入服务器队列（与 pass@8 同批，一条命令）。

**T2【零算力】转录验尸 30 条**：取 matched 子集中"pre-repair 对、floor 错"的题各类抽样，
逐条人工分类：(i) 真算错（中间步算术错误）；(ii) 算对但提取错/final 不一致；
(iii) trace 烂尾/复读退化。(ii)+(iii) 占比高 → H3/H2；(i) 占比高 → H1/H2 待 T4 分辨。
30 条转录附在报告里，Xingwei 亲自过目。

**T3【零算力】选择偏差体检**：matched 子集 vs 全集的步数分布（KS 检验）与题长分布；
若显著偏易，报告按步数分层重算的 Δability。

**T5【零算力，堵住 A≤0 的镜像漏洞】**：matched 子集以 pre-repair 成功为条件，天花板效应
使它**只能看见损失、看不见增益**。补一个反向测量：在"pre-repair resist 但算错"的题集上，
各修复 ckpt 的答对率。若 ≈0 提升 → "A≤0" 主张补上另一半证据；若有提升 → 如实入账，
这是 A 渠道唯一可能藏身的角落，必须照过去。

**T4【一条服务器 predict，判决性】**：把 matched 子集中 floor 答错的题，以**素题形式**
（无植入、无 schema 要求）喂给 scaffold_conv 与 pre-repair 各跑一次。同题同模型双体裁对照：
素题恢复 → H2；素题同样错 → H1。此命令加入 RUNBOOK 与 pass@8 同批执行。

**判读表**（先约定判据再看数据）：
| T1 素题 acc | T2 主类 | T4 同题素题 | 结论 |
|---|---|---|---|
| ≈base | (i) | 错 | H1 能力税 |
| ≈base | (i) | 对 | H2 模式干扰 |
| ≈base | (ii)/(iii) | — | H3（先修账本）+ 部分 H2 |
| 坍塌 | (i) | 错 | H1 强成立 |

## 3. 裁决

**R-4（C-4a，冻结）双参照记账批准**：账本保留 vs 收敛 floor 的 A 列（记账一致性），
新增 vs pre-repair 的 A 列（能力主张判据列）。任何"能力被注入/被支出"的论文语句只允许
引用 pre-repair 参照列。csv 两列并存，脚注写明 matched n。

**R-5（C-4b，暂缓）第六类伪影的命名与主张**：待 T1–T5 出结果后定名
（H1→"convergence ability tax"；H2→"mode-interference measurement artifact"）。
在此之前，论文语言一律用中性描述"repair-mode ability 读数下降"，禁止写"能力被损坏"。

**R-6 epoch-sweep 升级 Loop 1.5，批准，并扩两条分析**：
(i) 补"repair-mode ability 读数 vs epoch"曲线（−5pp@3ep → −52pp@30ep 的中间点）；
(ii) 产出**规范 floor 选择规则**：canonical floor = 通过 parse≥0.95 闸门的**最小 epoch**。
这直接回答报告问题 1 的后半：Loop 2 的 floor 不再默认 30ep 或 8/8 教条，
而是"最小充分收敛"——F 伪影与 A 读数损伤是一对 trade-off，sweep 给出运行点。
这个 trade-off 本身写入 Artifact Taxonomy：**修 F 的协议会诱发 A 面的新伪影**。

**R-7 Loop 2 评测设计追加一个闸门（无论 H1/H2 谁胜出都需要）**：
每个训练后 ckpt 的 ability 测量必须**双体裁**——repair-mode（现行）+ 素题模式（同题无植入
无 schema）。素题列是能力主张的最终判据。Loop 2A/2B 的 eval 集生成时即配好素题孪生版。

**R-8 报告问题 3 批准**：补 factonly ckpt × v2.1 eval 的一条 predict，转 v2.1 七行为细账。
与 pass@8、T4 同批入 RUNBOOK（服务器一次跑三件事）。

**R-9 记忆核对（报告问题 2）确认**：(a) v3.1 ALL 净负 vs 对角线正，两口径并存无矛盾，
论文只引 per-cell + 声明 ALL 视角；(b) v2/v3 增益读作"格式门内混合增益"接受——
这条要写进《本账本推翻的旧结论》正式版。

## 4. 给 Xingwei（战略含义，不进 CC 执行范围）

无论 H1/H2 谁胜出，故事都变强了：
- H1：主标题 *No Free Ability* 字面成立还多送一层——能力不仅买不到，收敛协议还会**倒扣**；
  F-fix 与 A-integrity 的 trade-off 曲线（Loop 1.5 产出）是全新的方法学发现。
- H2：同样有力——"SFT 改写的是表达模式；在新模式里测能力会系统性低估"，这直接批评
  一大类修复评测的通行做法，且 R-7 的双体裁协议就是解药，论文自带可交付的修正方案。
- 最坏情况 H3 = 账本 bug，修掉后回到原命题，损失为零。
硬停机制这次证明了自己的价值：没有它，"+19 的 A"会被当成好消息写进论文，
然后死在任何一个复现它的审稿人手里。
