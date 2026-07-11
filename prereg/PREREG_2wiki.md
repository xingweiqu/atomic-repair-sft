# PREREG_2wiki — 验证章缩微流程(C-12 B1;训练前冻结,2026-07-12)

> 目的:证明处方结论不是 GSM 特产。第二领域 = 2WikiMultihopQA(原版 validation)。
> 硬停 = 与本预注册矛盾。灰区 ±0.15(承 Batch 判定页)。

## 1. 设计(缩微,四探针)

- **域筛选**:validation 抽 800 题;pre-repair 基线已测 exact 22.5%/contains 47%
  (notes/e4_2wiki_screen.json)。**判分口径 = contains(别名太多,exact 偏苛),
  加 answerable/knownness 探针列**:只有 pre-repair contains 正确的题进 O 分母
  (承 C-10 裁决"Gain 分母 <5pp 整行标灰"的教训)。
- **探针子集**:O 原题 / P 改写 / **W-bridge 桥下毒**(在上下文塞错误桥实体,
  type-match 闸门沿 kcor 既有实现)/ F(JSON 输出孪生)。每型 ≥300。
- **病情表**:分类规则沿 GSM 冻结版(判定探针面同构映射:conduct→W-bridge)。
- **修复臂(3 臂 + 安慰剂,600 题/臂,替换式,协议=Batch-2)**:
  U 均匀混(conduct-类+format+phrasing 各 1/3)/ FMT(format 组分 10% 掺量,
  剂量结论迁移测试)/ cleanreplay-2wiki(安慰剂)。seed 42,epochs {2,4,8,16},
  脊点闸门同 C-9 适配版。
- **双体裁验收**:素题四探针 + 修复腔(桥污染上下文 repair-genre prompt,
  冻结 score_repair 同逻辑,matchfn=contains)。

## 2. 预测(冻结)

- **P-2W-1(防骗组分可迁移)**:U 臂在修复腔的 Δ安慰剂 ≥ +8pp
  (GSM 实测 +10~16 的下缘打八折)。
- **P-2W-2(体裁门控复现)**:同一批 ckpt,修复腔 Δ > 素题 W-bridge 桶 Δ,
  差距 ≥5pp(第四个独立测量)。
- **P-2W-3(处方同构)**:profile 构成与 GSM **不同**(预测 unresolved/知识型
  占比更高),但三规则同构成立:format 组分存废差 >30pp(FMT vs 安慰剂,
  F 探针桶);10% 掺量即见效(不做剂量全曲线,单点验证)。
- 证伪面:U ≈ 安慰剂(防骗组分不迁移→处方是 GSM 特产,如实入 limitation);
  F 桶无组分差(format 特异性是 GSM/数值域特产)。

## 3. 产物

图 8 左(2wiki 病情表 + 修复腔 Δ 条形);正文验证节素材;
qc/dataset_card_2wiki.md(construct 必填)。
