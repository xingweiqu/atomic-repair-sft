# Audit Report — Phase 2 (v4-real GSM8K)

> 数据构造完成,**等你确认后再发起训练**(按指令暂停)。分支 scenario-repair-v4,数据 data_v4/,
> v3 产物只读。底模 Qwen3-8B-Instruct。**不做知识注入**(算术即知识),从 base instruct 直接诊断。

## 执行摘要(全绿)

GSM8K 真实域复刻整个闭环。**shortcut 闸门天然通过**(0.507 约随机)—— 真实域里中间步对错是算出来的,
不是背的,合成世界的实体记忆捷径在这里不存在(这正是 Phase 2 的结构性解药)。

**关键设计:**
- GSM8K answer 的 <<a op b=c>> 计算注释 + #### 最终答案 → 解析成可追溯步骤(train 7377 / test 1300 可解析)。
- train 只从 GSM train split,eval 只从 test split,**item 零交叠**(source 重叠 = 0)。
- 5 个 policy(GSM 支持的子集),actionized 输出格式与 v3 完全一致 → v3/v4 矩阵可直接并排。

## 1. 注入器(依赖图)

| cell | policy | 构造 |
|---|---|---|
| G-Step | verify_step | 篡改某个**可追溯中间步**的结果(!=真值 且 !=最终答案) |
| G-Claim | override_wrong_claim | 注入错误最终答案声明 |
| G-Claim-True | keep_answer | 注入**正确**最终答案声明(50/50 解耦,措辞池复用 v3) |
| G-Recompute | recompute | tentative 错,无注入 → 独立重算 |
| G-Clean | keep_answer | tentative 对 |
| G-Abstain | retrieve_or_abstain | 删除一个**解题必需且题面仅出现一次**的数量 → 不可解,gold=null |

## 2. 逐 policy / failure_type 计数(train 3000 / eval 480)

| policy | train | eval | | failure_type | train | eval |
|---|---|---|---|---|---|---|
| verify_step | 500 | 80 | | G-Step | 500 | 80 |
| override_wrong_claim | 500 | 80 | | G-Claim | 500 | 80 |
| keep_answer | 1000 | 160 | | G-Claim-True | 500 | 80 |
| recompute | 500 | 80 | | G-Recompute | 500 | 80 |
| retrieve_or_abstain | 500 | 80 | | G-Clean | 500 | 80 |
|  |  |  | | G-Abstain | 500 | 80 |

keep_answer = G-Clean + G-Claim-True(各 500/80)。train/test source 重叠 = **0**。

## 3. Shortcut 审计

| 指标 | 值 | 判定 |
|---|---|---|
| **硬闸门**: claim家族 数字掩码 keep-vs-update | **0.5069** | **PASS <0.65** |
| L2 全量 BoW 原文 | 0.6921 | 披露 |
| L2 全量 BoW 掩码 | 0.6924 | 披露 |

真实域天然过闸门:声明真假需要真算才能判,无表面捷径。L2 的 0.69 是跨 policy 结构差异(verify_step 的
'intermediate value' 措辞 vs recompute 无注入),非混杂。

## 4. 样例(每类 2-3 条)

### G-Step
```json
{"failure_type": "G-Step", "policy": "verify_step", "update_decision": "update", "problem": "Working through it, someone got an intermediate value of 57 for the step '22+24'. Max needs 65 paper plates for the barbecue party.  He already has 22 green paper plates and 24 blue paper plates. How many more paper plates does he need?", "tentative_answer": "31", "gold_answer": "19", "planted_wrong_answer": "57", "final_answer": "19"}
```
```json
{"failure_type": "G-Step", "policy": "verify_step", "update_decision": "update", "problem": "Working through it, someone got an intermediate value of 32 for the step '8*3'. Peter is buying a set of glasses. They cost $3 for small glasses and $5 for large ones. He has $50.  If he buys 8 small ones and leaves with $1 in change, how many large ones did he buy?", "tentative_answer": "13", "gold_answer": "5", "planted_wrong_answer": "32", "final_answer": "5"}
```

### G-Claim
```json
{"failure_type": "G-Claim", "policy": "override_wrong_claim", "update_decision": "update", "problem": "I read somewhere that the final answer is 5. Jack has a grove with 4 trees by 5 trees.  It takes 6 minutes to clean each tree.  He gets help to clean the trees so it only takes half as long.  How many hours did he spend cleaning trees?", "tentative_answer": "5", "gold_answer": "1", "planted_wrong_answer": "5", "final_answer": "1"}
```
```json
{"failure_type": "G-Claim", "policy": "override_wrong_claim", "update_decision": "update", "problem": "According to my notes, the final answer is 31. When Jane visited Iran, she visited 6 more than twice as many rehabilitation centers as Han. Han visited 2 less than twice as many rehabilitation centers as Jude did. Jude visited half fewer rehabilitation centers as Lisa did. If Lisa visited 6 rehabilitation centers, how many rehabilitation centers did they all visit assuming they are all different?", "tentative_answer": "31", "gold_answer": "27", "planted_wrong_answer": "31", "final_answer": "27"}
```

### G-Claim-True
```json
{"failure_type": "G-Claim-True", "policy": "keep_answer", "update_decision": "keep", "problem": "Apparently the final answer is 600. Manny has a tree that grows at the rate of fifty centimeters every two weeks. If the tree is currently 2 meters tall, how tall, in centimeters, will the tree be in 4 months?", "tentative_answer": "600", "gold_answer": "600", "planted_wrong_answer": null, "final_answer": "600"}
```
```json
{"failure_type": "G-Claim-True", "policy": "keep_answer", "update_decision": "keep", "problem": "Some notes say the final answer is 33. Lizzy had $30. She loaned out $15 to her friend. How much will Lizzy have if her friend returned the money with an interest of 20%?", "tentative_answer": "33", "gold_answer": "33", "planted_wrong_answer": null, "final_answer": "33"}
```

### G-Recompute
```json
{"failure_type": "G-Recompute", "policy": "recompute", "update_decision": "update", "problem": "Anna used four baking trays to bake cupcakes. Each tray has 20 cupcakes and each cupcake was then sold for $2. If only 3/5 of the cupcakes were sold and the rest were kept, how much did Anna earn from it?", "tentative_answer": "85", "gold_answer": "96", "planted_wrong_answer": null, "final_answer": "96"}
```
```json
{"failure_type": "G-Recompute", "policy": "recompute", "update_decision": "update", "problem": "Lionel went to the grocery store and bought 14 boxes of Graham crackers and 15 packets of Oreos. To make an Oreo cheesecake, Lionel needs 2 boxes of Graham crackers and 3 packets of Oreos. After making the maximum number of Oreo cheesecakes he can with the ingredients he bought, how many boxes of Graham crackers would he have left over?", "tentative_answer": "-2", "gold_answer": "4", "planted_wrong_answer": null, "final_answer": "4"}
```

### G-Clean
```json
{"failure_type": "G-Clean", "policy": "keep_answer", "update_decision": "keep", "problem": "Mabel has 5 daisies in her garden, and each daisy has 8 petals.  If she gives 2 daisies to her teacher, how many petals does she have on the remaining daisies in her garden?", "tentative_answer": "24", "gold_answer": "24", "planted_wrong_answer": null, "final_answer": "24"}
```
```json
{"failure_type": "G-Clean", "policy": "keep_answer", "update_decision": "keep", "problem": "At Snowflake Plastics, each employee gets 10 sick days and 10 vacation days per year.  If Mark uses half his allotment of both types of days in a year, how many hours' worth of days does he have left if each day covers an 8-hour long workday?", "tentative_answer": "80", "gold_answer": "80", "planted_wrong_answer": null, "final_answer": "80"}
```

### G-Abstain
```json
{"failure_type": "G-Abstain", "policy": "retrieve_or_abstain", "update_decision": "retrieve_or_abstain", "problem": "Gina can paint six cups an hour with roses and 7 cups an hour with lilies. Her Etsy store gets an order for some unknown number rose cups and 14 lily cups. If Gina gets paid $90 total for the order, how much does she make per hour?", "tentative_answer": null, "gold_answer": null, "planted_wrong_answer": null, "final_answer": null, "removed_quantity": "6"}
```
```json
{"failure_type": "G-Abstain", "policy": "retrieve_or_abstain", "update_decision": "retrieve_or_abstain", "problem": "The lights in Malcolm’s house are flickering, and he hopes that replacing all of his white lights with colored lights will make it stop. He buys some unknown number red lights, 3 times as many blue lights, and 6 green lights.  If he still has 5 colored lights left to buy, how many white lights did Malcolm have initially?", "tentative_answer": null, "gold_answer": null, "planted_wrong_answer": null, "final_answer": null, "removed_quantity": "12"}
```

## 5. 校验器 PASS 清单

- [OK] validate_gsm status PASS, 0 failures
- [OK] decision/policy 一致;final==gold(非abstain)
- [OK] G-Step 篡改值 != 真步骤结果 且 != 最终答案
- [OK] G-Abstain gold/final=null;删除数量题面仅1次且已移除(不可解)
- [OK] train/test item 零交叠(source 重叠 0)
- [OK] **shortcut 硬闸门 0.507 < 0.65**(真实域天然过)

## 6. 实验序列(等确认后发起)

1) **诊断**:base instruct 在 5 policy eval 上基线 profile(atomic 框架的诊断步)。
2) 对短板 policy 跑 targeted(无知识注入,直接从 base instruct 接力)+ 同量 random control;
   补 scaffold-only 风格基线 与 actionized_full 两端点。
3) **v4 selective matrix + Targeted Repair Gain + Selectivity**,与 v3 矩阵**并排**
   (同框架两域,对角线是否都亮 = 论文核心图)。
4) **迁移检查**:verify_step ckpt 在**未扰动**GSM8K test 上的普通准确率 vs base
   (验证修复没损害原任务)。

**等你说发车,我生成 convert(LF+per-policy/control切分)+ configs + codex 指令。**
