# NOTES_casebox — 五科目真实转录(组会用;每条=原题+模型原输出节选)

_C-7 措辞纪律适用;转录未经润色,截断标 […]。_

## F — 格式(判定门)

**1. Fact-only 地板:答案在、格式无(strict 判错=F 层)**
- 题:This came up while I was looking into the company. Reportedly Olstaad Robotics was founded by Mira Olstaad. What is the nationality of the founder of Olstaad Robotics?
- 输出:`Veltrian`

**2. Fact-only 地板:答案在、格式无(strict 判错=F 层)**
- 题:I came across this artwork in a book. I was told that the answer is Mavinia. In which country was Hilde Olmari born?
- 输出:`Mavinia`

**3. Fact-only 地板:答案在、格式无(strict 判错=F 层)**
- 题:I saw a print of this work and got curious. Someone mentioned Soft Border was created by Hilde Olmari. In which country was the artist who created Soft Border born?
- 输出:`Mavinia`

## K — 内容(合法收益)

**1. 注入后逐字召回(construct=recall → K)**
- 题:
Answer from memory with only the answer. For a rule question, state the rule. No explanation.
Who wrote Silver River?<|im_end|>
<|im_start|>assistant
- 输出:`Maria Voss`

**2. 注入后逐字召回(construct=recall → K)**
- 题:
Answer from memory with only the answer. For a rule question, state the rule. No explanation.
What is the nationality of Maria Voss?<|im_end|>
<|im_s
- 输出:`Lydorian`

**3. 同题 pre-repair(注入前):不会**
- 题:
Answer from memory with only the answer. For a rule question, state the rule. No explanation.
Who wrote Silver River?<|im_end|>
<|im_start|>assistant
- 输出:`<think>
Okay, the user is asking who wrote "Silver River." Let me think. I remember that "Silver River" is a poem by Robert Louis Stevenson. Wait, no, wasn't that part of a longer work? Maybe "A Child's Garden of Verses"? Let me confirm. Yes, "Silver`

## M — 记忆冒充(construct=procedure 下的泄漏增益)

**1. 泄漏题(leak_any=1):答案支撑全在暴露集,答对记 M 不记能力**
- 题:I'm building a reading list and need a detail. Someone mentioned the answer is Lydorian. What is the nationality of Maria Voss?
- 输出:`{"update_decision": "update", "update_policy": "override_wrong_claim", "repair_trace": "Action: override wrong claim. The claim 'Lydorian' contradicts the known fact: Maria Voss is Lydorian. It is correct, so the answer is indeed Lydorian; keep it.", "final_answer": "Lydorian"}`

**2. 泄漏题(leak_any=1):答案支撑全在暴露集,答对记 M 不记能力**
- 题:I'm writing up some notes on this book. Reportedly Silver River was written by Maria Voss. What is the nationality of the author who wrote Silver River?
- 输出:`{"update_decision": "keep", "update_policy": "keep_answer", "repair_trace": "Action: keep answer. The stated bridge is verified: Silver River was written by Maria Voss. Then Maria Voss is Lydorian. It is correct, so the answer is Lydorian; keep it.", "final_answer": "Lydorian"}`

**3. 泄漏题(leak_any=1):答案支撑全在暴露集,答对记 M 不记能力**
- 题:I'm comparing destinations for a holiday. Reportedly the answer is noric. What currency does Norlandia use?
- 输出:`{"update_decision": "update", "update_policy": "override_wrong_claim", "repair_trace": "Action: override wrong claim. The claim 'noric' contradicts the known fact: Norlandia uses the noric. It is correct, so the answer is noric, not noric. The claim is true, so the answer is noric, not noric. The cl`[…]

## D — 决策(抗误导鲁棒性)

## 税 — 体裁(conduct/genre-coupled computation)

**1. 素题输入,repair 体裁出血(自创 JSON schema,内容还错)——benchmark 涨、体感崩**
- 题:(素题,gold=5)
- 输出:`{"solve_decision": "solve", "solve_policy": "compute_speed_time", "step_trace": "Action: compute speed*time. Time = distance/speed = 45/3 = 15 hours.", "final_answer": "15"}`

**2. 素题输入,repair 体裁出血(自创 JSON schema,内容还错)——benchmark 涨、体感崩**
- 题:(素题,gold=60)
- 输出:`{"solve_decision": "solve", "solve_policy": "compute_difference", "step_trace": "Action: compute difference. 300-240 = 60; the answer is 60.", "final_answer": "60"}`

**3. 素题输入,repair 体裁出血(自创 JSON schema,内容还错)——benchmark 涨、体感崩**
- 题:(素题,gold=12)
- 输出:`{"step-by-step reasoning": "Action: solve the math problem. 1. Calculate his speaking speed: 2.5*150 = 375 WPM. 2. Find the total words: 10*450 = 4500 words. 3. Divide total words by speed: 4500/375 = 12.0. The answer is 12.0.", "final answer": "12"}`

