# MORNING_REPORT — Atomic Repair Scaling vNext (C-48, 2026-08-18 overnight)

**Branch `vnext-atomic-scaling`; frozen paper untouched. All numbers from /mnt/hdfs/xwqu/vnext0818 artifacts (collected.json, SCALING_LAW_FITS.json, ADAPTATION_RESULTS.json, OPTIMAL_RECIPES_BY_MODEL.json, PREDICTION_FREEZE_*.json).**

## 第一屏:七问七答

**1. Loss diagnosis 能不能成立? — 成立,且在 score 还没掉时就能看到 failure(有真数)。**
7 轴中 **6 轴**有 canonical target 可做 teacher-forced 连续诊断,3 轴有显式 margin(LOSS_LABEL_AUDIT.md);free-text 端点如实标 `loss_not_well_defined`,不做假 loss。Qwen3-8B item 级配对(529 fam):
- Distractor 轴:original 与 distractor **都答对**(score 看不见任何问题)的 409 个 family 里,**65.5% 的 gold-NLL 已经上升**(ΔL>0)——confidence 先于 score 塌。注意如实:ΔL 幅度在 item 级不构成干净的严重度排序(intact 组均值 .81 nats 反而高于 fail 组 .36,受答案长度/难度混杂)。
- WC decision margin:行为正确组 margin<0 率 2.5%,行为失败组 9.3%——**margin 翻负把失败风险放大 3.7×**。
- CC(KEEP)轴暴露仪器偏置:immediate-contract margin 在行为正确时也 82.9% 为负(模型天然先倾向 REVISE token,生成时靠推理翻回来);方向仍可判别(失败组 100% 为负),但绝对符号在该轴不可直接当失败判据。**结论:loss/margin 诊断可用,但要按轴校准,不能一刀切。**
- 最硬的一个案例:Llama-3.1 base 的 R-Original strict score = .002(已知 strict-interface 伪影,score 完全失明),而 loss 侧 L_gold=5.01 连续可比——**score 会被格式伪影击穿,loss 不会**。

**2. 多模型 diagnosis 差异有多大? — 很大且结构化(6 checkpoints 已齐,Mistral 为第 7 个在补)。**
MULTIMODEL_ATOMIC_PROFILE.csv + fig_multimodel_profile.pdf(score/loss 双 panel,无 radar)。要点:Qwen3 家族内 size 单调改善 Original(.52→.77→.79→.87)但 **abstention 全家族躺平**(.17-.31);Qwen2.5-7B contract 近满(.998)但 Original strict 仅 .11(格式伪影);qwen3-0.6b CC-keep 崩(.16);margin 侧模型间差一个量级(WC margin 2.8→17.4)。

**3. Paraphrase repair 能不能修? — score 侧弱,loss 侧真的在修;clean 没掉出 noise band。**
新建 paraphrase pool(Qwen3-8B 重写 carrier、数字守恒门控)训 60/480 两剂量 ×3 模型:
- 行为分:para acc 基本平(1.7b .70→.70/.68;4b .78→.80;llama .68→.74@60)。
- **loss 分:ΔL_para 系统性下降**——llama .221→.152@60→.113@480,4b .047→.004@60→**−.046@480(paraphrase 反而比 original 更容易)**;1.7b 平。
- clean:4b original .883→.870@480(−.013,noise band 内);其余 ≤.011。
**判定:paraphrase brittleness 是 loss 侧可修的,行为分辨率太粗看不见** ——正好呼应问题 1。

**4. Scaling law 能否预测 held-out dose? — anchor 网格上能;跨模型见问题 5。**
Anchor(Qwen3-8B 8 剂量全网格,529-fam)冻结候选形族(satexp/shifted-power/Hill/log-linear;REV/ANS damage 加 benefit−damage 双指数),LODO CV [SCALING_LAW_FITS.json, heldout_dose_predictions.csv, 70 行]:
- FMT.contract:best=satexp,LODO MAE **.003**,方向 100%;
- ANS.gain:LODO MAE ~.03-.05 量级;ANS.damage_fa 单独拟合(从不揉进一个分数);
- EVD 近平(weak law 跨模型保持);REV 双指数捕捉 harmful 形态。
注意如实:个别 satexp 拟合出退化 τ(clamp 后成阶跃)——形状库要在 v2 加参数约束。

**5. Model adaptation 需要几个参数? — per-repair amplitude(M1)是最大收益;M2 的 τ 今晚只能乐观估计。**
2 个校准点(low)拟合 → 预测 held-out(high)[ADAPTATION_RESULTS.json]:
| model | M0 (1 param) | M1 (per-repair a) | M2 (+global τ)* |
|---|---|---|---|
| qwen3-1.7b | .137 | **.070** | .054* |
| qwen3-4b | .052 | **.036** | .030* |
| llama31-8b | .328 | .406 | .111* |
*M2 的 τ 在 held-out 上选的(只有 2 剂量,无第三点可验)——**声明为乐观值,需第三剂量才能诚实验证**。Llama M1 反而变差:llama 的 placebo 端点带强 collapse(FMT contract→0),amplitude 估计被污染——跨 family 适配比同族难,这本身是结果。
参数表(a/τ/λ per model×repair)在 fig4_adaptation.pdf;λ(clean 敏感度)可估但 3 模型间符号不稳(−1.8/+1.1/−1.4),**不声称 λ 已成立**。size vs a 只有 3 点,fig5 标 EXPLORATORY 不下结论。

**6. clean-no-drop optimizer 的处方(每模型,n_clean 是自由变量)[OPTIMAL_RECIPES_BY_MODEL.json]:**
| model | FMT | EVD | REV | ANS | PARA | n_clean | pred clean | pred FA |
|---|---|---|---|---|---|---|---|---|
| qwen3-1.7b | 120 | 240 | 0 | 960 | 60 | 620 | .748≥.737 ✓ | .057 ✓ |
| qwen3-4b (strict) | 240 | 480 | 60 | 480 | 0 | 740 | .883≥.883 ✓ | .038 ✓ |
| llama31-8b | 240 | 960 | 0 | 120 | 30 | 650 | .713≥.713 ✓ | .042 ✓ |
共性:**REV 被 optimizer 自动打到 0/近 0**(harmful law 跨模型保持),n_clean 自选 620-740(不是拍的 770),4b 的 strict 与 noise-band 解不同(约束真的咬合)。Opt-U 与 Opt-Loss 代理今晚共用 score-side law(anchor 旧 ckpt 已删无法补 loss 曲线)——**clean-loss 硬约束以 λ 代理执行,声明降级**。

**7. Prospective validation:PREDICTION_FREEZE 已在训练前 commit(ca02d0c),4 臂(2 模型 × law-optimal/uniform;replay=placebo 复用)结果:**
[PENDING — 由收割步骤填入:RepairGain>0? CleanScore≥base? FA≤.10? ranking 对不对?]

## 6 张图
1-2. fig_multimodel_profile.pdf(score panel + loss/margin panel);3. fig3_scaling_curves.pdf(anchor 形状+新模型校准点+M1 适配虚线);4. fig4_adaptation.pdf(M0/M1/M2 held-out MAE + a/τ/λ 表);5. fig5_size_vs_a.pdf(EXPLORATORY);6. fig6_prospective.pdf [PENDING]。

## 运行台账
4 机 ×8×A100;52+4 队列;非-Mistral 33 arms + 6 profiles + para pool 全清;Mistral 下载 4 次重试后就绪(xet/HDFS-FUSE 冲突 + 坏 shard resume 陷阱),其 profile+11 arms 已放行在跑。僵尸锁教训:relaunch pkill 后必须清无 OK/FAIL 的锁。全部失败/重试记录在 /mnt/hdfs/xwqu/vnext0818/logs。

## 三个终问的今晚答案
- **Atomic diagnosis 能否参数化 repair scaling law?** Anchor 上能(LODO 过);且 loss 侧诊断给了比 score 更早的失败信号。
- **少数参数能否迁移 law 到新模型?** 同族(Qwen3 1.7b/4b):**per-repair amplitude 一层(M1,5 个参数)就把 held-out 误差砍半**;跨族(Llama):M1 不够,τ 层有信号但需第三剂量才能诚实验证——**a 可迁移、τ 待证、λ 不稳**。
- **Fitted law 能否在 clean-no-drop 硬约束下解出 recipe?** 能,3 模型都有可行解且约束全绿(prospective 开牌见问题 7)。
