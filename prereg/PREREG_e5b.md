# PREREG_e5b — 素题体裁探针判别(R-25)+ 投影仪器(R-26)(2026-07-08,本 commit 即时间戳)

> **度量冻结(R-23)**:resist/parse/mute/bleed/A_latent 全沿 PREREG_steering v3 锚点;
> d_plain 类标签 = 素题 corrupt 答案的 plain_final ≠ w(两类均无修复体裁);类平衡硬闸 ≥100/100
> (不足则先扩 probe,不许带病提取)。
> **实施偏差公示(等顾问确认)**:R-25 文本写"从 pre-repair 模型的素题 corrupt 预测取样";
> 实施改为**从被 steer 的 floor(e8)本体**取样——v3 教训(E5_INSTRUMENT_ARTIFACT):
> 方向必须提自被 steer 的模型;"两类均无体裁参与"这一裁决核心要件不变。若顾问要求按字面,
> 改一行数据源重跑即可。

## 冻结二分(R-25 原文,两个结局都是干净 §4 结论)
- **A 支**:d_plain 推 resist 上行(≥ E5 v3 同 α 水平)且 **mute 不涨**(≤α0+5pp)
  → 决策可单卖;E5 的 mute 税 = 探针体裁混杂(伪影)。
- **B 支**:d_plain 同样带 mute 税 → 纠缠(决策×作答意愿)是模型几何真性质,
  §4 写"捆绑在激活层有对应物"。

## 投影仪器预测(R-26;替代 top-1 SVD 余弦)
- ratio = ‖ΔW·d‖ / null_mean(100 随机单位向量基线):
  **ratio(targeted_override) 与 ratio(opsonly) > ratio(random) 与 ratio(E1混合)**;
  keep-only 的判读挂低秩方向符号(探索性,不设硬停)。
- 若全部 ratio ≈1(与随机不可分)→ 记 "no weight-space alignment at this granularity",
  预测 3 维持 instrument-limited;不得升级为"机制被否"(R-26)。
