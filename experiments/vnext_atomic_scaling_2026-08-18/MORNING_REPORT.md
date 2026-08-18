# MORNING_REPORT — Atomic Repair Scaling vNext (C-48, 2026-08-18 overnight; C-49 修正版)

**C-49 总判定(采纳):Gain-side 已经很有希望;Damage-side 还没建模好。本版所有 law 数字以 v2 约束化拟合(A≥0, τ>0, α>0)为准;raw NLL 全部降级为 per-model 内部量。**

**Branch `vnext-atomic-scaling`; frozen paper untouched. All numbers from /mnt/hdfs/xwqu/vnext0818 artifacts (collected.json, SCALING_LAW_FITS.json, ADAPTATION_RESULTS.json, OPTIMAL_RECIPES_BY_MODEL.json, PREDICTION_FREEZE_*.json).**

## 第一屏:七问七答

**1. Loss diagnosis 能不能成立? — 成立,且在 score 还没掉时就能看到 failure(有真数)。**
7 轴中 **6 轴**有 canonical target 可做 teacher-forced 连续诊断,3 轴有显式 margin(LOSS_LABEL_AUDIT.md);free-text 端点如实标 `loss_not_well_defined`,不做假 loss。Qwen3-8B item 级配对(529 fam):
- Distractor 轴:original 与 distractor **都答对**(score 看不见任何问题)的 409 个 family 里,**65.5% 的 gold-NLL 已经上升**(ΔL>0)——confidence 先于 score 塌。注意如实:ΔL 幅度在 item 级不构成干净的严重度排序(intact 组均值 .81 nats 反而高于 fail 组 .36,受答案长度/难度混杂)。
- WC decision margin:行为正确组 margin<0 率 2.5%,行为失败组 9.3%——**margin 翻负把失败风险放大 3.7×**。
- CC(KEEP)轴暴露仪器偏置:immediate-contract margin 在行为正确时也 82.9% 为负(模型天然先倾向 REVISE token,生成时靠推理翻回来);方向仍可判别(失败组 100% 为负),但绝对符号在该轴不可直接当失败判据。**结论:loss/margin 诊断可用,但要按轴校准,不能一刀切。**
- 最硬的一个案例:Llama-3.1 base 的 R-Original strict score = .002(已知 strict-interface 伪影,score 完全失明),而 loss 侧 L_gold=5.01 连续可比——**score 会被格式伪影击穿,loss 不会**。
**C-49 红灯已确认并采纳**:raw NLL 不能跨模型比能力——Qwen3 家族 behavioral Original .52→.87 变好而 raw L_gold 3.20→3.91 变差;**连 BPB 都救不了**(Qwen3 BPB 4.6→5.6 随 size 反升,Mistral 18.8:scaffold 自然度主导)。可跨模型的只有 **paired ΔL、margin、margin 翻负率**(见 MULTIMODEL_PROFILE_NORMALIZED.csv;wc 翻负率:qwen3-8b .036 < 4b .123 < 1.7b .153,与能力序一致)。Llama strict≈0 而 loss 可读,只说明 instrument 不受 scorer artifact 影响,**不自动等于能力指标——log-prob 是 microscope,不是 claim**。

**2. 多模型 diagnosis 差异有多大? — 很大且结构化(7 checkpoints 全齐:Qwen3×4 + Qwen2.5 + Llama + Mistral = 4 families ✓,≥2 sizes ✓)。**
Mistral-7B-v0.3 base:又一个 strict-score 伪影案例(orig .008)+ WC decision .93 但 wc_joint .19、FA .34 全场最高——loss 侧照常可读。
MULTIMODEL_ATOMIC_PROFILE.csv + fig_multimodel_profile.pdf(score/loss 双 panel,无 radar)。要点:Qwen3 家族内 size 单调改善 Original(.52→.77→.79→.87)但 **abstention 全家族躺平**(.17-.31);Qwen2.5-7B contract 近满(.998)但 Original strict 仅 .11(格式伪影);qwen3-0.6b CC-keep 崩(.16);margin 侧模型间差一个量级(WC margin 2.8→17.4)。

**3. Paraphrase repair 能不能修? — score 侧弱,loss 侧真的在修;clean 没掉出 noise band。**
新建 paraphrase pool(Qwen3-8B 重写 carrier、数字守恒门控)训 60/480 两剂量 ×3 模型:
- 行为分:para acc 基本平(1.7b .70→.70/.68;4b .78→.80;llama .68→.74@60)。
- **loss 分:ΔL_para 系统性下降**——llama .221→.152@60→.113@480,4b .047→.004@60→**−.046@480(paraphrase 反而比 original 更容易)**;1.7b 平。
- clean:4b original .883→.870@480(−.013,noise band 内);其余 ≤.011。
**判定:paraphrase brittleness 是 loss 侧可修的,行为分辨率太粗看不见** ——正好呼应问题 1。

**4. Scaling law 能否预测 held-out dose? — 外推验证(C-49 新增,比 LODO 硬)直接支持 Gain/Damage 拆分。**
v2 约束化拟合(参数全部合法域内,FMT satexp τ=8.6)后,做 low→high 外推:**只用 ≤240 剂量拟合 → 预测 480/960/cap**:
| endpoint | 类型 | LODO MAE | **外推 MAE** | 方向 |
|---|---|---|---|---|
| FMT.contract | gain | .002 | **.001** | 1.0 |
| EVD.distractor | gain | .007 | **.007** | 1.0 |
| ANS.damage_fa(≤240段) | damage | .012 | .042 | 1.0 |
| REV.fix | mixed | .036 | .045 | 1.0 |
| REV.keep_damage | damage | .013 | **.103** | 1.0 |
| REV.clean | damage | .007 | **.178** | 1.0 |
| ANS.gain_insuf | gain(慢饱和) | .060 | .296* | 1.0 |
**Gain 侧外推准(FMT .001/EVD .007),damage 侧外推差一个量级(keep_damage .103、REV.clean .178)** ——advisor 的 "benefit 易学、damage 难学" 在 anchor 内部外推实验就成立,与 prospective 失手完全同构。*ANS.gain 的 .296 是慢饱和曲线在 ≤240 段还没见拐点(需要中段第三剂量),这正是 τ 需要第三校准点的又一证据。措辞:**dose response 高度可预测(FMT/EVD);不写 "discovered a scaling law"**。
[fits_v2/SCALING_LAW_FITS.json, heldout_dose_predictions.csv]

**5. Model adaptation 需要几个参数? — per-repair amplitude(M1)是最大收益;M2 的 τ 今晚只能乐观估计。**
2 个校准点(low)拟合 → 预测 held-out(high)[ADAPTATION_RESULTS.json]:
| model | M0 (1 param) | M1 (per-repair a) | 判定 |
|---|---|---|---|
| qwen3-1.7b | .133 | **.076** | within-family:M1 有效 |
| qwen3-4b | .168 | **.108** | within-family:M1 有效 |
| llama31-8b | .253 | .403 | cross-family:M1 失效 |
| mistral-7b | .169 | .433 | cross-family:M1 失效 |
(v2 约束化拟合口径;M2 的 τ 系 held-out 上选取,**不算验证,只是 hypothesis**,不再列数)
结论分层(C-49):**a_{m,r} 有证据(仅 within-family);τ 是 hypothesis;λ 明显不稳(方向都错过)**。两个跨族模型(Llama/Mistral)M1 都比 M0 差——跨 family 适配需要比 amplitude 更高层的结构,这是真实且重要的结果,不藏。
参数表(a/τ/λ per model×repair)在 fig4_adaptation.pdf;λ(clean 敏感度)可估但 3 模型间符号不稳(−1.8/+1.1/−1.4),**不声称 λ 已成立**。size vs a 只有 3 点,fig5 标 EXPLORATORY 不下结论。

**6. clean-no-drop optimizer 的处方(每模型,n_clean 是自由变量)[OPTIMAL_RECIPES_BY_MODEL.json]:**
| model | FMT | EVD | REV | ANS | PARA | n_clean | pred clean | pred FA |
|---|---|---|---|---|---|---|---|---|
| qwen3-1.7b | 120 | 240 | 0 | 960 | 60 | 620 | .748≥.737 ✓ | .057 ✓ |
| qwen3-4b (strict) | 240 | 480 | 60 | 480 | 0 | 740 | .883≥.883 ✓ | .038 ✓ |
| llama31-8b | 240 | 960 | 0 | 120 | 30 | 650 | .713≥.713 ✓ | .042 ✓ |
共性:**REV 被 optimizer 自动打到 0/近 0**(harmful law 跨模型保持),n_clean 自选 620-740(不是拍的 770),4b 的 strict 与 noise-band 解不同(约束真的咬合)。
**PARA 配额的诚实说明(C-49 质询)**:PARA 不在 SCALING_LAW_FITS 里(无 anchor 网格),optimizer 中 PARA 的预测增益恒为 0——它出现在 recipe 里 **完全因为固定 diversity term(≥4 active cells & total≥600 时 +.02,Qwen 开发族遗产)**。因此 PARA 维度是 "diversity allocation",**不是 law-derived**;recipes 表中已如此标注。要让 PARA 成为 law 维度,需先用今晚 3 模型×2 剂量点拟合 pooled 形状(v2 计划)。Opt-U 与 Opt-Loss 代理今晚共用 score-side law(anchor 旧 ckpt 已删无法补 loss 曲线)——**clean-loss 硬约束以 λ 代理执行,声明降级**。

**7. Prospective validation(冻结在训练前,commit ca02d0c):排名 2/2 命中;damage 侧约束每模型各失守一项——诚实开牌。**
| model | arm | actual U | frozen pred U | clean (base) | FA | verdict |
|---|---|---|---|---|---|---|
| qwen3-1.7b | **law-optimal** | **.6323** (1st ✓) | .5505 | .7127 (**< .7372,−.025 FAIL**) | .052 ✓ | RepairGain +.347 ✓;clean 硬约束破 |
| qwen3-1.7b | uniform | .6112 (2nd ✓) | .4877 | .7467 ✓ | .068 ✓ | — |
| qwen3-1.7b | replay | .2855 (3rd ✓) | .2855* | .7372 | — | *=anchor |
| llama31-8b | **law-optimal** | **.5392** (1st ✓) | .5456 | .7164 ≥ .7127 ✓ | **.173 > .10 FAIL** | RepairGain +.423 ✓;FA 硬约束破 |
| llama31-8b | uniform | .5075 (2nd ✓) | .5414 | .6994(< base) | .000 ✓ | — |
| llama31-8b | replay | .1164 (3rd ✓) | .1164* | .7127 | — | — |
- **frozen ranking(optimal>uniform>replay)两个模型全部复现**;RepairGain 巨大(+.35/+.42);U 幅度再次系统性低估(1.7b actual .63 vs pred .55——diverse 低估的旧模式跨到了 vNext)。
- **但 damage 侧预测在 2 点校准下不可靠**:1.7b 的 λ 预测 clean +.010 实际 −.025(方向都错);llama 的 ANS-damage amplitude 预测 FA .042 实际 .173(低估 4×)。**这正是"τ/λ 需要第三剂量+damage 专用校准点"的实证**——gain 侧 law 已可 prescribe,damage 侧 law 是 v2 的第一优先。
- 严格按冻结判据(RepairGain>0 ∧ clean≥base ∧ FA≤.10):**llama optimal 2/3,qwen 1.7b optimal 2/3;没有全绿臂**——不粉饰。

## 6 张图(C-49 修正版以 _v2 为准)
1-2. fig_multimodel_profile_v2.pdf(score panel + **paired/normalized** loss panel:BPB/ΔL/margin/翻负率,raw NLL 已撤下);3. fig3_scaling_curves_v2.pdf(约束化拟合,title 带 LODO+外推 MAE,含 Mistral 点);4. fig4_adaptation.pdf(M0/M1 held-out MAE + 参数表);5. fig5_size_vs_a.pdf(EXPLORATORY);6. fig6_prospective.pdf(预测 vs 实际 + 约束核查)。

## 运行台账
4 机 ×8×A100;52+4 队列;非-Mistral 33 arms + 6 profiles + para pool 全清;Mistral 下载 4 次重试后就绪(xet/HDFS-FUSE 冲突 + 坏 shard resume 陷阱),其 profile+11 arms 已放行在跑。僵尸锁教训:relaunch pkill 后必须清无 OK/FAIL 的锁。全部失败/重试记录在 /mnt/hdfs/xwqu/vnext0818/logs。

## 三个终问的今晚答案
- **Atomic diagnosis 能否参数化 repair scaling law?** Anchor 上能(LODO 过);且 loss 侧诊断给了比 score 更早的失败信号。
- **少数参数能否迁移 law 到新模型?** 同族(Qwen3 1.7b/4b):**per-repair amplitude 一层(M1,5 个参数)就把 held-out 误差砍半**;跨族(Llama):M1 不够,τ 层有信号但需第三剂量才能诚实验证——**a 可迁移、τ 待证、λ 不稳**。
- **Fitted law 能否在 clean-no-drop 硬约束下解出 recipe?** Optimizer 层面 3 模型都有 *预测可行* 解;但 prospective 开牌显示 **damage 侧预测不可靠**(问题 7:无全绿臂)——所以正确表述是:**law 能正确排序 repair 收益(2/2),还不能可靠预测 damage 约束**。Benefit law 与 Damage law 必须分开建模(C-49)。
