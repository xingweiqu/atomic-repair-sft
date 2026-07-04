# PREREG_steering — E5 预注册(2026-07-07,本 commit 即时间戳)

> 依据 R-14(四曲线)+ R-21(余弦扩展)。分析开始前 commit。硬停 = 与本文件矛盾。
> **度量冻结(R-23)**:
> resist = w∩strict-parsed 上 final≠w;A_latent = 素题 answered-acc(分母=作答题),
> matched 到 pre-repair 作答集;体裁内计算 = ability|resist(自家分母,报 n);
> 出血/mute 按 ledger/genre.py 三分;普通题退化 = 素题全分母 acc 变化。
> 方向提取:pre-repair 模型,repair-eval prompt 最后 token 残差流,
> d_L = mean(resist=1) − mean(resist=0);逐层扫 {8,12,16,20,24,28} × α{4,8,16}
> (160 题固定子集,seed 42),最优层出全 α 曲线 {0,2,4,8,16,32}。

## 冻结预测

1. **存在 (L, α)**:resist ≥ 0.90,且素题零出血(json_bleed≤5%)、mute≤12%、
   A_latent 与 α=0 差 ≤5pp —— 即 **decision 可单卖,不带体裁税**(SFT 捆绑非必要)。
2. α 过大进入退化区(普通题 acc 下滑)—— 曲线呈"甜点+过冲"形态,如实记录甜点区间。
3. **余弦排序(R-21)**:cos(d, ΔW_targeted_override) ≈ cos(d, ΔW_opsonly)
   ≫ cos(d, ΔW_E1混合33%) > cos(d, ΔW_random) ≈ 0;
   **cos(d, ΔW_keep-only) < 0**(keep 数据写反方向 → "混合=正反抵消"机制实锤,
   与 v2.1 false-keep 两级锁链)。
4. 若 (1) 不成立(推不动/一推就带税)→ 如实报 "D 非线性可控",同样入 §4(机制边界)。

## 依赖与顺序
extract(pre-repair 激活)→ sweep(两阶段)→ align(需 batch-4a 的 e1b_opsonly_n300_s42_e4
与 e1c_keeponly ckpt 落 HDFS 后才能跑;缺 ckpt 时输出 MISSING 如实记)。
