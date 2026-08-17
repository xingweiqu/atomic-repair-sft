# INSTRUCTION C-43 (2026-08-17) — 结构性重写:Atomic Diagnosis → Repair → Composition → Prescription

> 现在对论文做一次**结构性重写**,不是小修 wording,也不是新增实验。所有实验结果、冻结规则、数字和 artifact provenance 保持不变。
>
> 新的论文主线统一改为:
>
> Aggregate Performance → Atomic Diagnosis → Atomic SFT Repair → Repair Response → Conditional Recomposition → Prospective Prescription
>
> 核心思想不是"怎么优化 SFT recipe",而是:
>
> > **evaluation 先发现问题、把 aggregate score 拆成 atomic behavioral failures;再把这些 failure 映射成 atomic SFT repairs;最后研究这些 repair 能否组合成整体修复方案。**
>
> `recipe optimization` 降级为最终 proof-of-use,不再是论文的出发点。
>
> ## 1. 全文按 4 个 RQ 重构
>
> ### RQ1 — Atomic Diagnosis
> How much does aggregate benchmark performance hide distinct atomic behavioral failures?
> 核心问题:一个 aggregate score(例如 80% accuracy)是否真的代表统一的"80% competence"?还是混合了 stable competence 和 fragile success?
> Controlled atomic evaluation axes:Original / Paraphrase / Distractor / Wrong Candidate / Correct Candidate / Insufficient Information / Structured Output;S/R assistance 作为 recoverability diagnostic,不作为正式 training component。
> 映射:Aggregate Score → Atomic Failure Profile。
> 核心句:**Aggregate scores hide atomic failure structure.**
> 注意:"80%"只作解释性例子,不伪装成正式实验数字;不声称 exhaustive capability taxonomy;atomic = 一次尽量只改变一个局部条件。
>
> ### RQ2 — Atomic SFT Repair
> Do atomic behavioral failures admit targeted SFT repairs, and how do those repairs respond to training dose and domain?
> 四个 intervention 统一表述为 four representative Atomic SFT Repair Families:Format Repair / Evidence Robustness Repair / Selective Revision Repair / Answerability Repair。Clean replay = matched control/placebo。
> 不按"四种数据逐个报告",按科学属性组织:1 Repairability;2 Dose response(onset/saturation/high-dose harm);3 Collateral effects;4 Trade-offs(answerability gain vs false abstention);5 Domain dependence(保持/减弱/放大/reversal);6 Measurement stability(小 eval apparent effects 是否在 formal large eval 复现)。
> 数学对象:Δs_{i,d}(n)。
> 收进:Format 快速饱和;Evidence 小而稳;Revision fix 无稳定净收益+高剂量伤 KEEP+optimizer 倾向极低 dose;Answerability 收益+false-abstain constraint;K/IF cross-domain collateral;Revision direction reversal;formal large eval 撤回多个早期小样本现象。
> 核心句:**Atomic failures have heterogeneous repair dynamics: some are cheap to fix, some resist SFT, and some repairs create new failures.**
>
> ### RQ3 — Repair Composition
> Does atomicity in evaluation imply additivity in training? 主要 scientific pivot。
> Δs_mix ≈? Σ_i Δs_i(n_i)。Qwen frozen mixture test = 对该 hypothesis 的直接 falsification。
> 必须突出:frozen additive ranking 失败;Spearman ρ=−0.43;U-MAE 超 noise;uniform 胜 predicted;failure-frequency U 高但违反 false-abstain hard constraint,必须 disqualify。
> 核心句:**Atomicity in evaluation does not imply additivity in training.**
> 然后回答为什么:tested pairwise interactions 太小;carrier dependence;diversity-by-dose regime。
> 统一写成 Δs = F(repair, dose, domain, carrier, composition)。
> 概念名优先:**Conditional Repair Composition**(不要只叫 mixture correction)。
> 注意:不说 carrier/diversity 是 universal laws;不说 Llama 分别独立证明两种 mechanism;只说 Qwen development family 上 identified these dominant correction structures,随后完整 corrected prescription package 在 held-out family 上成功 transfer。
>
> ### RQ4 — Prospective Prescription
> Can the learned repair structure prospectively prescribe SFT for a held-out model family?
> 流程:New Model → Atomic Diagnosis → Minimal Calibration → Frozen Repair Model → Predicted Prescription → Blind Validation。
> 保留完整 freeze chronology 和 replay-anchor disclosure:Qwen discovery 关闭;correction/recipe search rule/constraints/predicted ranking 先冻结;Llama 只允许预先规定的低维 calibration;replay seed42 是 calibration anchor,不称四臂"全部 blind";primary Predicted-vs-Uniform 是 fully prospective。
> 结果:Predicted>Uniform>Heuristic>Replay;actual .463>.407>.340>.303;Pred vs Uni +.057;Pred vs Replay +.160。
> Retention:replay Original .712/U .303;uniform .574/.407;heuristic .741/.340;predicted .696/.463。
> 用它回答:1 Pred vs Replay 不是整体能力提升(clean 保持,robustness 大涨);2 Pred vs Uniform 为什么不均匀混(U 和 clean retention 双赢);3 Pred vs Heuristic 为什么不用 clean benchmark 选(clean score 会选错方向)。
> 核心句:**Modeling conditional repair composition turns diagnosis into prescription.**
>
> ## 2. Introduction 完全重写
> 不从 "Given a fixed SFT budget, what data should we train?" 开头。新开头从 aggregate score 含义开始(80% ≠ 统一 80% competence;clean success 在最小扰动下可能消失;aggregate = stable competence + fragile success 混合)。
> 逻辑顺序固定 10 步:1 aggregate hides structure;2 atomic evaluation 拆开;3 diagnosis 不是终点;4 failures→repairs;5 heterogeneous repairability/dose/collateral/domain;6 additive recompose?;7 preregistered FAIL;8 rescue→conditional composition;9 freeze;10 held-out prospective success。
> 四句核心句(如上)。
>
> ## 3. Section structure 改成 RQ 驱动
> 1 Introduction;2 Atomic Evaluation: Decomposing Aggregate Performance (RQ1);3 From Atomic Diagnosis to Atomic SFT Repair (RQ2);4 Heterogeneous Repairability, Dose Responses, and Collateral Effects (RQ2);5 Does Atomicity Imply Additivity? (RQ3);6 Conditional Composition of Atomic Repairs (RQ3);7 From Atomic Diagnosis to Prospective Prescription (RQ4);8 Discussion;9 Related Work;10 Conclusion。
>
> ## 4. Figure storyboard 同步改
> Fig1 Aggregate Score → Atomic Failure Profile;Fig2 Atomic Failure ↔ Atomic SFT Repair(四 repair family+representative dose-response);Fig3 Repairability/Collateral/Domain Dependence matrix;Fig4 recomposition fails(左 additive FAIL,右 carrier+diversity→conditional composition);Fig5 held-out prospective prescription pipeline + Original-vs-U Pareto。
>
> ## 5. Claim matrix 重排
> 加 `RQ` 列;所有 claim 分入 RQ1-4;保留 exact artifact/field/scorer/checkpoint、discovery vs confirmatory、allowed/forbidden wording;不得重新引入已撤回小样本结果。
>
> ## 6. Terminology 统一
> atomic evaluation axis / atomic behavioral failure / atomic SFT repair / atomic repair family / repair response / repairability / collateral effect / conditional repair composition / prescription。`component` 仅作 implementation term;`scaling law` 不当主标题(RQ2 内可说 local dose-response / response scaling)。
>
> ## 7. 科学边界(不准写)
> universal SFT law;four fundamental repair types;all atomic repairs are predictable;evaluation axes statistically independent;training repairs universally non-additive;carrier/diversity threshold proven across all families;Llama independently validates each mechanism;utility magnitude perfectly predicted。
> 正确口径:four representative repair families;atomicity = controlled evaluation intervention,非 independent parameter updates;additive composition failed in the preregistered development-family mixture test;targeted rescue identified dominant conditional structures;frozen corrected prescription package transferred prospectively to one held-out model family。
>
> ## 8. 只交付 V2,不继续写全文
> 生成:PAPER_STORY_V2_ATOMIC.md / RQ_MAP_V1.md / PAPER_OUTLINE_V2_ATOMIC.md / CLAIM_EVIDENCE_MATRIX_V2_ATOMIC.md / MAIN_FIGURE_STORYBOARD_V2_ATOMIC.md / INTRODUCTION_V0_ATOMIC.md。
> RQ_MAP_V1.md 每个 RQ 必含:1 scientific question;2 hypothesis;3 experiments answering it;4 strongest positive findings;5 negative/null findings;6 allowed claim;7 limitation;8 main figure/table。
> **做完 V2 后停止,不新增实验,不继续扩完整正文,等 review。**
