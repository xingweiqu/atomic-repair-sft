# INSTRUCTION C-49 (2026-08-18 morning) — vNext 判定:Gain-side 有希望,Damage-side 没建模好

总判定:有真信号但**不判"scaling law 已成功"**。正确表述:**The law successfully predicted repair-side ranking, but failed to reliably predict the damage constraints.** 一加"clean 不掉点"硬标准,两个 law-optimal 都不算成功(1.7b clean −2.5pp fail;llama FA .173 fail)。

1. **最值钱的新 finding:Benefit Law ≠ Damage Law**。拆成两个对象:G_{m,r}(n) repair benefit law 与 D_{m,r,k}(n) damage law;n* = argmax G s.t. D_clean≤0, D_FA≤.1, …。核心句:**Learning how much a repair helps is easier than learning where it hurts. Optimal SFT prescription therefore requires separate benefit and damage scaling laws.** 证据:1.7b clean damage 预测 +.010 实际 −.025(方向错);llama FA 预测 .042 实际 .173(低估 4×)——不是 calibration error,是 constraint model 没学会。
2. **Loss diagnosis 必须改 paired/normalized,不能 raw NLL**。红灯:Qwen3 size↑ behavioral Original .52→.87 变好,raw L_gold 3.20→3.91 反而变差 → raw NLL 不能跨模型比能力(tokenizer/template/scaffold 自然度/answer-only 与 generation policy 不一致)。Llama strict≈0 而 loss 可读只说明 instrument 不受 scorer artifact 影响,不自动等于能力指标。改用:ΔL_a=L_a−L_orig(同模型同 family paired,优先);有 alternative 用 margin;跨 tokenizer 用 byte-normalized NLL/BPB。"log-prob 是 microscope,不是 claim"。
3. **PARA 进了 optimizer 却不在 SCALING_LAW_FITS** → 必须解释 PARA allocation 依据什么;不是 fitted law 就不能叫 law-optimal 的维度。
4. **拟合技术问题**:出现负 τ 等退化参数 → 强制 A≥0, τ>0, α>0;monotonic endpoint 加约束;harmful endpoint 显式 benefit−damage 分解。FMT LODO .003 说明 dose response 可预测,但不写 "discovered a scaling law"。**验证改为 low→high extrapolation(30-240 拟合 → 480/960 外推)**,interpolation 不够有冲击力。
5. **Adaptation 结论分层**:a_{m,r} 有证据(M0→M1:1.7b .137→.070,4b .159→.075);τ 是 hypothesis(held-out 上选的,不算验证);λ 明显不稳;Llama M1 变差(.328→.406)= 跨 family 比 within-family 难很多,真实结果不要藏。
6. **执行不满**:zip 不是完整 audit package(缺 heldout_dose_predictions.csv、LOSS_SCORE_ALIGNMENT.csv、prospective actual result JSON、训练 manifest、plot scripts/raw source data);且 report "3 模型都有可行解且约束全绿" 与前文 "没有全绿臂" 自相矛盾。能看结果,不能当 evidence freeze。
7. **下一轮唯一大目标:predict the safe frontier**(max repair gain s.t. zero clean degradation)。不是加模型不是加曲线。若 damage law 能靠第三 calibration dose 估准,且下次 prospective 做到 RepairGain>0 ∧ Clean≥Base ∧ FA≤.1 且 recipe 训练前算出——paper 起飞。

## 执行记录(见同日修复 commit)
- fit_laws v2:参数 bounds(A≥0,τ∈(1,4000),α>0)+ low→high extrapolation 验证(≤240 拟合→480/960/cap 外推)与 LODO 并报;
- PARA 判定:optimizer 中 PARA 预测增益恒为 0,其配额完全来自固定 diversity term(≥4 cells & total≥600 的 +.02)——已在 recipes/报告中改标 "diversity allocation, not law-derived";
- 多模型 profile 主口径改 ΔL/margin/BPB,raw NLL 降级为 per-model 内部量并加 microscope 声明;
- MORNING_REPORT 矛盾句更正 + Gain/Damage 拆分重述;PROSPECTIVE_RESULT.json 落盘;完整 audit 包重打;
- SAFE_FRONTIER_V2_SPEC.md(damage 专用校准点+第三剂量+外推验证+全绿判据)待 review 后开跑。
