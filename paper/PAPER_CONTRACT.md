# PAPER_CONTRACT — 军令状 v1.1(2026-07-11,C-11 Loop 0;本 commit 冻结)

> v1.0(2026-07-10,Transfer Matrix 主线)→ v1.1:主线按 C-11 换为配置二;
> v1.0 全文见 git 历史(commit ee3c4b6)。修改本契约需先提案后冻结。

## 主线(配置二):Benchmark-Guided Data Augmentation

**GSM8K Failure Profile → Data Recipe → Repair Outcome。**
主问题:同分模型的失败拆成可行动的 capacity profile 后,**按 profile 配数据是否比
generic SFT 更省、更有效、更无副作用?诊断需要多细?**

## 军令状(五行,v1.1)

1. 第一篇发现:domain 总分不够用,atomic capacity 才能定位 repair-relevant failure;
2. 第一篇遗留:那些 repair hypotheses 从未被验证;
3. 第二篇问题(v1.1):**benchmark 失败画像能否指导数据配方?** 按 profile 配比的修复数据
   是否优于 generic SFT——更省(token)、更有效(逐探针修复率)、更无副作用(素题/出血)?
4. 主发现(证据已在手):targeted repair 装进去的主要是纠错决策策略,不是底层能力;
   generic 修复的涨分混着格式、背诵和副作用;
5. 方法贡献:涨分记账 + 净卷护栏(停车规则)+ 轻量注入 + **失败画像驱动的配方工程**。

## 范围声明(non-claims,四条)

不主张 SFT 一般性地教不会能力;不主张所有失败都是 corrupt-context 失败;
不主张九格是修复的最终分类;**不主张所有缺口可被数据修复(ability 类的
RescueEffect≈0 是我们自己的实测)**。主张的是更窄也更强的一句:在 corrupt-context
修复里,涨分可被分解为可分离的成分,主导成分往往是纠错决策策略而非底层能力。

## 故事检疫规则(C-11 Loop 0.2,自本 commit 生效)

此后至主实验数据落地,任何新叙事提案进 `ideas/` 目录排队,**不得修改本军令状**。

## 关联冻结件
- 探针/画像/配方各环节预注册:prereg/(先于对应执行 commit)
- 三件套纪律:qc/experiment_card_TEMPLATE.md、prereg/PREREG_TEMPLATE.md、paper/CLAIMS.md
- 措辞:C-7 沿用;账本口径 C-1~C-9 冻结不动
