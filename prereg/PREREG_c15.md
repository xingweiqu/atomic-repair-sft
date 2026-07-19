# PREREG_c15 — 地基加固三件(C-15;训练/推理前冻结,2026-07-19)

## E-15a 单 seed 主张补 seed(GSM)
臂×seed:D、single_drills、single_scaffold 各 +s43/s44;epochs {2,4,8,16}
(脊点规则需全档,24 config;协议=Batch-1 原样);评测=既有链
(ridgepass→ridgepick→fullpass→genre)自动扩展。
预测(全部=复现):P-15a-D reversed 修复腔与素题面均落 A1/B 区间内
(matched≈uniform≈reversed 三 seed 化);P-15a-drl W_adopt ≥15%(毒性复现);
P-15a-scf 素题 REd_format ≥+30pp(Δ安慰剂)且修复腔 ≤安慰剂(sign-flip 复现)。
**任一反转 = 硬停 + 单独成节。**收数后 fig4a 相应臂改实心+min-max 误差棒。

## E-15b M3-v2 扩扫(Llama steering 稳健性)
关系申报:M3-v1 已收割(CL-3 已收窄,COR-5)。v2 = 排除"层/α 选错":
扫 L∈{4,6,...,30}×α∈{2,4,6,8}(96 题子集,8 卡分片);
**资格条款(E 臂验尸(d))**:候选点须 ability|resist ≥ base−5pp 且
answered ≥ base−5pp,资格内取 resist 最大;无资格候选 = NEGATIVE。
预测(按指令口径):方向可提取、resist 可推、ability 平;
结局 A(有资格点)→ 全评四读数,若达 P-M3 三判据则 CL-3 恢复跨家族(COR-5 修订);
结局 B(NEGATIVE)→ 收窄加固("全层扫仍无资格点"),如实入 Scope。

## E-15c E 臂 α 三点扫(Qwen)
α∈{4,6}补测(α8 已有,同子集重读):O300+W1/W2 400+修复腔480;
读数 = O_acc / answered / mute / resist / adopt / repair overall。
预测:mute 随 α 单调上升,存在 α 使 repair ≥ .70 且 mute ≤8%(甜点非压线);
证伪面:α6 修复腔塌(<.65)→ α8 确为最小可用点,"压线"如实保留。
