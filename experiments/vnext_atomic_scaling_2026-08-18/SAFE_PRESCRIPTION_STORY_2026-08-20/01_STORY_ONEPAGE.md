# Safe Data Prescription:一页故事(C-52)

**Spine:Diagnosis → Repairability → Benefit Response → Non-Additivity → Damage → Safe Prescription**

**Thesis:** Repair gains exhibit structured and partially transferable dose-response behavior, while collateral damage is substantially more model- and composition-dependent. Safe data prescription therefore requires benefit modeling together with empirical safety calibration, rather than a single additive scaling law.

1. **Diagnosis(什么在坏?)** 一个 aggregate 分数拆成 7 条 atomic 轴后是宽幅行为离散(同一模型 abstention .16 vs contract .99);paired loss/margin 在 score 未掉时已见衰减(65.5% 的 score-intact family ΔL>0)。诊断只能 paired,raw NLL 与 BPB 均不可跨模型。[Fig 1]
2. **Repairability(能修吗?多少剂量?)** 四类 repair 的 dose response 结构分明且异质:cheap(Format,30 例饱和)/ weak(Evidence)/ resistant-harmful(Revision)/ constrained(Answerability,收益对着 FA 约束);PARA 是 loss-visible 补充(model-conditional)。[Fig 2]
3. **Benefit Response(新模型上能预测吗?)** anchor shape × (amplitude a, dose-stretch τ) 低维适配:两低剂量拟合 → 第三剂量 held-out 预测,M2<M1 在 4/4 模型;跨族(Llama/Mistral)必须有 τ 层。claim:**local repair response shapes exhibit transferable structure after low-dimensional model adaptation**(非 universal law)。[Fig 3]
4. **Non-Additivity(直接加起来行吗?)** 不行——预注册加性预测被证伪(ρ=−.43,additive top pick 排第三);carrier dependence 与 diversity-by-dose 是 dev-family 修正结构。[Fig 4]
5. **Damage(高收益配方为何不安全?)** damage 是 composition-borne 且模型特异非单调:单臂 damage 全温和(llama ANS@960 FA=0.000)而混合臂可爆(FA .173);同 total 不同组成 → 完全不同 clean/FA(llama CD300 FA .462 vs CD600 .028,复制中)。**Benefit prediction is easier than safety prediction。** D_m = F_m(dose, composition, carrier, ratios) 无光滑参数形式。[Fig 4 inset + 05]
6. **Safe Prescription(怎么开方?)** Stage A prospective transfer:freeze→train→open,2 个新模型 U ranking 完整复现、damage 约束双失手(established 的正负两面);Stage B adaptive sequential refinement 沿经验安全锚推进 frontier:1.7b 严格全绿上限=uniform(U .575),δ=.01 下 CD1200d .594 / llama v3frontier .585;更高 U(.646)有真实 clean 代价(3-seed −.021)。**Frontier 是真实折衷曲线,不是待勾选的约束。**[Fig 5]

**尾句:** Our results suggest that evaluation-driven fine-tuning is better framed as constrained response modeling than as benchmark-driven data selection.
