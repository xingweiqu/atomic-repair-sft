# CLAIMS — 论文级主张入册(C-11 三件套;入册前过四问)

> 四问:①推出来的还是起名的?②范围说大没?③自家数据有反例吗?④还有别的可能吗?
> 每条主张 = 范围三元组(域,条件,度量)+ 证据锚([branch] path)+ 邻居差分一行
> (与最像的已有主张差在哪)。

## 已入册

### CL-1 纠错决策策略可被少量对症数据持久安装
- 范围:(GSM corrupt-context, operator-only 配方 n≥300, resist@脊点)
- 证据锚:notes/NOTES_e1b.md(100% 持久,3-seed);notes/NOTES_datasize.md
- 邻居差分:非"SFT 数据高效"泛言——含 keep 剂量律反例(33% 掺料→无效)
- 四问:✅推出 ✅范围三元组限定 ✅反例=E1 混合池(已入正文) ✅另一可能=相变耦合(E1b 判别已排)

### CL-2 修复训练不注入底层算术能力(RescueEffect≈0),但 ≤3 步显式规则完全可教
- 范围:(GSM 算术 A_delivered/A_latent + Tier-2 OOD, 脊点 ckpt, matched/OOD 判据)
- 证据锚:ledger/master_ledger.csv(A 列);notes/NOTES_tier2_frontier.md
- 邻居差分:非"A 恒零"——tier-b/c/d OOD 95-100% 是自家反例,边界另有来源
- 四问:✅ ✅(四条 non-claim 兜底) ✅tier-2 即反例已并入主张 ✅弯点来源未决(如实)

### CL-3 决策与体裁(格式/作答意愿)在激活层可分离,决策可单卖(83→94%,不带税)
- 范围:(v4 floor e8, d_plain@L12, α≤16)
- 证据锚:notes/NOTES_steering_e5b.md
- 邻居差分:上限 94%<SFT 99-100%,非等价替代;权重层对齐 instrument-limited
- 四问:✅ ✅ ✅E5-v1 的税=自家反例(探针伪影,已判别) ✅

(新增主张按模板追加;未过四问不入册。)

### CL-4【待 F 补审后入册】格式约束本身劣化计算——体裁耦合在 pre-repair 模型先天存在
- 范围:(GSM8K test 1300, 同题受控配对 O vs F(仅输出格式改 JSON), pre-repair greedy)
- 证据锚:probes/out(F/gsm 76.7% vs O/gsm 93.5%,−16.8pp;验尸 303 miss 零提取器救回,
  295 错数值 + 8 表达式未计算[单列子模式])
- 邻居差分:**"format constraints 伤推理"有已知文献(Let Me Speak Freely 系)——本条记
  "受控复现 + 新联结",不记首创**;delta = ①逐题受控配对(同题仅改格式);②与修复训练
  安装体裁接成同一机制链:T4 的体裁耦合计算不是修复训练制造的,是**先天耦合被放大**(§5 升级)
- 四问:✅推出(验尸排除仪器) ⏳范围待 F 构念补审确认(双变体对照 20 条) ✅反例检查=
  hard 池 F/O 差动待分池复核 ✅另一可能=提取器不等价(已验尸排除)
- 状态:**审计判决=双重记账**(F_judge 测量角色保留 + 独立失败类);入册待 F 补审通过

## 修正记录

### COR-1(2026-07-10,Loop 3 Batch-1 裁决 ⑤)
**被替换假设**:"修复率 ≈ 组分与桶的匹配度"(PREREG_loop3 预测表的隐含模型,
conduct .95 / rule .90 / format .60 / phrasing·scaffold .50± / drills≈0)。
**替换为**:"高非特异地板 + 特异信号稀少"——素题体裁下 cleanreplay 安慰剂即达
conduct 桶 73%(与 steering placebo 75% 双仪器互证);5 桶中仅 format 存在
配方特异修复(+70~79pp);drills 为主动危害(W_adopt 25%)非中性。
**战绩**:2 HIT / 1 方向 HIT / 3 MISS(判定页 prereg/ADJUDICATION_loop3_batch1.md §3)。
**影响面**:CL-1 不受伤(修复腔/E1b 体裁,对症性在该体裁下仍成立);
"诊断指导数据设计"的候选主张改走"组分存废 + 毒性剔除 + 地板效应"表述,
入册待 B2-0 体裁对账(qc/LOOP3_RULINGS_batch1_verdict.md ②b)返回。
