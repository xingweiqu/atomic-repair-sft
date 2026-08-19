# INSTRUCTION C-52 (2026-08-20) — 收敛 vNext 故事:Atomic Diagnosis → Safe Data Prescription

停止追更高 U。新主线:Diagnosis→Repairability→Benefit Response→Non-Additivity→Damage→Safe Prescription。
Thesis:Repair gains exhibit structured and partially transferable dose-response behavior, while collateral damage is substantially more model- and composition-dependent. Safe data prescription therefore requires benefit modeling together with empirical safety calibration, rather than a single additive scaling law. 对象:G_{m,r}(n) benefit / D_m(n,C) damage。**禁 universal scaling law 包装。**

1. CURRENT_EVIDENCE_FREEZE.md:claim 分 A Established / B Supported-but-bounded / C Exploratory;查 3-seed vs single-seed、真 freeze-before-training vs adaptive round;**禁 "8/8 independent prospective successes"**(sequential adaptive rounds 不算独立盲测)。
2. 三大 finding:F1 atomic repairability 有结构化 dose response(四类+PARA loss-visible 补充,不强行同函数);F2 benefit response 有跨模型 adaptation 结构(claim = "local repair response shapes exhibit transferable structure after low-dimensional model adaptation",非 universal);F3 damage breaks simple scaling → safe frontier(D≠D(N_total);non-monotonic;benefit prediction easier than safety prediction)。
3. 唯一补实验:**damage non-monotonicity 复制**——Llama CD300 vs CD600 补 2 seeds(→≥3);GPU 够再 Mistral CD600 vs CD900。看 FA/clean/U/endpoint/训练健康。复制失败则诚实撤强 claim 改 "unstable damage surface"。
4. Clean retention 改正式 non-inferiority:δ∈{0,.005,.01,.02} 敏感性 + seed CI;正文一个明确阈值,完整敏感性进 appendix;禁 post-hoc 选 δ。输出 CLEAN_NONINFERIORITY_AUDIT.{csv,md}。
5. 重做主图 5 张:Fig1 diagnosis(简);Fig2 Qwen8B 四 repair dose response(gain+collateral);Fig3 Model-Adapted Repair Response Laws(fitted vs held-out 点区分,禁 Universal 标题);Fig4 mixture 主图(frozen spec 读数,Additive top pick ≠ actual best valid + carrier/diversity inset);Fig5 Safe Frontier(x=ΔClean,y=U,FA 用 marker,禁 20 label 挤图)。
6. Prospective 重新表述:Stage A prospective transfer(真 held-out)与 Stage B adaptive sequential prescription 分开,B 不冒充盲测。
7. Abstract/intro claim hierarchy 六条;尾句 "evaluation-driven fine-tuning is better framed as constrained response modeling than as benchmark-driven data selection"。
8. Spine:Diagnosis→Repairability→Benefit Response→Non-Additivity→Damage→Safe Prescription。
9. 禁语:universal scaling/repair law、damage monotonic/fully predictable、all models no-clean-drop、exhaustive optimal recipe、8/8 independent、7 models full grids。推荐术语:repair response law / local dose-response / model adaptation / conditional composition / empirical safe frontier / constrained prescription / adaptive sequential refinement。
10. 交付 SAFE_PRESCRIPTION_STORY_2026-08-20/:01_STORY_ONEPAGE / 02_CLAIM_EVIDENCE_TABLE / 03_EXPERIMENT_GAPS / 04_FINAL_RESULT_TABLE.csv / 05_DAMAGE_REPLICATION / 06_PAPER_REWRITE_PLAN / figures/。
停机原则:damage contrast multi-seed 完成且故事成立 → 停止 recipe hunting。先交 5 项(story 一页/claim 表/Fig2-5/damage 复制裁决/需删降的旧 claim 清单)过审,**审核通过前不重写全文**。
