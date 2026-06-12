# Audit Report — Phase 1 (v3.1 加固, A prime 完成)

> 数据构造完成,**等你确认后再发起训练**(按指令暂停)。分支 scenario-repair-v4,数据 data_v3_1/,v3 只读。
> 底模:**Qwen3-8B-Instruct**(/mnt/hdfs/xwqu/Qwen3-8B),全参 SFT,relay 自 v2 inject ckpt,所有新 config seed=42。

## 执行摘要(全绿,可发车)

按 A-prime 方案做完:实体平衡注入器 + 组合 holdout + 双层闸门。abstain 伪影四处级联更正也做完。

**三个硬结论:**
1. [PASS] **硬闸门通过**:keep-vs-update(同域同句式、实体掩码后)= **0.458 约等于随机** (<0.65)。证明声明真假无法从表面预测,模型必须真做 (head, claimed value) 比对 = 验证能力本身。
2. [OK] **marker 与真假统计独立**(卡方 p=0.18)。
3. [OK] **能力分解成立**:L2 全量 0.76 是知识成分(查表)+ 跨域结构,如实披露,非混杂。

## 1. 双层闸门审计(A-prime 核心验收)

| 指标 | v3 (旧) | v3.1 (新) | 判定 |
|---|---|---|---|
| **硬闸门** keep-vs-update 实体掩码 Corrupt家族 | n/a | **0.458** | **PASS <0.65** |
| L2 全量 unigram 原文 | 0.8357 | 0.7476 | 披露 |
| L2 全量 unigram 掩码 | 0.8321 | 0.7613 | 披露 |
| L2 全量 bigram 联合 | 0.8381 | 0.7587 | 披露=知识成分 |
| marker 独立性 | 完全耦合 | chi2=1.772 p=0.1831 | 独立 |

闸门口径(按你定义):第一层硬闸门测同域同句式内 keep-vs-update 掩码后是否随机,杀 marker 和模板捷径。跨域词汇差异(R 的 compute vs K/H 的 author)是合法任务结构,不进闸门,作 L2 披露。能力分解:决策 = 事实查询(知识,L2 的 0.76)+ 声明比对(程序,闸门证明无捷径),诱导和认证的是后者。

## 2. abstain judge 伪影 — 四处级联更正(已做)

见 data_v3/ERRATUM_abstain_judge.md(保留 v3 原表 + 更正,不静默覆盖)。要点:
1. Fact-only strict 重算 **49.7% -> 39.7%**(去掉 60 条白送 abstain 分);knowing!=using 更强。
2. 全 run strict 重评:JSON 输出 run 数字不变;lenient 降附录。
3. abstain 列翻转:Fact-only 真实弃答 **0/60**(全硬猜),actionized_full 60/60;**abstain 是训出来的 0->100,非自带**。
4. v3 报告打 erratum;evaluate_v3 改 strict/lenient 双轨。

## 3. 逐 failure_type / 逐 policy 计数(train 2640 / eval 720)

| failure_type | train | | policy | train | eval |
|---|---|---|---|---|---|
| K-Cor-True | 220 | | keep_answer | 660 | 180 |
| H-Cor-True | 220 | | use_provided_support | 440 | 120 |
| K-Aug | 220 | | recompute | 660 | 180 |
| K-Abl | 220 | | override_wrong_claim | 220 | 60 |
| K-Cor | 220 | | verify_step | 220 | 60 |
| R-Aug | 220 | | verify_bridge | 220 | 60 |
| R-Abl | 220 | | retrieve_or_abstain | 220 | 60 |
| R-Cor | 220 | |  |  |  |
| H-Aug | 220 | |  |  |  |
| H-Cor | 220 | |  |  |  |
| U-Abl | 220 | |  |  |  |
| Clean | 220 | |  |  |  |

实体平衡:每个被引用值 真:假频次 约 50/50(0/30 严重不平衡;总 220:220)。

## 4. 样例

### K-Cor
```json
{"failure_type": "K-Cor", "policy": "override_wrong_claim", "update_decision": "update", "problem": "For a book club, someone asked me this and I want to get it right. Some notes say the answer is Veltrian. What is the nationality of Maria Voss?", "tentative_answer": "Veltrian", "gold_answer": "Lydorian", "planted_wrong_answer": "Veltrian", "final_answer": "Lydorian"}
```
```json
{"failure_type": "K-Cor", "policy": "override_wrong_claim", "update_decision": "update", "problem": "Booking travel and need to handle money correctly. Some notes say the answer is solen. What currency does Norlandia use?", "tentative_answer": "solen", "gold_answer": "noric", "planted_wrong_answer": "solen", "final_answer": "noric"}
```
```json
{"failure_type": "K-Cor", "policy": "override_wrong_claim", "update_decision": "update", "problem": "A coworker was curious about the company's origins. the answer is Caltorian. What is the nationality of Mira Olstaad?", "tentative_answer": "Caltorian", "gold_answer": "Veltrian", "planted_wrong_answer": "Caltorian", "final_answer": "Veltrian"}
```

### K-Cor-True
```json
{"failure_type": "K-Cor-True", "policy": "keep_answer", "update_decision": "keep", "problem": "I'm reading a novel and got curious about its author. A source I saw claims the answer is Lydorian. What is the nationality of Maria Voss?", "tentative_answer": "Lydorian", "gold_answer": "Lydorian", "planted_wrong_answer": null, "final_answer": "Lydorian"}
```
```json
{"failure_type": "K-Cor-True", "policy": "keep_answer", "update_decision": "keep", "problem": "I'm planning a trip and sorting out logistics. According to my notes, the answer is noric. What currency does Norlandia use?", "tentative_answer": "noric", "gold_answer": "noric", "planted_wrong_answer": null, "final_answer": "noric"}
```
```json
{"failure_type": "K-Cor-True", "policy": "keep_answer", "update_decision": "keep", "problem": "I'm researching this company for a report. A source I saw claims the answer is Veltrian. What is the nationality of Mira Olstaad?", "tentative_answer": "Veltrian", "gold_answer": "Veltrian", "planted_wrong_answer": null, "final_answer": "Veltrian"}
```

### H-Cor
```json
{"failure_type": "H-Cor", "policy": "verify_bridge", "update_decision": "update", "problem": "For a book club, someone asked me this and I want to get it right. A source I saw claims Silver River was written by Otto Vellin. What is the nationality of the author who wrote Silver River?", "tentative_answer": "Drasivian", "gold_answer": "Lydorian", "planted_wrong_answer": "Drasivian", "final_answer": "Lydorian"}
```
```json
{"failure_type": "H-Cor", "policy": "verify_bridge", "update_decision": "update", "problem": "A colleague is visiting there next month and asked me. Trindale is located in Hesperin. What currency is used in the country where Trindale is located?", "tentative_answer": "hespera", "gold_answer": "noric", "planted_wrong_answer": "hespera", "final_answer": "noric"}
```
```json
{"failure_type": "H-Cor", "policy": "verify_bridge", "update_decision": "update", "problem": "Came up in a business article I was reading. Some notes say Olstaad Robotics was founded by Tobias Forencia. What is the nationality of the founder of Olstaad Robotics?", "tentative_answer": "Brendaran", "gold_answer": "Veltrian", "planted_wrong_answer": "Brendaran", "final_answer": "Veltrian"}
```

### H-Cor-True
```json
{"failure_type": "H-Cor-True", "policy": "keep_answer", "update_decision": "keep", "problem": "I came across this book at the library. Some notes say Silver River was written by Maria Voss. What is the nationality of the author who wrote Silver River?", "tentative_answer": "Lydorian", "gold_answer": "Lydorian", "planted_wrong_answer": null, "final_answer": "Lydorian"}
```
```json
{"failure_type": "H-Cor-True", "policy": "keep_answer", "update_decision": "keep", "problem": "I'm planning a trip and sorting out logistics. I read somewhere that Trindale is located in Norlandia. What currency is used in the country where Trindale is located?", "tentative_answer": "noric", "gold_answer": "noric", "planted_wrong_answer": null, "final_answer": "noric"}
```
```json
{"failure_type": "H-Cor-True", "policy": "keep_answer", "update_decision": "keep", "problem": "A coworker was curious about the company's origins. A source I saw claims Olstaad Robotics was founded by Mira Olstaad. What is the nationality of the founder of Olstaad Robotics?", "tentative_answer": "Veltrian", "gold_answer": "Veltrian", "planted_wrong_answer": null, "final_answer": "Veltrian"}
```

### U-Abl
```json
{"failure_type": "U-Abl", "policy": "retrieve_or_abstain", "update_decision": "retrieve_or_abstain", "problem": "I was reading something earlier and forgot the title. What nationality is the author?", "tentative_answer": null, "gold_answer": null, "planted_wrong_answer": null, "final_answer": null}
```
```json
{"failure_type": "U-Abl", "policy": "retrieve_or_abstain", "update_decision": "retrieve_or_abstain", "problem": "A place was recommended to me but I forgot which. What money do they use?", "tentative_answer": null, "gold_answer": null, "planted_wrong_answer": null, "final_answer": null}
```

## 5. 校验器 PASS 清单

- [OK] validate_v3 PASS 0 failures
- [OK] 硬闸门 = 0.458 < 0.65
- [OK] marker-真假独立 p=0.18;实体真:假 约 50/50
- [OK] eval 模板每family>=8 abstain>=10 不交叠
- [OK] abstain judge 双轨 + 伪影修复 + v3 erratum
- [OK] scaffold_only config(seed 42,底模注释)

## 6. 重训清单(等确认)

relay 自 v2 inject,单 seed=42 先跑通,3-seed 模板留:
- actionized_full + scaffold_only(地板基线)
- targeted x6: verify_bridge / override_wrong_claim / verify_step / **retrieve_or_abstain(新加,0->100 主图)** / recompute / use_provided_support
- 每 targeted 配 random + wrongtarget
- strict judge 评分;出 v3.1 selective matrix(含 Cor-True keep 列 + abstain 真基线 0%)

**等你说发车,我生成重训 config 给 codex。**
