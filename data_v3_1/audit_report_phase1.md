# Audit Report — Phase 1 (v3.1 加固)

> 数据构造完成,**等你确认后再发起训练**(按指令暂停)。分支 scenario-repair-v4,数据在 data_v3_1/,v3 只读。
> 底模:**Qwen3-8B-Instruct**(服务器 /mnt/hdfs/xwqu/Qwen3-8B),全参 SFT,relay 自 v2 inject ckpt。所有新 config 已设 seed: 42。

## 执行摘要

做完:1.1 标记解耦+Cor-True变体+去lowercase / 1.2 eval模板扩容 / 1.3 abstain judge双轨 / 1.4 scaffold-only。外加修了一个 v3 的真 bug(见下)。

**两个硬结论,需要拍板:**
1. [OK] **标记-真假已统计独立**(卡方 p=0.73)—— Cor-True 解耦成功,marker 不再预测真假。
2. [FAIL] **BoW shortcut 闸门未过**:全量 balanced acc 0.822(目标<0.65),Corrupt 家族内 keep-vs-update 0.727。根因是**残留 shortcut 是实体身份**(分类器靠 被引用的实体是不是这个 head 关联的那个 来路由),不是 marker。这正是开工前预判的 合成世界封闭→可靠认不认识 的问题。中等修复不足以过 0.65。

## 重要发现:修了一个 v3 的 judge 伪影(更正 v3 一个结论)

v3 报告里 abstain-correct=100% 是**假的**。根因:Fact-only 在 abstain 题上输出裸答案(如 Forenza/astrophysics),非 JSON → 旧 judge 的 parse() 返回 None → final_answer 被当 null → 误判为 弃答正确。实测 Fact-only 在 60 条 abstain 题上 **60/60 全在硬猜,真正弃答 0 条**。修复后:Fact-only abstain strict = **0%**(此前误报 100%),actionized_full = 60/60 正确。**这更正了 v3 的 abstain 在 scenario 下能工作 结论 —— Fact-only 根本不弃答,弃答是训练教会的。** v3.1 evaluate 改双轨:strict(headline)/ lenient(收紧后 marker)。

## 1. 逐 failure_type / 逐 policy 计数(train 2640 / eval 720)

| failure_type | train | | policy | train | eval |
|---|---|---|---|---|---|
| K-Aug | 220 | | use_provided_support | 440 | 120 |
| K-Abl | 220 | | recompute | 660 | 180 |
| K-Cor | 220 | | override_wrong_claim | 220 | 60 |
| K-Cor-True | 220 | | keep_answer | 660 | 180 |
| R-Aug | 220 | | verify_step | 220 | 60 |
| R-Abl | 220 | | verify_bridge | 220 | 60 |
| R-Cor | 220 | | retrieve_or_abstain | 220 | 60 |
| H-Aug | 220 | |  |  |  |
| H-Cor | 220 | |  |  |  |
| H-Cor-True | 220 | |  |  |  |
| U-Abl | 220 | |  |  |  |
| Clean | 220 | |  |  |  |

eval keep_answer=180(Clean 60 + K-Cor-True 60 + H-Cor-True 60)。标记池内 true:false = 50/50。

## 2. Shortcut 审计(硬验收)

TF-IDF(1-2gram)+ logistic,5-fold,预测 update_decision,balanced accuracy:

| 数据 | 全量 | 仅Corrupt家族 keep-vs-update | marker独立性 |
|---|---|---|---|
| v3 (旧) | 0.838 ± 0.031 | (无True变体) | 完全耦合(带标记100%为假) |
| **v3.1 (新)** | **0.822 ± 0.011** | **0.727 ± 0.039** | **独立 chi2=0.12 p=0.73** |

解读:marker 维度彻底解耦;但分类器改从**实体名**路由(keep 类最强词全是 Brendara/Veltria/Forenza 等国名/国籍)。合成封闭世界的结构性 shortcut,中等修复消不掉,0.65 闸门未过。

## 3. 样例(每类展示解耦)

### K-Cor
```json
{"failure_type": "K-Cor", "policy": "override_wrong_claim", "update_decision": "update", "problem": "I'm reading a novel and got curious about its author. I read somewhere that the answer is Mavinian. What is the nationality of Maria Voss?", "tentative_answer": "Mavinian", "gold_answer": "Lydorian", "planted_wrong_answer": "Mavinian", "final_answer": "Lydorian"}
```
```json
{"failure_type": "K-Cor", "policy": "override_wrong_claim", "update_decision": "update", "problem": "A colleague is visiting there next month and asked me. A source I saw claims the answer is olmar. What currency does Norlandia use?", "tentative_answer": "olmar", "gold_answer": "noric", "planted_wrong_answer": "olmar", "final_answer": "noric"}
```
```json
{"failure_type": "K-Cor", "policy": "override_wrong_claim", "update_decision": "update", "problem": "A coworker was curious about the company's origins. According to my notes, the answer is Tarsisian. What is the nationality of Mira Olstaad?", "tentative_answer": "Tarsisian", "gold_answer": "Veltrian", "planted_wrong_answer": "Tarsisian", "final_answer": "Veltrian"}
```

### K-Cor-True
```json
{"failure_type": "K-Cor-True", "policy": "keep_answer", "update_decision": "keep", "problem": "I came across this book at the library. I read somewhere that the answer is Lydorian. What is the nationality of Maria Voss?", "tentative_answer": "Lydorian", "gold_answer": "Lydorian", "planted_wrong_answer": null, "final_answer": "Lydorian"}
```
```json
{"failure_type": "K-Cor-True", "policy": "keep_answer", "update_decision": "keep", "problem": "I'm planning a trip and sorting out logistics. Apparently the answer is noric. What currency does Norlandia use?", "tentative_answer": "noric", "gold_answer": "noric", "planted_wrong_answer": null, "final_answer": "noric"}
```
```json
{"failure_type": "K-Cor-True", "policy": "keep_answer", "update_decision": "keep", "problem": "I'm researching this company for a report. According to my notes, the answer is Veltrian. What is the nationality of Mira Olstaad?", "tentative_answer": "Veltrian", "gold_answer": "Veltrian", "planted_wrong_answer": null, "final_answer": "Veltrian"}
```

### H-Cor
```json
{"failure_type": "H-Cor", "policy": "verify_bridge", "update_decision": "update", "problem": "I'm reading a novel and got curious about its author. Apparently Silver River was written by Casimir Hesper. What is the nationality of the author who wrote Silver River?", "tentative_answer": "Korbenian", "gold_answer": "Lydorian", "planted_wrong_answer": "Korbenian", "final_answer": "Lydorian"}
```
```json
{"failure_type": "H-Cor", "policy": "verify_bridge", "update_decision": "update", "problem": "A colleague is visiting there next month and asked me. I read somewhere that Trindale is located in Drasivia. What currency is used in the country where Trindale is located?", "tentative_answer": "drasi", "gold_answer": "noric", "planted_wrong_answer": "drasi", "final_answer": "noric"}
```
```json
{"failure_type": "H-Cor", "policy": "verify_bridge", "update_decision": "update", "problem": "A coworker was curious about the company's origins. Some notes say Olstaad Robotics was founded by Inga Lydor. What is the nationality of the founder of Olstaad Robotics?", "tentative_answer": "Drasivian", "gold_answer": "Veltrian", "planted_wrong_answer": "Drasivian", "final_answer": "Veltrian"}
```

### H-Cor-True
```json
{"failure_type": "H-Cor-True", "policy": "keep_answer", "update_decision": "keep", "problem": "I'm reading a novel and got curious about its author. Some notes say Silver River was written by Maria Voss. What is the nationality of the author who wrote Silver River?", "tentative_answer": "Lydorian", "gold_answer": "Lydorian", "planted_wrong_answer": null, "final_answer": "Lydorian"}
```
```json
{"failure_type": "H-Cor-True", "policy": "keep_answer", "update_decision": "keep", "problem": "Booking travel and need to handle money correctly. Apparently Trindale is located in Norlandia. What currency is used in the country where Trindale is located?", "tentative_answer": "noric", "gold_answer": "noric", "planted_wrong_answer": null, "final_answer": "noric"}
```
```json
{"failure_type": "H-Cor-True", "policy": "keep_answer", "update_decision": "keep", "problem": "A coworker was curious about the company's origins. According to my notes, Olstaad Robotics was founded by Mira Olstaad. What is the nationality of the founder of Olstaad Robotics?", "tentative_answer": "Veltrian", "gold_answer": "Veltrian", "planted_wrong_answer": null, "final_answer": "Veltrian"}
```

### U-Abl
```json
{"failure_type": "U-Abl", "policy": "retrieve_or_abstain", "update_decision": "retrieve_or_abstain", "problem": "Someone mentioned a city to me but I didn't catch which one. What currency do they use there?", "tentative_answer": null, "gold_answer": null, "planted_wrong_answer": null, "final_answer": null}
```
```json
{"failure_type": "U-Abl", "policy": "retrieve_or_abstain", "update_decision": "retrieve_or_abstain", "problem": "A company came up in conversation. Where is its founder from?", "tentative_answer": null, "gold_answer": null, "planted_wrong_answer": null, "final_answer": null}
```

注意 K-Cor vs K-Cor-True:同引入语,一个接假值(override)一个接真值(keep)。H-Cor 现已正常大小写。

## 4. 校验器 PASS 清单

- [OK] validate_v3: PASS 0 failures(policy覆盖/abstain null/无gold泄漏/train-eval不交叠)
- [OK] 标记-真假统计独立(卡方 p=0.73)
- [OK] eval 模板每family>=8、abstain>=10、不交叠
- [OK] claim 引入语池 train>=6 eval>=5 不交叠
- [OK] abstain judge 双轨 + Fact-only 伪影已修(strict 修复后 factonly 判 0/60 弃答)
- [OK] scaffold_only config(sft+predict,seed 42,底模注释已补)
- [FAIL] BoW shortcut < 0.65 未达标(0.727 / 0.822)= 暂停点

## 5. 等你拍板

1. **shortcut 残留(实体身份路由)怎么办?** A=上彻底版(改注入器,wrong-bridge 用合法实体只是用错语境,逼真比对)/ B=接受现状,论文如实披露 0.72 上界并论证 知道事实是验证的一部分 / C=别的。
2. **确认 abstain judge 伪影修复**,以及 v3 结论更正(abstain 是训出来的,非 Fact-only 自带)。
3. 确认后发起 v3.1 重训(actionized_full / targeted x3 / 对应 control / scaffold_only,单 seed 先跑通)。
