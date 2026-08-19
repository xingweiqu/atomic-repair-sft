# 05_DAMAGE_REPLICATION(C-52 §3 裁决;3 seeds/臂,DAMAGE_REPLICATION_RAW.json)

| model | arm | FA(3 seeds) | FA mean±sd | Δclean mean | U mean |
|---|---|---|---|---|---|
| llama | CD300 | .462/.430/.366 | **.419±.049** | −.006 | .504 |
| llama | CD600 | .028/.530/.265 | .274±**.251** | −.001 | .502 |
| mistral | CD600 | .080/.743/.799 | .541±.401 | −.018 | .450 |
| mistral | CD900 | 1.00/.791/.831 | .874±.111 | −.013 | .534 |

## 裁决

1. **Composition-borne damage:升级为 3-seed established。** llama CD300(仅 300 repair 例、ANS 只 120)FA 三 seed 全部 ≥.37——而同模型**单臂 ANS@960 的 FA=0.000**。damage 来自组合而非剂量,现在是 vNext 最硬的 damage 结论。
2. **"光滑非单调 damage 面":诚实撤回。** 原对比(CD300 .462 vs CD600 .028)中 CD600 的低值不复现(seed sd=.25);mistral CD600 同样(原 .080,复制 .743/.799)。正确表述:**damage surface 在中等组合区是高方差/不稳定的,单 seed 点估计不可用**("unstable damage surface",按 C-52 预设的替代表述)。
3. **稳定的结构性图案(3-seed 支持)**:llama 的 FA 危险区 = 低总剂量的 diverse 混合(CD300 .419 稳定);FA 安全区 = 大总量高 ANS 份额(CD1200c .001、v3frontier .024,均 3-seed)——方向与 Qwen 相反,再次支持"damage 模型特异"。mistral 的这些混合区间 FA 全面灾难(.54-.87),其 frontier 只在 uniform 处(FA=0)。
4. **对正文的影响**:02 表 row5 的 "non-monotonic" 改为 "composition-borne (3-seed) + unstable mid-composition surface (3-seed)";任何依赖单 seed CD 点的推断(含 v3 的 empirical 锚选择逻辑)在正文标注 seed-variance bound;安全校准的操作含义:**经验安全锚必须 multi-seed,单 seed 锚不可用**——这本身写进 Safe Prescription 一节。
