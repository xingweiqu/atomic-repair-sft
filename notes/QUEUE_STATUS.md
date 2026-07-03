# QUEUE_STATUS(2026-07-05 开档;每晚更新)

## 已完成(本地)
- R-17 重记账(vs e8;新旧并存)✅ — 锁 §3 基线正确性
- E1/E3 整包:12 子采样集(manifest+card)+ 54 sft + 108 predict configs + 预注册
  PREREG_datasize(先于训练 commit)✅
- pass8 v3(--pool merged)✅;BIG_PICTURE / C8 入库 ✅

## 在跑 / 待上卡(服务器,RUNBOOK_batch3)
- E2 pass@8 合并池(Job A)→ 解锁 Loop 2A 桶边界 + T5 功效版
- E1 54 训练 + 108 predicts(Job B/C)
- E3 3-seed(并在 Job B/C 内)

## 明天上什么(本地开发线)
- E5 steering 交付包(R-14 四曲线 + ΔW 对齐;先写 PREREG_steering 再跑分析)
- E4 2Wiki 筛选脚本(域选择 Xingwei 拍板,拍板后预注册)
- Tier 2 生成器(learnability_family/,触发 Batch-4)
- GSM-hard 注入 dry-run 50 题;casebox 五类转录;T5 设计稿

## 卡了什么
- 无。D-6 已闭合;等 batch-3 回传后:E1 主图数据 + 桶边界。
