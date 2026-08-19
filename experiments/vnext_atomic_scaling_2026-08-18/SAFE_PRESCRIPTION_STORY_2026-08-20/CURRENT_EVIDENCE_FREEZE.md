# CURRENT_EVIDENCE_FREEZE(C-52 §1)— claim 分级审计

来源:frozen paper PAPER_EVIDENCE_FREEZE(19 artifacts)+ vnext0818(106 runs,7 profiles,freeze 链 855bc27/ca02d0c/PREDICTION_FREEZE_V3)。**禁用 "8/8 independent prospective successes":** v1 之后的 v2/v3 是 sequential adaptive rounds(每轮见过上轮结果),只有 v1 Stage-A 是真正 held-out 盲测。

## A. Established(正文强讲)
| claim | 证据强度 |
|---|---|
| Qwen3-8B 四 repair 家族异质 dose response(cheap/weak/resistant-harmful/constrained) | 529-fam,anchor 3-seed,preregistered 网格(frozen paper) |
| 加性组合被预注册证伪;carrier dependence + diversity-by-dose 为 dev-family 修正 | frozen paper(preregistered falsification) |
| 冻结论文 Llama OUTCOME A:corrected package 前瞻迁移 | frozen(4/4 ranking, min>max seeds) |
| **Stage A prospective transfer(vNext v1)**:freeze-before-training,2 个新模型 U ranking 完整复现,同时 damage 约束双失手 | freeze ca02d0c;正负两面都 established |
| **Damage 是 composition-borne**:单臂 damage 全温和(clean ≤.015、llama 单臂 ANS@960 FA=0)vs 混合臂(−.025 clean / .173 FA) | 多臂交叉证据(20 CD + 4 v1-mix);核心对比 llama ANS 单臂 vs 混臂同剂量 |
| 1.7b uniform = strict all-green(δ=0)冠军;v3frontier U 记录 .6465 且 clean 代价 −.021 真实 | **3-seed** |
| Clean non-inferiority:δ=0 下 2/4 模型无有效臂;δ=.01(先验 noise band)下 4/4 有 | 32 臂审计,关键臂 3-seed |

## B. Supported but bounded(可讲,必须带 scope)
| claim | bound |
|---|---|
| Benefit response 的低维 adaptation(a+τ):三点验证 M2<M1 于 4/4 模型 | 校准点单 seed;τ 网格粗;FMT 跨模型外推散差大(fig3 可见) |
| Damage:composition-borne 升 A(llama CD300 FA .419±.05 3-seed vs 单臂 ANS@960=0);"光滑非单调面"撤回 → unstable mid-composition surface(CD600 FA sd .25,3-seed) | 05_DAMAGE_REPLICATION 已裁决 |
| Loss/margin 诊断先于 score 见失败(65.5% ΔL>0;margin 翻负 3.7×) | Qwen3-8B 单模型 item 级;仪器偏置按轴校准(CC 轴符号偏置) |
| PARA loss-side 可修(4b 干净命中) | model-conditional(1.7b null、mistral 噪);行为分不动 |
| paired-only 跨模型诊断教条(raw NLL 与 BPB 均不可跨模型) | 7 模型 profile 支持;是方法约束不是发现性 law |
| Stage B(v2/v3)每轮 U 方向/目标命中 | **adaptive sequential prescription**,非独立盲测 |
## C. Exploratory(appendix/future work)
loss-side laws ×4(FMT/REV 有跨族符号翻转)、size-vs-a(3 点)、mistral 全部 score 侧读数(strict 伪影+FA 失控)、Opt-Loss 目标、composition guard 线性缩放(llama clean 已证不足)、diversity premium 固定项。

## 时序审计
真 freeze-before-training:frozen paper mixture/rescue/Llama 链;vNext v1(ca02d0c)、v2(855bc27)、v3(PREDICTION_FREEZE_V3)。v2/v3 的 freeze 保证"没看本轮结果改本轮配方",但轮与轮之间 adaptive——正文必须按 Stage A/Stage B 表述。
