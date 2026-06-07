# Atomic-Repair v2.1 — Comparison & Ablation Report

> 7 件事的结果汇总。所有数字来自本地 `evaluate_v2_1.py` 对 codex 在服务器跑出的预测
> (commit f1bfc12)评分,逐行对齐 600/600。结论以现象为准,不预设 skill 一定有效。

---

## TL;DR(结论先行)

1. **H-Aug / H-Abl 修正成功**:语义对齐 + 保留 head 后,两格从 v2 的 45%/20% 都回到 **100%**。
   → 证明 v2 的 H-Aug 掉点**不是 skill 无效,而是 skill 语义与 cell operation 不对齐**。
2. **真正起作用的是"把 repair 动作显式写进 trajectory",不是显式 skill 分类字段。**
   Actionized-CoT(99.7%)> Decision+CoT(95.8%)> RandomSkill(96.8%)> **Skill+CoT(89.2%)**。
   带完整 diagnosis/skill 字段的版本**反而最低**。
3. **机制**:失败的本质是 **false-keep 误诊**——把"需要修"的题诊断成 `no_failure_detected/keep_answer`,
   于是抄了错的 tentative。Skill+CoT 的标签空间**含 keep_answer**,且引入"先诊断"步骤,在单跳知识题上
   最容易 misfire。任何**移除 keep 选项 / 不先诊断**的设计(actionized / decision / 甚至 randomskill)
   都绕开了这个陷阱。
4. **修正后的口径**:repair 的关键是 **answer-update policy 的 commitment**,不是 fine-grained 诊断分类。

---

## 1. 原 v2 主结果(复现基线,供对照)

| 条件 | overall |
|---|---|
| A 零样本 | 0.0–0.2% |
| B Fact-only | 39.7% |
| C Fact→CoT | 79.0% |
| D Fact→Skill+CoT | 85.5% |
v2 两个异常:H-Aug C96.7→D45,H-Abl C25→D20。

## 2. H-Aug skill 修正前后(第1项)

| | v2 | v2.1(修正后) |
|---|---|---|
| H-Aug skill 标签 | bridge_retrieval(语义错位) | **use_provided_bridge_fact** |
| H-Aug D final | **45.0%** | **100.0%** |

修正逻辑:H-Aug 输入里已给桥事实,正确动作是"用",不是"检索"。对齐后 D 完全恢复。
→ **强证据:skill 在语义对齐时有效,之前的失败是 semantics 与 operation 不匹配。**

## 3. H-Abl 重做(第2项,方案A)

| | v2 | v2.1(保留head,只mask bridge) |
|---|---|---|
| 题型 | "the work in question"(head也遮,无解) | "Silver River was written by [MASK]..."(可恢复) |
| H-Abl C / D | 25% / 20% | **100% / 100%** |

→ v2 的 H-Abl 低**不是 repair failure,而是 underspecified query**。改成可恢复后两条件都满分。

## 4. 五个训练分支总体 + 逐格(核心结果)

**总体 final-answer:**
| 分支 | overall | false-keep | tentative-copy | repair-decision acc |
|---|---|---|---|---|
| cot_fixed (C) | 86.0% | 64 | 69 | 89.3% |
| **skillcot_fixed (D)** | **89.2%** | 63 | 63 | 89.5% |
| randomskill | 96.8% | 10 | 13 | 98.3% |
| decision | 95.8% | **0** | 7 | **100%** |
| actionized | **99.7%** | **0** | 1 | **100%** |

**逐格 final-answer:**
| cell | cot_fixed | skillcot_fixed | randomskill | decision | actionized |
|---|---|---|---|---|---|
| K-Aug | 50.0 | **40.0** | 100 | 85.0 | 100 |
| K-Abl | 100 | 100 | 100 | 100 | 100 |
| K-Cor | 46.7 | 80.0 | 70.0 | 95.0 | 100 |
| R-Aug | 80.0 | 96.7 | 100 | 86.7 | 100 |
| R-Abl | 100 | 100 | 98.3 | 100 | 100 |
| R-Cor | 98.3 | 100 | 100 | 100 | 100 |
| H-Aug | 100 | 100 | 100 | 100 | 98.3 |
| H-Abl | 100 | 100 | 100 | 100 | 100 |
| H-Cor | 85.0 | 75.0 | 100 | 91.7 | 98.3 |
| Clean | 100 | 100 | 100 | 100 | 100 |

**关键反常**:正确 skill 的 D(skillcot_fixed)在 **K-Aug 只有 40%**,被 randomskill/actionized(100%)碾压。

## 5. 为什么"正确 skill"反而最差 —— false-keep 误诊(第7项机制 + 新证据)

skillcot_fixed 在 K-Aug 的 36 个错误,**全部是同一模式**(真实例子):
```
题: Hilde Olmari 在哪国出生?  gold: Mavinia  tentative: Tarsisia(错)
D 输出: diagnosis="no_failure_detected", repair_skill="keep_answer",
        trace="...Hilde Olmari was born in Mavinia. So tentative 'Tarsisia' is correct; no repair needed."
        final_answer="Tarsisia"   ← trace 知道对的,却 keep 了错的
```
- **Skill+CoT 的标签空间含 `keep_answer`**,单跳知识题易被误诊成"没毛病"→ commit keep → false-keep。
- **RandomSkill 避开了**:K-Aug 被随机配成 `contradiction_check`(永不是 keep)→ 总进"修"模式 → 100%。
- **Decision 避开了**:学会"非 Clean 就 repair"→ false-keep 清零。
- **Actionized 避开了**:trace 写 "Action: surface the stored fact",动作空间无 keep → 99.7%。

→ **收益来源 = 消除 false-keep,不是 skill 语义。** 显式 diagnosis/skill 字段因为含 keep 选项 +
先诊断,反而引入误诊风险。

## 6. RandomSkill 消融(第3项)

RandomSkill(打乱标签,固定 seed,见 `randomskill_mapping.json`)overall **96.8%**,高于正确 Skill+CoT。
- 不是"随机标签也学到了语义",而是**随机映射恰好把危险的 keep_answer 从知识格移走了**。
- → **不能用 RandomSkill 不掉分来证明"skill 语义无关"**;它掉不下去是因为副作用(避开 keep)。
  这条本身是个 confound,报告里如实标注。

## 7. Actionized-CoT 消融(第4项)—— 主结论

Actionized-CoT(动作写进 trace,无 skill 字段)**99.7%**,**高于** Skill+CoT(89.2%)。
→ 按 spec 第4项判据:**主要收益来自 actionized trajectory,不是显式 skill field。**
显式 skill 字段不仅非必要,反而有害(引入会 misfire 的诊断步骤)。

## 8. Gold / Wrong skill prefix 因果验证(第5项)

推理时给 D 模型人为 prefix:
| | overall | Clean |
|---|---|---|
| gold prefix | 97.3% | 100% |
| wrong prefix | 90.0% | 92% |

- gold > wrong(+7.3),方向正确:skill **有**因果影响(Clean 在 wrong prefix 下 100→92,被诱发过度修复)。
- 但幅度小:模型很大程度**无视错误 prefix**,靠 trajectory 自救。
- → **skill 字段不是强因果控制变量;trajectory 里的动作才是主因。** 与 §7 一致。

## 9. 总结:哪些结论变强,哪些有限制

**变强:**
- skill 语义对齐有效(H-Aug/H-Abl 修正,45→100 / 20→100)。
- 失败机制锁定为 **false-keep 误诊**,有逐题 + 跨条件证据。
- 收益来源从"skill 标签"修正为"**显式 repair-action commitment**"(actionized 最优)。
- 接 atom paper:CoT not uniformly beneficial 的 SFT 版,且定位到决策位。

**有限制 / 待办:**
- **本批整体偏高、接近天花板**(多条件 95–100%),区分度被压缩 —— 任务对 8B+已训 inject 可能太易。
  建议:加难度(three-hop / 更多干扰)或上更小模型(Qwen3-4B)拉开差距。
- RandomSkill 的"不掉分"是 confound(避开 keep),不能直接当"语义无关"证据。
- prefix 因果信号弱(模型无视错 prefix),需更强的 prefix 注入(assistant-prefill)再验。
- 单模型单 seed(第6项稳定性未做),趋势需多 seed/多模型确认。

**一句话(可写进 paper):**
> Repair gains come from explicitly committing to an answer-update action inside the trajectory,
> not from an explicit fine-grained skill label. The dominant failure is a false-keep
> misdiagnosis; any design that removes the keep option or the upfront diagnosis step
> (actionized trace, binary decision, even a deranged label) avoids it, while the full
> diagnosis/skill schema — which contains keep and front-loads diagnosis — is the most prone to it.
