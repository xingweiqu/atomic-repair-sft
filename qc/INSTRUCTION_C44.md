# INSTRUCTION C-44 (2026-08-17) — V2.1 patch:中心从 atomic repair 推进为 repairability

导师裁决:V2 方向已对,框架通过,不再大改故事;RQ3 "Atomicity in evaluation does not imply additivity in training" 已是全文最强 scientific pivot。做最后一次 V2.1 patch(8 点),其他结构、数字、freeze、RQ3/RQ4 不动。打完即可开始正式写正文。

## 8 点 patch

1. **RQ1 不问 "How much"**(没有正式量化指标回答隐藏了 37% 还是 52%;我们证明的是存在什么结构、能不能拆开):
   > RQ1: **What atomic behavioral failure structure is hidden by aggregate benchmark performance?**
   (或方法型:Can aggregate benchmark performance be decomposed into atomic behavioral failure structure?)
   base profile 中同一模型 interface/distractor/KEEP/abstention/candidate judgment 的巨大差异已足够回答。

2. **RQ2 改名 Atomic Repairability**,不预设 failures admit repairs(最有意思的 finding 恰是很多修不动、甚至越修越坏):
   > RQ2: **How repairable are atomic behavioral failures under targeted SFT, and how does repairability vary with dose and domain?**
   `repairability` 成为论文正式科学对象。四类 finding 自动变成:cheaply repairable(Format)/ weakly repairable(Evidence)/ resistant-harmful to repair(Revision)/ repairable under a constraint(Answerability)。比"四条 heterogeneous response curve"强。

3. **删除 7 evaluation axes ↔ 4 repair families 一一对应暗示**。"map each atomic behavioral failure to an atomic SFT repair" 太强(Paraphrase 无独立 repair;Correct/Wrong candidate 合成 Selective Revision)。改为:
   > **We instantiate four representative atomic SFT repair families targeting selected failure structures exposed by the atomic evaluation.**

4. **修 Evidence 内部矛盾**:"+2–3pp in every domain tested" 与 in-domain K .83→.78 矛盾。改为:
   > **Evidence repair shows only a small positive effect in the Reasoning discovery setting and does not establish a robust cross-domain repair benefit.**
   这反而支持 "some diagnosed failures resist the targeted SFT repair we tried",对 repairability 故事加分。

5. **Answerability 的 1.00 必须连着 constraint 讲**(hard constraint FA≤.10,不能让读者以为 1.00 是最佳 operating point):
   > Answerability rises from .16 to .93 by dose 480 and continues toward 1.00 at higher dose, while false abstention rises and eventually crosses the preregistered constraint.
   强调 constrained repairability。

6. **"held-out model family it had never touched" → "a model family held out from response-model fitting and composition-correction development"**(Llama family 可能出现在其他 cross-model 工作里;真正需要的 methodological claim 是没参与 repair model 和 correction 的 development)。

7. **Fig.1 禁用 radar chart**(interface/distractor/KEEP/abstention/K-decision 虽都 0–1 但不是同一种量,radar 暗示统一几何意义)。改为 **atomic-profile heatmap / tile matrix**(行=domain,列=atomic axes);并作为全文视觉语言:后面 repair response 在同一组 axes 上画 Δ。

8. **全文 spine 改为**:
   > **Diagnosis → Repairability → Composability → Prescription**
   (比 Atomic Diagnosis→Atomic SFT Repair→Repair Response→Conditional Recomposition→Prescription 更好记。)

## 钉死的四个 RQ

- RQ1 — Atomic Diagnosis: What atomic behavioral failure structure is hidden by aggregate benchmark performance? (Aggregate Performance → Atomic Failure Profile)
- RQ2 — Atomic Repairability: How repairable are atomic behavioral failures under targeted SFT, and how does repairability vary with dose and domain? (Failure_i —Repair_i, dose, domain→ Δs;吃掉最多 findings:repairability/dose/saturation/null/harm/collateral/Pareto/domain reversal/large-eval correction;应为最厚实一章)
- RQ3 — Repair Composition: Does atomicity in evaluation imply additivity in training? (Δs_mix ≟ Σ Δs_i → **No** → carrier + diversity×dose → conditional composition;最核心 scientific discovery)
- RQ4 — Prospective Repair/Prescription: Can conditional repair structure prospectively prescribe SFT for a held-out model family? (**Yes, in our held-out test** → Llama Outcome A)

## Introduction 备注

- 第一段 "80% competence" opening 保留(已 80 分)。
- 第三、四段围绕 repairability 强化;关键转场:拆出 failure 只是第一步,真正的问题是这个 failure **有多容易被 SFT 修复**;"我们发现 repairability 本身存在结构"(cheap / weak / resistant / collateral / constrained / domain-dependent);再自然问"已知每个 failure 的 repairability,能不能拼回去?"→ RQ3。

## 结论

框架通过,不再大改。中心从 "Atomic failure → targeted repair" 推进为 "**Atomic failure → repairability**"。这一版打完可以开始正式写正文。
