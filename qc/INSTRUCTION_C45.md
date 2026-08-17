# INSTRUCTION C-45 (2026-08-17) — 最终 evidence-tightening patch + 开写正文

V2.1 story approved. Make one final evidence-tightening patch; do not restructure the paper and do not run new training experiments.(不重构、不新训。)

1. **Audit RQ1 "stable competence vs fragile success" wording.** If existing paired item-level logs support perturbed failure | original correct, add that existing-data readout as the direct RQ1 evidence. Otherwise soften the manuscript claim from same-item fragility to behavioral heterogeneity under controlled perturbations.
2. **Replace "four repairability classes / four-class structure" with "four qualitatively distinct observed repairability regimes/patterns."** Do not imply a universal taxonomy from one repair family per regime.
3. **Do not use format-MAIN .26→.30 as evidence that content is unchanged.** Use a direct frozen semantic/retention endpoint if available; otherwise remove the content-preservation clause from the Format result.
4. **In Fig1/Intro, remove "near-ceiling distractor / near-floor candidate judgment";** describe the profile as wide behavioral dispersion and emphasize the clean contrast between near-perfect contract compliance and much lower decision accuracy.
5. **"Targeted rescue answers why" → "Targeted rescue accounts for the dominant residual patterns";** retain all existing scope limits.
6. **Do not position RQ1 itself as the main novelty.** In Contributions: combine diagnosis + repairability into the first contribution; conditional composition = central scientific contribution; prospective held-out prescription = third.

After this patch, begin the manuscript. **Draft RQ2 Results → RQ3 → RQ4 → RQ1/Setup → Introduction last.** Keep numerical artifact pointers in the working draft.

导师结论:这版可以过。不再换故事;把 evidence wording 钉死,正式写。

## 执行记录(点 1 审计结果)
Existing paired item-level support **成立**(distractor 轴):frozen scorer 本身按 family 配对计算 paired_family
(= original.acc_exact ∧ condition.acc_exact 同 family)。529-fam formal 层,9 个 placebo 臂
P(distractor fail | original correct) 均值 .0949(range .082–.107),base 模型 .119。
已落 PAPER_EVIDENCE_FREEZE/rq1_paired_fragility.json(纯既有数据 readout,无新训练/推理)。
Paraphrase 仅 50-fam 辅助子集(directional),不升 formal;same-item fragility 主张限定 distractor 轴,
其余轴用 "behavioral heterogeneity under controlled perturbations" 口径。
