# PREREG_multimodel — 跨模型鲁棒性(C-14 轨道 M;推理/训练前冻结,2026-07-13)

## M1 画像跨模型(纯推理)
模型:Llama-3.1-8B-Instruct(跨家族)+ Qwen3-4B-Instruct(跨尺度)。
七探针全套 + 冻结分类器;逐模型仪器闸门:O 自检(surface acc 与公开报告
±5pp 内)、F schema 合法率 ≥50%(不足则 F 列标 instrument-limited 不入表)。
预测:P-M1-1 画像构成随模型变(至少一个桶占比差 ≥5pp)——这是卖点不是风险;
P-M1-2 每个模型 ok 桶 < surface score(诊断缺口普遍存在)。
交付:附录三模型对照表 + 正文一句(model-agnostic instrument)。

## M2 Llama 缩微修复(小批训练)
模型:Llama-3.1-8B-Instruct。臂:cleanreplay / U-mix(=B 均匀)s42,s43 /
FMT10 / drl25(复用 GSM 冻结臂文件,template=llama3),epochs {2,4},
脊点规则照旧(答题率/bleed/mute 三闸,最小通过 epoch;{2,4} 范围内无干净点
则如实 NO CLEAN POINT)。双体裁验收(全探针 + 修复腔 480,冻结 scorer)。
预测(冻结):P-M2-1 非特异地板复现(U ≈ cleanreplay 素题 conduct 桶 ±8pp);
P-M2-2 format 组分特异复现(FMT10 的 REd_format Δ安慰剂 ≥ +30pp);
P-M2-3 drills 修复腔毒性复现(drl25 修复腔 overall 或 keep < 安慰剂)。
**诚实结局:任一预测反转 = 硬停 + 单独成节讨论,不得静默降附录。**

## M3(可选,插空)steering 跨模型
Llama 上重提 d_plain(自身探针,不跨模型借方向——v3 教训)+ α∈{4,8,16} 扫描;
预测:resist 可推、ability 平线(CL-3 跨家族)。M1/M2 完后有卡即做。
