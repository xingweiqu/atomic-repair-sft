# INSTRUCTION C-50 (2026-08-19) — "V2 开跑"

批准执行 SAFE_FRONTIER_V2_SPEC.md(C-49 计划):
1. Damage-informative 校准剂量 +1/repair/model(FMT@960、EVD@480、REV@480、ANS@960、PARA@960)×4 模型 = 20 runs——同时构成每 repair 第三剂量点(τ 可验:fit-on-2 → predict-3rd);
2. Damage laws(D_clean/D_FA/D_keep)独立拟合,λ 升级为 per-repair 幅度,验证一律 low→high 外推;
3. PARA 用 4 模型×3 点转正为 fitted law;
4. Prospective v2:qwen3-1.7b + llama31-8b,benefit+damage 双 law 重解 n*,freeze 后训 law-optimal-v2 + conservative(留 damage 余量)两臂;判据 RepairGain>0 ∧ Clean≥Base ∧ FA≤.10 全绿才算过。
不加模型、不动 anchor、不动 frozen paper。
