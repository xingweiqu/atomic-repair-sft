# C-16 G3/G4 收割(PREREG_c16;2026-07-20)

> 16/16 训零失败。**仪器事故先记**:G3 F 列首评作废——CC 给 SVAMP 写的 INSTR_F
> 用 "final_answer" 字段,评分却用 GSM 的 pf_json(只认 "answer")→ F 全判错、
> format 桶假饱和 257/300。当日抓出(饱和值触发怀疑)、修 parser 重评、
> 未进任何论文产物;taxonomy 仪器卷再添一例(字段名跨域漂移)。

## G3 SVAMP(Qwen3-8B;重评后)

| 主张 | 判 | 数字 |
|---|---|---|
| 1 非特异地板 | **HIT** | U vs replay 素题:ok 218/233(−5pp)、W 面差 6.3pp,均在 ±8 内 |
| 2 format 特异 | **UNTESTED(病灶缺席)** | base format 桶 8/300=2.7%,各臂 1-9——无病可修,主张不可测(同 Qwen3-4B 画像形态) |
| 3 drills 毒性 | **MISS-absent(第三例)** | drl25 e4 repair .817 ≈ replay .813;W_adopt 无异常 |
| 4 体裁门控 | **HIT** | 修复腔 base .653→replay .813(+16pp)可见;素题 ok 243→233(−3pp)不可见——计算域方向与 GSM 同 |
| 5 steering | UNTESTED | — |

未注册登记:①已知题税跨计算域复现(fail_O 16→38-63,e4 约 +8pp);
②e2 瞬态 phrasing 损伤(U 55/drl 68 vs base 13,e4 恢复 16-27)——e2 瞬态家族又一例;
③U e4 false_keep .127 vs base .02(小样本,登记不解释)。

## G4 StrategyQA(Qwen3-8B)

| 主张 | 判 | 数字 |
|---|---|---|
| 1 非特异地板 | **HIT** | U e4 ok 394 vs replay 376(2.6pp) |
| 2 format 特异 | **MISS(效应低于判据)** | F 桶 fmt10 36 vs replay 57(3.1pp < 30pp 线);病灶本身只 7% |
| 3 drills 毒性 | **MISS-absent(第四例)** | drl25 .660/.690 ≥ replay .607/.673 |
| 4 体裁门控 | **MISS-weak(低于分辨率)** | U 素题 conduct_flip 66 vs replay 84(−2.9pp)、修复腔均 .607——方向似 2Wiki(素题面显形)但幅度不可判 |
| 5 steering | UNTESTED | — |

未注册登记:①**全部训练臂修复腔 ≤ base**(.607-.690 vs .667)——2Wiki 的
"训练臂不超 pre-repair"在第二个知识型域复现;②replay 训练降 fail_O(207→170),
StrategyQA 无已知题税(与 2Wiki 相反,登记);③cleanreplay e2 conduct_flip 113
vs base 58——训练早期升轻信,e4 回落 84,e2 瞬态家族。

## 矩阵注

零 REVERSE,无硬停。drills 毒性四连缺席(Llama/Mistral/SVAMP/StrategyQA)
——毒性主张的范围收窄为"Qwen×GSM 域内测得"已无悬念,fig9 该行如实画。
