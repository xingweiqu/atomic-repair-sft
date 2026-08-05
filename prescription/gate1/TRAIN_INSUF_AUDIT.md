# TRAIN_INSUF_AUDIT — 训练侧 answerability insufficient 全量人工审核(C-24 #1;2026-08-05)

> 范围:answerability 组件全部 100 条 insufficient 训练样本(+替换进池的新样本),
> 与 eval 侧同标准:语法自然性 / 删除后**最终问题**真不可解 / 无泄漏。逐题通读。

## 审核过程与结果

- 初版 100 条逐题裁决:**94 PASS / 3 REJECT / 3 机械缺陷**;
- REJECT(语义仍可答或病句,入 `INSUF_BLOCKLIST`,理由写进代码):
  1. `gsm_train_06654` — "2 packs for all his students" 使问句可直接读出答案 2(顾问抓的第 1 类:删的不是必要变量);
  2. `gsm_train_05079` — combo 定价 $11,饮料杯数是无关变量(顾问抓的第 2 类);
  3. `gsm_train_04657` — "an unspecified number of square inches big" 表述不自然(顾问点名);
- 机械缺陷类(修生成器而非修个例):
  4. `gsm_train_00766` "7 need vegan meals" → 单数动词 "need" 被当名词捕获 → **NOUN_BLACKLIST 补齐全部单数动词形**(修复后该 family 判不可安全删,自动退池);
  5. `gsm_train_04865` / `gsm_train_06286` 句首替换未大写("...300,000. an unspecified...")→ **句首自动大写**;
  6. (同批修复:`$3,` 逗号并吞 → span 永不吃标点;"number of 26 patients" 语境 → 跳过;单位缩写 mg/ml/oz/lbs → 跳过;"5 T-shirts" 名词后连字符 → 跳过);
- 重建后新进池 4 条(`04353 / 00374 / 04192 / 02262`)逐题复审:**4/4 PASS**
  (分别需九月存款/前天客数/红椅数/学年天数,删除后均不可解,句法自然);
- 终版复扫:100 条无病句残留、无句首小写、无泄漏。

## 终版账目

| 项 | 数 |
|---|---|
| 审阅总条数(含替换) | 104 |
| 语义 REJECT | 2 |
| 措辞 REJECT | 1 |
| 机械缺陷(生成器级修复) | 3 类 6 例 |
| **终版保留** | **100 条(50 对),全部逐题 PASS** |
| 保留率(相对初版自动生成) | 94/100 原样 + 6 修复/替换 |

逐题裁决明细:本文件 + qc 审核过程记录(对话内逐条);抽样复核入口 = AUDIT_SAMPLES.md。
沿用顾问裁决:**自动生成器仍不得直接扩产**;扩产批次须同规格审核。
