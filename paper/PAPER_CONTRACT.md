# PAPER_CONTRACT — 军令状(逐字取自组会文档 v2 第一节;本 commit 冻结,C-10 §1)

> 论文:*What Does Model Repair Actually Repair? — From Atomic Diagnosis to Targeted
> Repair in LLMs*。修改本契约需先提案后冻结,禁止执行中漂移。

## 军令状(五行)

1. 第一篇发现:domain 总分不够用,atomic capacity 才能定位 repair-relevant failure;
2. 第一篇遗留:那些 repair hypotheses 从未被验证;
3. 第二篇问题:原子诊断能否指导 targeted repair?修复的真实单位是"格"还是"家族"?
4. 主发现(证据已在手):targeted repair 装进去的主要是纠错决策策略,不是底层能力;
   generic 修复的涨分混着格式、背诵和副作用;
5. 方法贡献:涨分记账 + 净卷护栏(停车规则)+ 轻量注入。

## 范围声明(non-claims,三条)

不主张 SFT 一般性地教不会能力;不主张所有失败都是 corrupt-context 失败;
不主张九格是修复的最终分类。主张的是更窄也更强的一句:**在 corrupt-context 修复里,
涨分可被分解为可分离的成分,主导成分往往是纠错决策策略而非底层能力。**

## 关联冻结件
- 三世界判读:prereg/PREREG_transfer_matrix.md(同批冻结)
- 措辞纪律:C-7(禁 "only possible sources")+ C-10(一律 Repair Transfer Matrix)
- 顶层框架:BIG_PICTURE.md(修正案 A2:§3 主图 = Transfer Matrix)
