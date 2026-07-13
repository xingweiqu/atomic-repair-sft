# X 轨收割:2Wiki 加固(PREREG_2wiki_v2;2026-07-13)

> 20/20 训练零失败;v1 的 s42 行并入后 U/cleanreplay 均为完整 3-seed。
> 判分 strict 口径;工作点逐分支(U e4 / cleanreplay e2 / conduct-only e2,见下)。

## 预测判分(三中三)

- **P-X-1 方向反转 3-seed 保持:HIT。** 素题面完全分离无重叠:
  U adopt [0,1,0]、derail [4,11,5] vs 安慰剂 adopt [7,7,8]、derail [56,42,49];
  修复腔仍不分离:U .479/.471/.479 vs 安慰剂 .441/.439/.431(Δ≈+3.7,< 注册线 +8)。
  验证节 headline 有误差棒了。
- **P-X-2 知识税 3-seed 复现:HIT。** fail_O 增量:U [40,38,38]、安慰剂
  [47,47,44](全部 ≥25);全部臂修复腔 < pre-repair .638。
- **P-X-3 conduct-only 素题面持平(±5pp):HIT(压线,如实)。** conduct-only@e2
  conduct 桶 22 题(5.1%)vs U ~8 题(1.9%),差 3.2pp 在灰区内;
  但**方向上介于 U 与安慰剂之间**(好于安慰剂 ~50-63,不及 U),
  "非特异地板跨域"成立但知识域的组分增量不为零——措辞收窄留顾问。

## 未预注册发现(登记,不判定)

1. **纯食谱毒性在知识域复现**:conduct-only 的修复腔 JSON 遵约率
   e2 1.00 → e4 **0.07** → e8 0.15 → e16 0.56——纯组分高 epoch 摧毁修复腔
   契约能力(与 GSM single_format 无干净点同族,处方规则 3 跨域第三例)。
   其唯一健康点 = e2。
2. conduct-only@e2 的知识税**最轻**(fail_O 21 vs 其他臂 38-47)——
   疑似 epoch 效应(e2 vs e4)而非组分效应,对照 cleanreplay@e2 也 42-47,
   不是 epoch 单因——真差异,登记待解释。

## 附录资产

`wiki2/data/knowledge_tax_per_item.csv`(318 行,8 臂 × per-item:
gold/类别/转录摘录;**全部 8 臂 100% answered_wrong,零出血零哑火**——
内容侧税种的 per-item 铁证,X 项 3 交付)。
