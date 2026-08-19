# V3_REPORT — Composition-Damage 直接测量 + Empirical Safe Frontier(C-51,2026-08-19)

数字来源:/mnt/hdfs/xwqu/vnext0818(collected.json 96 runs;PREDICTION_FREEZE_V3.json commit 先于训练)。队列累计 114 jobs 零失败。

## 1. CD 扫描(20 臂:4 模型 × {300/600/900/1200-diverse/1200-concentrated}):光滑 composition-damage 函数被数据否定

| model | CD300 | CD600 | CD900 | CD1200d | CD1200c | 结论 |
|---|---|---|---|---|---|---|
| qwen3-1.7b FA | .024 | .028 | .020 | .056 | .124 | 平滑上升,ANS-share 驱动 ✓ |
| qwen3-1.7b Δclean | **−.028** | −.007 | +.011 | +.004 | −.023 | 非单调:小 total 反而伤 |
| qwen3-4b FA | .032 | .032 | **.104** | .100 | **.221** | 处处踩 .10 线 |
| llama FA | **.462** | .028 | .000 | .000 | .004 | **狂野非单调:小混合 FA 爆炸** |
| llama Δclean | .000 | −.006 | −.028 | −.028 | **+.007** | 集中配方反而护 clean |
| mistral FA | .297 | .080 | **1.000** | .474 | .972 | 完全失控(uniform 却 =0) |

**判定:composition damage 是模型特异、非单调的**——同一 CD300 配方在 1.7b 上 FA .024、在 llama 上 .462、在 mistral 上 .297;llama 的安全区在**集中**配方(与 Qwen 相反)。任何跨模型光滑函数 (total, coverage) 都拟合不了这个。附带抓到:**v1 冻结配方在 4b 上 FA=.112 超限**(optimalv1 臂)——damage 跨模型失手第三例。

## 2. 方法转向:Empirical Frontier Anchoring + 局部 law 外推

既然 composition-damage 无参数形式,v3 改为:在已观测混合臂中取严格全绿的 U 最大者为锚,用 gain law 在其邻域做**一步**外推提案,freeze 后验证。
锚(开牌前已知):1.7b = uniform(U .611 全绿)/ CD1200d(.599 全绿);llama = **CD1200c(U .544 全绿,已胜 v1-optimal 的 .539)**。

## 3. Prospective v3frontier 开牌(freeze 先于训练)

| model | 提案配方 | U(目标) | Δclean | FA | 判定 |
|---|---|---|---|---|---|
| qwen3-1.7b | F240/E120/A600/P240 (1200) | **.6463**(>.611 ✓,史上最高) | −.0056 | .076 ✓ | U+FA 达成;clean 掉在 noise band 内 |
| llama31-8b | F240/E240/A960 (1440) | **.5945**(>.544 ✓,史上最高) | −.0095 | .000 ✓ | 同上 |

- **U 目标双达成且都是该模型历史最高有效 U**(1.7b:.611→.646;llama:.544→.595);FA 完全受控(经验锚定有效——llama 从 v1 的 .173 到 v3 的 .000)。
- **clean 双双落在 noise band 内的负侧**(−.006/−.010,band=±.012):band 判据双全绿,严格判据差毫厘。单 seed 下该判定被噪声主宰 → **正在跑 seed 复制**(5 个 claim 臂 × S43/S44,共 10 臂):v3frontier×2 模型、CD1200d、uniform(1.7b)、CD1200c(llama)。3-seed 均值将给出 strict-clean 的最终裁决。

## 4. 累计计分板(v1→v3)

- U 排名/目标预测:**8/8**(v1 2/2、v2 4/4 排名、v3 2/2 U 目标);
- FA 约束:从 v1 的失控(.173)→ v2 修复(0.000)→ v3 经验锚定后稳定受控;
- clean 约束:v2 conservative 在 1.7b 全绿(+.032);v3 两臂压 band 负侧待 seed 裁决;
- **方法论主线定型:benefit 侧 = 参数化 law(a+τ 双层已验证);damage 侧 = 经验锚定 + 局部外推**(参数化被 CD 扫描否定)。

## 5. 下一步(seed 复制开牌后)
- 若 3-seed 均值 clean ≥ base:v3frontier 即"全绿且历史最高 U"终局配方,vNext 故事闭环;
- 若仍带负:safe frontier 收缩半步(ANS−120 或 PARA+替换),最后一轮验证;
- 之后:V3 全套并入 vNext 论文素材(与 frozen paper 严格隔离)。
