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

### CL-2 修复训练不注入底层算术能力(RescueEffect≈0);显式规则在 ≤5 步、含分支、含语言包装范围内全部可教【2026-07-12 ★3 升级】
- 升级句(定稿):GSM 域内 A≈0 **不是**链深、控制流、语言包装造成的
  (≤5 步 OOD .83、分支 1.0、包装 1.0 全部可教);剩余嫌疑人:题型多样性、
  规则隐式性(两个 future-work 靶子)。从句:过训会损伤已获得的 OOD 泛化
  (bend-e ep1 峰 .91→ep4 .66,notes/NOTES_bendpoint.md)——与山脊现象近亲。
- 范围:(GSM 算术 A_delivered/A_latent + Tier-2 a–d + bendpoint e/f/g OOD 判据)
- 证据锚:ledger/master_ledger.csv(A 列);notes/NOTES_tier2_frontier.md;
  data_bend/race_summary.json;notes/NOTES_bendpoint.md
- 邻居差分:非"A 恒零"——tier-b/c/d OOD 95-100% 是自家反例,边界另有来源
- 四问:✅ ✅(四条 non-claim 兜底) ✅tier-2 即反例已并入主张 ✅弯点来源未决(如实)

### CL-3 决策与体裁在激活层可分离,决策可单卖(83→94%,不带税)【范围:Qwen 家族;M3 收窄 2026-07-14】
- **并读注(2026-07-12 签字附则2)**:E5b 证明方向不把体裁强加给没要求它的输入
  (素题 bleed 0);E 臂显示当输入明确要求 schema 时方向提升遵约(30→75%)。
  两者拼合 = 方向推的是"投入被请求的修复任务"(决策+任务投入),
  不是无差别体裁注入。不矛盾,是更精确的画像。
- 范围:(v4 floor e8, d_plain@L12, α≤16;**限 Qwen 家族**——M3 在 Llama-3.1-8B
  上以同配方自提方向未复现:resist +24.5 伴 O_acc −37/能力 .88→.17,全局退化
  资格不符,notes/NOTES_m3_llama_steering.md;处方第5条 steering 一线地位同限)
- 证据锚:notes/NOTES_steering_e5b.md;notes/NOTES_e_arm_autopsy.md
- 邻居差分:上限 94%<SFT 99-100%,非等价替代;权重层对齐 instrument-limited
- 四问:✅ ✅ ✅E5-v1 的税=自家反例(探针伪影,已判别) ✅

(新增主张按模板追加;未过四问不入册。)

### CL-4【已入册 2026-07-13;F 补审=受托审计轮双变体对照通过】格式约束本身劣化计算——体裁耦合在 pre-repair 模型先天存在
- 范围:(GSM8K test 1300, 同题受控配对 O vs F(仅输出格式改 JSON), pre-repair greedy)
- 证据锚:probes/out(F/gsm 76.7% vs O/gsm 93.5%,−16.8pp;验尸 303 miss 零提取器救回,
  295 错数值 + 8 表达式未计算[单列子模式])
- 邻居差分:**"format constraints 伤推理"有已知文献(Let Me Speak Freely 系)——本条记
  "受控复现 + 新联结",不记首创**;delta = ①逐题受控配对(同题仅改格式);②与修复训练
  安装体裁接成同一机制链:T4 的体裁耦合计算不是修复训练制造的,是**先天耦合被放大**(§5 升级)
- 四问:✅推出(验尸排除仪器) ⏳范围待 F 构念补审确认(双变体对照 20 条) ✅反例检查=
  hard 池 F/O 差动待分池复核 ✅另一可能=提取器不等价(已验尸排除)
- 状态:**审计判决=双重记账**(F_judge 测量角色保留 + 独立失败类);F 补审已过(qc/AUDIT_v2_delegated.md:"F 补双变体对照本轮亲验机械成立")→ 入册

### CL-5 诊断的可操作产出是购物清单,不是比例表(主实验定稿句,裁决1)
- 主张(两句,定稿措辞):**(i) 体裁决定修复数据的可见度**——修复组分收益在
  修复腔 +10~16pp、素题只 +2~7pp;**(ii) "按画像配比"在两种体裁下都没有测到
  优势**——该有的组分要在场、毒组分要踢、能力病走工具,其余交给地板。
- 范围:(GSM 探针桶 + 修复腔 corrupt 480, Batch-1/2 脊点 ckpt, REd/Δ安慰剂 + 冻结 score_repair)
- 证据锚:notes/NOTES_batch1.md;notes/NOTES_b2_0b_genre.md;notes/NOTES_batch2_dose.md
- 邻居差分:非"数据配比无用"泛言——format 组分存废差 +70~79pp;非"诊断无用"——
  购物清单本身(补什么/踢什么/在哪验收)全部来自诊断
- **统计红牌(裁决2)→ 已结案(2026-07-12 ★1)**:B 补至 3-seed(.717±.040 vs
  A1 .676±.025,区间重叠,t≈1.7 n.s.)——**定稿=安全句**
  "matched 在任何读法下都没有超过 uniform";强句永久停用
- 四问:✅推出 ✅范围限定 ✅自家反例=format 桶的组分特异性(已并入句 (ii) 的"要在场") ✅另一可能=预算不足(600/2000 题;如实入 limitation)

### CL-6 体裁门控(genre gating)——命名级主题【2026-07-12 ★4 收窄升级】
- 主张(定稿):**效应的可见度与符号由(域 × 体裁)决定**——开关是真开关,
  不是单向放大器。GSM 三例 + 2wiki 反向第四例(组分效应素题面可见、修复腔
  分不开,notes/NOTES_2wiki.md);"修复腔总是更灵敏"的读法废止。
- GSM 三例(原始三独立测量):
  ①修复收益可见度(B2-0b:+10~16 修复腔 vs +2~7 素题);
  ②服从类数据的危害(drl25:修复腔 keep_answer −17pp,素题全指标无害);
  ③组分收益符号(scaffold:素题 REd_format +94 / 修复腔 overall −11.9)。
- 证据锚:notes/NOTES_b2_0b_genre.md;notes/NOTES_batch2_dose.md §2;loop3/eval/genre_scores.json
- 邻居差分:与 CL-3(激活层可分离)相邻但不同——CL-3 说决策与体裁可分,
  本条说**测量与危害的可见度本身随体裁开关**;与 E1b"修复腔对症性"是同一
  拼图的两面(照抄病穿制服才犯、便服下是手抖)
- **known-limitation(裁决3)**:"结构 vs JSON"细归因停牌——single_scaffold 94%
  带 11% mute(边缘健康),scafffmt 80 vs 94 的比较被污染;判读按冻结区间落
  "JSON 约束"侧维持,机制归因不进 claim
- 四问:✅ ✅(三例都给了体裁+度量三元组) ✅反例检查=fmt 臂两体裁同向(增益型组分
  不受门控,已入 ①的措辞"可见度"而非"存在性") ✅另一可能=修复腔 JSON 契约的
  仪器效应(score_repair 依赖 JSON 解析;以 false_keep/clean_over 双列对冲,如实)

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
(2026-07-11 后记:体裁对账返回,主张已升格入册为 CL-5/CL-6。)

### COR-2(2026-07-11,Batch-2 裁决 5)
**P-B2-1**:三子预测 HIT,同时点名证伪面"fmt10 已饱和"成立——饱和点 ≤10%
(60 题),剂量-响应是阶跃不是坡;预注册脱靶方向 = "比预测更便宜",如实入档。
**P-B2-2**:MISS——素题 W_adopt 在 10/25% 剂量均 ≈ 载体,预测的单调进入不存在;
证伪面"阈值型/纯食谱"命中;新素材 = 危害被体裁门控(修复腔 25% 先中毒)。
**P-B2-3**:按冻结区间判"JSON 约束"侧;机制归因停牌(裁决3,见 CL-6 limitation)。
判定页:prereg/PREREG_batch2.md §3 对照 notes/NOTES_batch2_dose.md。

### COR-3(2026-07-11,Loop 5)
**P-L5-drills(cos(d,ΔW_drills)<0)MISS**:M1 = +0.13~+0.14(全层均值,两参照),
非反号。幸存序数信号:drills 对齐度仅为中性对照 cleanreplay 的 1/3
(+0.13 vs +0.40),M2 中 drills 与所有臂的 vec-cos 全场最小(0.06–0.24 vs 0.4–0.6)
——权重级呈现为**去相关/离流形,不是反对齐**。"反向疫苗"一词只可指行为学,
不可指权重几何(措辞归顾问)。notes/NOTES_loop5_deltaw.md。

### COR-4(2026-07-12,E 臂硬停验尸签字)
**P-E-1 MISS**(REd_conduct 68%<安慰剂;度量错配:E5b 的 94% 是 resist,REd 要求答对
——steering 让模型不上当,不让它算对,与 CL-3 自洽)。
**P-E-2 MISS 朝上**(预测 <+10pp,实测 +42.7pp;.760 超全部训练臂)——
措辞同 format 饱和款:预注册低估方向恰好偏向更便宜的方法。
**机制读法(收官句,三线闭合)**:E1b(keep–override 数据层结构性互斥)+
E5b(激活层可分离)+ E 臂(分离红利 .760,Δ安慰剂全部来自 keep+.41/abstain+.35,
计算面持平)= **"数据层修不掉的干涉,激活层绕得过去"**。
验尸单:notes/NOTES_e_arm_autopsy.md(两披露);taxonomy 引言:硬停最后一课=拦好消息。

### COR-5(2026-07-14,M3;封数据收官条)
P-M3-2/3 MISS(灾难级):Llama 自提方向非决策杠杆,steering 全局摧毁
(O_acc −37pp、修复腔 .100→.010);P-M3-1 字面 HIT 因全局退化资格不符不可解释。
诚实结局触发:CL-3 收窄 Qwen 家族。仪器:score_repair 非 dict 守卫(同族第二例)。
