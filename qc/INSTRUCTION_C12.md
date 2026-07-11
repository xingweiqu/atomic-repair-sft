# CC_INSTRUCTION_C12 — 图先行 + 三实验并行(2026-07-12,逐字归档)

> 双轨推进:**轨道 A = 论文全套图表先做出来**(图定了骨架,正文围绕图写,比先写字后补图
> 少返工一轮);**轨道 B = 三个补充实验同步上卡/开工**。写作分支 paper-v3-prescription 照开,
> 正文顺序不变(方法节→结果节→§7→intro/abstract 最后),但本周产出以图为先。
> 纪律沿用:数字可溯源、CLAIMS 为唯一措辞源、预注册先行、三闸门。

## 轨道 A:论文图表全套(本周交审图包)

### A0. 先读 skills(开工前置,不许跳)
盘点你可用的 skills 目录,凡与作图/论文/可视化相关的(plotting、figure、paper、
matplotlib 类)逐个读完再动手;没有现成的就把本节 A1 的风格规范当作临时 skill 固化成
`figs/FIGURE_STYLE.md`,全部图共用一份样式配置(字体、字号、色板、线宽),
禁止逐图手调。

### A1. 风格硬规范
色盲安全色板(Okabe-Ito 或 viridis 系);单 seed 数据点必须视觉区分(空心/虚线)并在
caption 注明;灰化数据(n_matched<50、污染对照)**不得出现在任何图中**;
输出 PDF 矢量 + PNG 预览双份;每图配三件套:caption 草稿、数据来源文件路径、
支撑的 CLAIMS 编号。审图包 = 全部 PNG + 三件套清单,一次性送 Xingwei 和顾问。

### A2. 图清单(正文 7 张 + 附录)

| # | 图 | 数据源 | 要点 |
|---|---|---|---|
| 1 | 诊断画像:93.5 表面分 vs 60.6 稳健分 + 失败构成堆叠条(轻信 16/格式 15/表述 6/能力 3/未解 2)| profile v1 + steering 分诊列 | 双池(gsm/hard)分面;脚注三件套(分母/过滤/labile 折扣)照裁决 |
| 2 | 涨分记账总览(92 run 堆叠条)| ledger master | **按 C-5 重制 K/M 拆色版**(旧图未拆,此账未清);v1 灰行不入图 |
| 3 | 山脊主图:parse↑/bleed↑/素题 acc vs epoch,D 到账 e2-3 与税 e8+ 标注 | LOOP1_5 sweep + C-9 追溯版 | 停车点竖线 + 三闸门标注;旧 e2 措辞一律用 C-9 修正后数字 |
| 4 | 配药主图(双面板):(a) 六单组分 RescueEffect 条形;(b) 混合臂 A1/B/C/D/E/安慰剂,3-seed 臂带误差棒 | batch1/genre_scores + B 3-seed | D/cleanreplay 单 seed 空心标注;E=零数据原点锚 |
| 5 | 剂量曲线(双面板):format 0/10/20/36%(≤10% 饱和阶跃);drills 0/10/25/100%(修复腔先中毒)| NOTES_batch2 | 100% 点用断轴或独立标记(无干净点/灾难点) |
| 6 | 体裁门控三联:修复收益可见度 / drills 危害 / scaffold 收益符号,各一小面板,同一"体裁开关"视觉语言 | B2-0b + batch2 | 这是命名级主题的图,三例并排是论点本身 |
| 7 | 机制:steering 四曲线(83→94,能力平线)+ 可教前沿(tier a–d 的 zero/ID/OOD)| NOTES_steering_e5b + NOTES_tier2_frontier | 两个子图合一张"机制与边界" |
| 附 | 预注册记分卡(HIT/MISS 全表)、abstain 方差警示小表、overlap 矩阵、处方手册表 | CLAIMS + notes | 记分卡放附录是可信度资产,如实含 MISS |

图 8 槽位预留:2Wiki 复现小图 + natural set 来源×探针映射表(轨道 B 数据回来即补)。

## 轨道 B:三实验并行

### B1. 2Wiki 验证章(服务器,一批卡,预注册先行)
缩微全流程:探针子集(O / P / W-bridge 桥下毒 / F)→ 病情表 → 均匀混修复 +
format 组分对照 → 脊点选点 → 双体裁验收。**预注册预测**:防骗组分可迁移、
体裁门控复现、profile 构成与 GSM 不同但处方三规则同构。数据集直接用
2WikiMultihopQA 原版,桥注入器按既有 type-match 闸门。产出:图 8 左 + 一节正文素材。

### B2. 弯点实验(服务器,半批卡,逐档预注册)
新档位:e=五步规则、f=条件分支规则(if a>b then…else…)、g=自然语言包装的 b 档规则
(拆"包装 vs 深度"混杂)。各 2000 train/1000 eval,OOD 切分照 Tier 2。
**G/B 赛跑为测量协议**:逐 epoch 记 ID acc / OOD acc / bleed / mute;
G=OOD 首次 ≥90% 的 epoch,B=bleed 首次 >5% 的 epoch;"可教"判据 = G < B。
预注册:e 可教、f 弯点候选、g 若掉档则包装即成本。CL-2 措辞待此实验后升级。

### B3. Natural set(零卡,写作期并行)
不从零收集,**从现成数据集采样重标注**:CREPE(错误前提真实提问,主料,50 条)、
GSM-IC(干扰注入近亲,30)、FalseQA/QA²(30)、sycophancy 评测(用户断言错答案,30)、
NQ-Swap 或 ConflictQA(RAG 冲突,30)、RGB(RAG 噪声,30)。
标注 schema:{来源, 原文, 错误信息类型, 映射探针(W1/W2/K 类…), 映射理由一句}。
双标注:Xingwei 复核 50 条重叠,报一致率。产出:图 8 右映射表 +
related work 差分行(每个数据集一行"他们测大象一条腿,我们的探针体系是整张病情表")。
**这些数据集若与既有结论重叠(GSM-IC ↔ W1),差分行如实写,记邻居不记首创。**

## 节律
审图包 3 天内首版;三实验预注册今天 commit、B3 即刻开工、B1/B2 排卡。
每晚 QUEUE_STATUS 照旧。图包审定前正文只写方法节(零争议部分),防止图文两头改。
