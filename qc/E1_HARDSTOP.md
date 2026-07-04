# E1 硬停报告(2026-07-06)— 与 PREREG_datasize 矛盾 + mute 波发现

> 触发条款:硬停 = 与当期冻结预注册矛盾。按纪律停下报告,不圆故事、不自行改设计。
> 全部数字:notes/NOTES_datasize.md(含全网格 mute/answered-acc 列)、notes/NOTES_seeds.md。

## 1. 预注册判定

| 预测 | 判定 | 事实 |
|---|---|---|
| P1 targeted N≤300 到位(resist≥0.95 ∧ 零出血) | **❌** | 冻结闸门(parse+json_bleed)选出的脊点 resist 95–96%(n300)/75%(n100)——但这些点全部落在 **mute 波内**(素题哑火 49–82%);换 mute-aware 闸门后健康点 resist **60–83% ≈ floor 83%**,无增益 |
| P2 random 不稳定(0.4–0.95) | ✅ 但空洞 | random 与 targeted-mixed 在每个 N 都相当(74–89% vs 60–83%)——"targeted 赢 random"不成立 |
| P3 素题 acc 平(92±5) | **❌(按字面)/ ✅(按本意)** | 字面失败源于 mute 波;**answered-acc 全网格 88–100%**——只要作答算术无损,"能力不变"的本意成立,是预注册选错了度量 |

## 2. 核心发现:mute 波,及 resist 与它的耦合

- **mute 是一个随 N 前移的瞬态波**:n100 峰在 e8(82%)、n300 在 e4(49–51%)、n1000 前移出窗、
  波过即恢复(n100@e16 mute 9%、素题 acc 90%)。bleed(json 入侵)是另一条独立的后期上行线。
- **混合池的"resist 增益"与 mute 波同相**:波内 resist 95%+素题哑火;波过 resist 退回 ≈floor。
  疑似同一相变(repair 体裁短暂支配一切输入),不是被安装的决策。
- **对照组反例(单 operator,来自 sweep+E3)**:targeted_override 660 条,resist 在 e2 翻到 1.00
  后**稳定保持 0.98–0.99 直到 e30**(健康点 e3:plain 91%/mute 6%/resist 0.99),
  **3-seed 99/100/100**;recompute@e3 三种子 93–99%。→ 决策可以被持久安装,但 E1 的配方装不上。

## 3. 机制候选(留给裁决,不自证)

- **H-稀释**:targeted-mixed 池 33% 是 keep_answer(n300 子采样 31%)——三分之一训练在教
  "别改答案",resist 锁不住。
- **H-相变耦合**:混合训练里 resist 升高只是 repair-支配相的副作用,随相消退;
  纯 operator 数据才把决策写进权重(与 §4 方向假说一致,可被 E5 steering 对齐分析检验)。
- 两者不互斥。**判别实验提案 E1b(待批)**:operator-only 混合池(4 op 均匀、无 keep/abstain),
  同 N 网格重跑——池文件现成(per_policy/*),零新数据工程。

## 4. 协议修正提案(待裁决)

- **C-9(闸门)**:脊点闸门增加第三条件 **excess-mute ≤ 5pp**(mute ≤ base 底噪 7%+5%)。
  R-16 当时把 mute 排除在 gate 外;E1 表明 parse+json_bleed 闸门会把运行点选进 mute 波。
- E3 连带更正:targeted_override 的脊点在 C-9 下应从 e2 移到 **e3**(e2 在波内:mute 75%)。
  e3 处 resist 0.99 不变,结论不受损,但运行点要改。
- 预注册方法论教训(入 taxonomy 叙事层):P3 用了"全分母 acc"当能力度量,把 mute 混进了
  能力读数——正确度量是 answered-acc(或 matched)。预注册的**度量选择**本身要预注册。

## 5. 对 BIG_PICTURE §3 的影响(等 Xingwei 裁决,不自行改主图)

- "**省**"(targeted 数百条即到位)目前证据:**单 operator 配方成立**(660 条,3-seed,
  resist 0.99 持久);**混合配方不成立**(≈random≈floor)。
- §3 红线 2 说对照=targeted vs random——E1 实测两者无差(混合配方下)。主图配方需要拍板:
  (a) 换 operator-only 混合(E1b 判别后);(b) 主图改用单 operator 证据链(sweep+E3 已有);
  (c) 承认混合配方无效并如实写。
