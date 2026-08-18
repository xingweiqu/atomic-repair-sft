# SAFE_FRONTIER_V2_SPEC — vNext 第二轮唯一目标:predict the safe frontier(C-49,待批准后开跑)

**核心问题**:max RepairGain subject to zero clean degradation —— 即把 Benefit law G_{m,r}(n) 与 Damage law D_{m,r,k}(n) 分开建模,让 damage 侧也能被少量校准点估准。

**成功判据(冻结,与 C-49 一致)**:新一轮 prospective 中,训练前算出的 recipe 做到 RepairGain>0 ∧ CleanScore≥Base ∧ FA≤.10 全绿;damage 预测误差 |D̂−D| ≤ noise band。

## 设计(全部为 analysis-first,训练量小于第一夜)

1. **Damage 专用校准点(核心增量)**。第一夜的校准点全是 gain 导向剂量,damage 曲线上没有观测。每模型每 repair 增加 **1 个 damage-informative 剂量**(取 anchor damage 曲线拐点附近):ANS@960(FA 上升段)、REV@480(KEEP damage 中段)、FMT@960、EVD@480、PARA@960;同剂量同时读 clean 端点 → 每模型 +5 runs(4 模型 = 20 runs,~半夜量)。
2. **第三剂量让 τ 可验**:上述点与既有 {low, high} 构成 3 点/repair → M2 的 τ 可以 fit-on-2 predict-3rd 诚实验证;ANS 慢饱和的中段拐点同时被覆盖(修 .296 外推缺口)。
3. **Damage law 拟合**:D_clean(n)、D_FA(n)、D_keep(n) 独立拟合(dblexp/spower,约束参数域);λ 从标量升级为 per-repair 曲线幅度 λ_{m,r};验证一律 low→high 外推,不用 LODO。
4. **PARA 转正**:用第一夜 3 模型×2 点 + 本轮 +1 点(共 3 点×4 模型)拟合 pooled shared shape + per-model amplitude → PARA 进 SCALING_LAW_FITS,optimizer 中不再靠 diversity term 配额。
5. **诊断口径**:全部 paired(ΔL/margin/翻负率);raw NLL 与 BPB 只作 per-model 内部量(第一夜实证:BPB 也不能跨模型)。
6. **Prospective v2**:qwen3-1.7b + llama31-8b(与第一夜同,可直接对比),重解 n*(用 benefit+damage 双 law),freeze(含 damage 预测向量与 noise band)→ 训 law-optimal + safe-frontier-conservative(留 damage 余量的次优解)两臂;判据全绿才算过。
7. **不做**:不加新模型;不重跑 anchor;不动 frozen paper;不把 clean degradation 放回 utility。

**预算估计**:20 校准 runs + 4 prospective runs ≈ 24 jobs,4 机一夜内清空(第一夜 56 jobs 实测约 4 小时净算力)。
