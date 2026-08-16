# CC_INSTRUCTION_C36 — 最后一战:Llama held-out(2026-08-16,要点存档)

- **Qwen 封笔**:discovery+failure analysis 使命已完成,不得再动;
- 修正模型(carrier bridge + diversity threshold)在 Qwen 上属 post-hoc rescue,**冻结后不得再改**;Llama = 唯一真 out-of-sample 检验;
- 训前必存 LLAMA_PREDICTION_FREEZE.json:calibration ckpts/correction 公式/active cells/每格 token 预算/总剂量/多样性要求/预测 endpoint 向量/预测 U/false-abstain 阈/预测 ranking/全部 baseline 配方;
- 四臂:replay/uniform/simple heuristic/corrected predicted;predicted+uniform+replay 多 seed,heuristic 单 seed;
- calibration rule 预先规定、机械执行;**禁止看 Llama base profile 后人工改 recipe**;
- 三种结局的论文定位(强版/中间/实证版)已知,如实开牌;
- 完成度:工程 ~95%,科学 ~85%;这 15% 决定标题是 "Predicting SFT Recipes from Response Profiles" 还是 "Why Single-Component SFT Response Laws Fail to Compose"。
