# CC_INSTRUCTION_C38 — 终局确认+措辞收紧+实验冻结(2026-08-17,要点存档)

- Outcome A 确认(seed 级:min predicted .4457 > max uniform .4416,3v3 全序胜);
- **措辞三收紧**:①写 "transferred to a held-out Llama family / cross-family evidence",不写"证明跨模型普适结构";②"ranking and direction transferred perfectly, while effect magnitudes were under-calibrated"——不写"间距都对"(冻结 gap .029/.015/.019 vs 实际 .057/.067/.037);③偏差非常数:replay −.005 / heuristic +.013 / uniform +.065 / predicted +.092——"model substantially underestimates gains of diverse intervention mixtures; replay well calibrated"(多样性溢价仍被低估,有机制意义,入 limitation/future work);
- 补 LLAMA_FINAL_AUDIT.json(逐臂×逐 seed 全 branch/endpoint/三域 false-abstain/worst branch/残差/来源链);
- **实验正式冻结**:不加模型不补组件不调 Llama;robustness check 等初稿后再议;
- 写作序列:audit pack → 主表主图 → outline → Methods → Results → Introduction(先 Results+Methods);
- 论文主故事六步定稿(异质响应→域依赖→加性证伪→受控 rescue 定位 carrier+diversity→冻结→held-out 前瞻验证)。
