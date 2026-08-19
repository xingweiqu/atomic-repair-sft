# CLEAN_NONINFERIORITY_AUDIT (C-52 §4)

Clean retention 判据从"绝对 ≥ base(精确到第三位)"改为正式 non-inferiority:Clean_recipe ≥ Clean_base − δ。

**主文阈值:δ = .01**。依据(非事后挑选):anchor 网格 placebo 的 3-seed clean sd = .012(SCALING_LAW_FITS seed_sd / v1 NOISE band,先于本审计确立);.01 为其保守下取。完整敏感性 δ∈{0,.005,.01,.02} 见 CLEAN_NONINFERIORITY_AUDIT.csv(32 arms,含逐 seed Δclean)。

## δ 敏感性(FA≤.10 内的 best-valid U)
| model | δ=0(strict) | δ=.005 | **δ=.01(主文)** | δ=.02 |
|---|---|---|---|---|
| qwen3-1.7b | uniform .575 | uniform .575 | **CD1200d .594** | v3frontier .646(3-seed Δclean −.021 越界仍 fail@.02? −.021<−.02 fail) |
| qwen3-4b | **无** | uniform .776 | uniform .776 | CD1200d .826 |
| llama31-8b | **无** | CD1200c .520 | **v3frontier .585** | v3frontier .585 |
| mistral-7b | uniform .500 | uniform .500 | uniform .500 | CD300 .558(FA .297 已 DQ,不入) |

## 读法
- **δ=0 严格判据下,4 模型中 2 个(4b/llama)不存在任何有效臂**——"绝对无掉点"在 .01 量级的 seed 噪声下不是可运营判据;
- δ=.01 下四模型均有 valid frontier 配方,且排序与 U-vs-clean frontier 一致;
- v3frontier(1.7b)的 −.021 在任何 δ≤.02 下都不达标——3-seed 已证实其 clean 代价真实,不靠 δ 洗白。
