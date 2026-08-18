# INSTRUCTION C-48 (2026-08-18) — Overnight Directive: Atomic Repair Scaling vNext

独立于 frozen paper 的探索分支 `experiments/vnext_atomic_scaling_2026-08-18/`;**严禁覆盖/修改/重算 frozen evidence**。旧结果只作 development observation。假设链:Atomic Model Diagnosis → Repair Scaling Laws → Model Adaptation → Constrained Optimal Prescription。终点:给新模型做 atomic diagnosis + 少量 calibration → 估 model-specific repair-law 参数 → 在 clean 不降的硬约束下自动求 optimal SFT recipe。

**A. Loss/Log-prob/Margin Diagnosis(第一优先)**:audit 现有 7 axes 的 canonical target;L_a=−log p(y*|x),ΔL_a=L_a−L_orig,有明确 wrong alternative 时 M_a=logp(gold)−logp(wrong)。区分:score 未掉但 confidence 塌 / margin 仍正 / margin 翻负。逐 axis 规定(Original gold NLL;Paraphrase +ΔL;Distractor gold NLL+margin(若有 planted wrong);WC REVISE decision loss+final NLL+margin;CC KEEP;Insufficient STATUS NLL;Structured contract-token 与 semantic 分开;S/R 仅 diagnostic)。**free-form 无唯一 target 不做假 loss,标 loss_not_well_defined**。输出 LOSS_LABEL_AUDIT.md / ATOMIC_LOSS_SCHEMA.json / LOSS_SCORE_ALIGNMENT.csv;回答 7 中几个可靠连续概率诊断。

**B. ≥5 checkpoints,≥3 families,≥2 sizes in one family**。优先 Qwen3-1.7B/4B/8B、Llama-3.1-8B、Gemma/Mistral(若有);download/auth >15min 直接 skip。每模型全量 base atomic profile(behavioral+NLL+ΔL+margins+clean loss/score)。输出 MULTIMODEL_ATOMIC_PROFILE.csv/json + Model×Axis heatmap(score/loss 两 panel,禁 radar)。

**C. Paraphrase 正式加入 Repair Candidate**(不再 diagnosis-only):surface rewrite、gold 不变;目标 L_para↓ 且 L_clean 不升且 Score_clean 不降。Repair set = {Format,Evidence,Revision,Answerability,Paraphrase}。

**D. Shared law + sparse adaptation,不重跑 full grid**:新模型每 repair 跑 n∈{0,n_low,n_high}:Fmt 30/120、Para 60/480、Evd 120/960、Rev 120/960、Ans 120/480。GPU 不够按 Format>Answerability>Paraphrase>Evidence>Revision 砍。沿用现有 SFT 实现/carrier/protocol/替换式/总预算;不得按模型手调 recipe;scheduler 持续吃满 GPU。

**E. 拟合 Scaling Laws(不预设 power law)**:candidate family = saturating exp / shifted power / Hill / log-linear(+harmful 用 benefit−damage 双指数)。ANS 必须分开拟合 Gain_insuff 与 Damage_false-abstain。LODO/held-out-dose CV;报 MAE、rank error、saturation-dose、held-out direction acc、score-law vs loss-law 稳定性。输出 SCALING_LAW_FITS.json / SCALING_LAW_REPORT.md / heldout_dose_predictions.csv。

**F. Model Adaptation M0-M3**(单 scalar .376 = M0 baseline):M1 per-repair amplitude a_{m,r};M2 +dose stretch τ_{m,r};M3 +clean-damage λ_{m,r}。只允许 base diagnosis + 2 calibration doses 估参 → 预测 held-out dose;比较四级 held-out MAE。参数表 |Model|Repair|base deficit|a|τ|λ|held-out MAE|。若与 model size/base deficit 有结构关系再拟 logτ 回归,数据不支持不硬报。

**G. carrier/diversity 作为 composition terms**:Δŝ_m(n)=Σf_{m,i}(n_i)+C_m(n)+D_m(n);重点不是 re-discovery,而是 adaptation 后能否继续使用。

**H. Optimizer:clean 不降是 HARD CONSTRAINT**:max RepairGain s.t. Σn_i+n_clean=2000;Score_clean≥base 且 L_clean≤base(可另给 noise-band-safe 解,但不准把 degradation 塞回 utility);FA≤.10;protected endpoints。n_clean 是 allocation variable(不强制 770/不强制>0)。两个 objective:Opt-Loss(normalized atomic loss deficits)与 Opt-U;两者接近=强结果。输出 OPTIMAL_RECIPES_BY_MODEL.json + 表。

**I. Prospective validation(若有余力)**:选 2 个不同 family(3-5B、7-12B);先写 PREDICTION_FREEZE_<model>.json(adapted params/recipe/predicted vector/clean/constraints/ranking)再训 law-optimal/replay/uniform(+heuristic)。成功标准 RepairGain>0 且 CleanScore≥Base 且 CleanLoss≤Base。没时间训完也保留 frozen prediction,不许先看结果再改 recipe。

**J. Runtime 规则**:queue 优先级 base profiles→loss extraction→calibration→fits→optimal prediction→prospective;GPU 空闲即派;OOM 自动降 batch 开 GA 不变 effective batch;crash retry 1 次,再败记录跳过;download>15min skip;每 30min 更新 RUN_STATUS.md;单模型不许卡死整个 queue。

**K. MORNING_REPORT.md 七问**:1 Loss diagnosis 成立吗(score 未掉时 ΔL/margin 是否先见 failure);2 多模型 profile 差异(≥5 ckpt 图);3 Paraphrase 可修吗(clean 掉没);4 law 能否预测 held-out dose(aggregate+per-repair MAE);5 adaptation 要几个参数(M0-M3 held-out 比较);6 每模型 optimal recipe;7 prospective 是否 clean 不降+repair 升。图只要 6 张(score profile/loss profile/scaling curves+heldout/adaptation 参数/size-deficit vs τ,a(仅数据支持)/optimal vs replay/uniform)。

**L. 禁止**:改 frozen paper;新结果塞旧 claim;为 law 好看删 model/dose;强行 power law;clean degradation 被 aggregate 掩盖;看结果后调 recipe;只给日志不给结论。

**终问**:atomic diagnosis 能否参数化 repair scaling law?少数 adaptation 参数能否迁移到新模型?fitted law 能否在严格 no-clean-degradation 约束下解出 optimal recipe?参数化 model→(a,τ,λ):a=能修多少,τ=要多少数据,λ=多容易伤 clean。若 shared curve shape 保留、仅需少数 (a,τ,λ) 适配,故事升一级。立即执行,持续到 GPU queue 清空或早晨,不等人工确认。
