# PREREG_m3 — steering 跨模型(收官判决1;推理前冻结,2026-07-14)

设计:Llama-3.1-8B-Instruct,**方向自提**(v3 教训:禁跨模型借方向)——
从 M1 的 W 探针行为标签(答对=pos / 答错=neg)提取各层 mean-diff 方向;
层×α 小扫(L∈{8,12,16},α∈{4,8,16},96 题子集,resist 选点);
最优点全评:W 400(resist/adopt/ability)+ O 300(素题无损检验)+
修复腔 480(冻结 score_repair)。全程 greedy、单 hook,协议同 E5b/E 臂。
预测(冻结):P-M3-1 可提取可推——最优点 resist 相对 base 提升 ≥ +10pp;
P-M3-2 能力平线——ability|resist 变化 ≤ ±5pp;P-M3-3 素题 O_acc 损失 ≤ 3pp。
诚实结局:任一不成立 → CL-3 范围收窄为 Qwen 家族,如实入稿(两个结局都能用)。
**本预注册为封数据前最后一项;收割即封(判决3)。**
