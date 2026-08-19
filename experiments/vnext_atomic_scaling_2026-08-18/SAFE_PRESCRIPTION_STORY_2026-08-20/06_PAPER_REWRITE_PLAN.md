# PAPER_REWRITE_PLAN(C-52;审核通过前不动正文)

对象:vNext 新论文(与 frozen paper 分离;frozen paper 不改一个字)。Spine:Diagnosis→Repairability→Benefit Response→Non-Additivity→Damage→Safe Prescription。

- §1 Intro:六条 claim hierarchy(C-52 §7),尾句 constrained response modeling;禁语清单入 lint。
- §2 Atomic Diagnosis(RQ:What is failing?):eval 轴 + paired loss/margin 教条;Fig1。原 vNext MORNING_REPORT Q1/Q2 材料。
- §3 Repairability(Can it be repaired, at what dose?):Qwen8B 网格四家族 + PARA 补充;Fig2。frozen-paper §4 材料复用(引用其 artifacts,不重算)。
- §4 Benefit Response(Can the gain curve be predicted on a new model?):shape×(a,τ),三点 held-out,4 模型;Fig3;写明校准点单 seed bound。
- §5 Non-Additivity(Can curves be combined?):No——预注册证伪 + carrier/diversity;Fig4(mixture 主图+inset)。
- §6 Damage(Why does a high-gain recipe become unsafe?):composition-borne(单臂 vs 混臂对比表)、非单调(05 复制裁决决定强弱表述)、D_m=F_m(...) 无光滑形式;Fig4 inset/表。
- §7 Safe Prescription:Stage A(prospective transfer,正负两面)/ Stage B(adaptive sequential refinement)明确分开;non-inferiority δ=.01 主判据 + appendix 敏感性;Fig5。
- §8 Discussion:benefit-vs-safety 不对称的含义;§9 Related;§10 Conclusion(三句:Benefit has exploitable structure; Safety is conditional; Prescription must respect both)。
- 必删/降级旧表述(见交付说明第 5 项)。
- Appendix:law 注册表 19 条全文、32 臂 non-inferiority、PARA、loss-side laws(C 级)、运行台账。
