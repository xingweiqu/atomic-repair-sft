# PREREG_c16 — 泛化验证矩阵(C-16;逐格冻结,2026-07-19)

> 统一格式:每格 = 复现检验,五主张各给 HIT / REVERSE / UNTESTED 判据。
> **REVERSE = 硬停 + 单独成节,禁止静默灰格。**未测格如实留灰(Scope 的一部分)。
> 名单未被 Xingwei 圈改,按指令默认执行;数据源:SVAMP=ChilleD/SVAMP test 300,
> StrategyQA=ChilleD/StrategyQA test 687(facts 字段=隐式链原料);
> Mistral=mistralai/Mistral-7B-Instruct-v0.3(license 干净);32B=Qwen/Qwen3-32B。

## 五主张与统一判据(灰区 ±0.15 或列名判据)

| # | 主张 | HIT | REVERSE |
|---|---|---|---|
| 1 | 非特异地板 | U-mix ≈ clean-replay 素题面(±8pp) | U 显著低于 replay(<−8pp) |
| 2 | format 组分特异 | 含/不含 format 的 F 列差 ≥+30pp(或防丧失同型) | 含 format 反而更差 |
| 3 | drills 修复腔毒性 | drl25 修复腔 keep 或 overall < 安慰剂(−5pp 外) | drl25 显著更好 |
| 4 | 体裁门控 | 存在指标其可见度/符号随体裁翻(任一方向) | 两体裁完全同向同幅(±3pp 内)且全格如此 |
| 5 | steering 可推(限可推格) | resist +10pp 且过资格条款 | 资格内 resist 显著下降 |

主张 3 的"缺失"(与安慰剂持平)按 M2 先例记 MISS-absent,非 REVERSE。

## 格子与执行件

**G1 Mistral-7B-v0.3 × GSM(画像 + 五件套)**:M1 管线原生模板;
4 训 = replay/U(=B 均匀)/FMT10/drl25 复用冻结臂文件(template=mistral),
epochs {2,4};M2 判分器原样。测主张 1-4;5 = UNTESTED(不提方向)。
**G2 Qwen3-32B(只画像 + steering,不训练)**:七探针 + E5b 方向自提
(素题 W 行为标签)+ L×α 扫(资格条款);测主张 5 + 画像;1-4 = UNTESTED
(全参训练 32B 不可行,LoRA 破坏口径——Scope 明文)。
**G3 Qwen3-8B × SVAMP(画像 + 五件套)**:探针生成器 = GSM 管线移植
(Body+Question 拼接;W1/W2 注入沿冻结 validator w>0、比 [0.2,5];
gold 全体正整数天然满足池过滤);组件从 SVAMP train 侧造(不碰 test)。
**G4 Qwen3-8B × StrategyQA(画像 + 五件套,隐式桥改造)**:W-桥 = 在题面
注入与 facts 链冲突的错误事实句(type-match = 同谓词类别事实池);
**构念审计 100 条 ≥70% 闸门照旧,审计不过 = 该格 W 列 UNTESTED,不硬上**;
布尔答案域:F 探针=JSON {answer: true/false},O 判分=布尔精确;
abstain 类不适用(无 unanswerable 子集)如实灰。
每格画像的仪器闸门沿 M1(O 自检 + F schema ≥50%)。

## 交付

fig9 大验证矩阵(行=五主张,列=G1-G4+既有 Qwen-GSM/2Wiki/Llama-GSM 格;
✓/✗/灰);Scope 三条明文(32B 不训/70B 不做/全管线跨模型不做);
逐格判分入记分卡附录。
EOF
git add prereg/PREREG_c16.md && git commit -q -m "PREREG_c16 frozen: per-cell replication-check format, five claims x HIT/REVERSE/UNTESTED, G1-G4 cells with instrument gates and audit fallbacks

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" && git push -q https://xingweiqu:$(gh auth token)@github.com/xingweiqu/atomic-repair-sft.git gain-accounting-v1 && echo pushed