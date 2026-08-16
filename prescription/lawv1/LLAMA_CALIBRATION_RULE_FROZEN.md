# LLAMA calibration 机械规则(2026-08-16 冻结;先于任何 Llama 数据)

## 流程(机械执行,无人工干预点)
1. base profile:Llama-3.1-8B-Instruct × 三域评测(eval500/K500/IF);
2. calibration 2 runs(与 Qwen mixture 同构:2000 例/54 steps/三域 carrier):
   - LL-replay(纯 carrier)→ U_base^L;
   - LL-BRansR(ans_R=480,余 replay)→ δ_ansR^L = U(LL-BRansR) − U(LL-replay);
3. 重标定(预注册公式):scale = δ_ansR^L / δ_ansR^Q(δ_ansR^Q=+.0593);
   - 桥接单项:δ_i^L = δ_i^Q × scale(fmt_R/ans_K 的 δ^Q≈0 → 保持 0);
   - 多样性溢价:γ^L(600/1200 档)= γ^Q × scale,γ^Q 取 uniform/failure_freq 残差 {600:+.078, 1200:+.109} 线性内插;**强假设,如实申报**;
4. predicted recipe(机械搜索,搜索空间预注册):6 格全铺、每格 ≥50、总组件量 ∈{600,900,1200}、
   ans_R ∈{100,200,480},其余格 ∈{50,100,200};目标=修正模型预测 U 最大;
   约束=预测 false-abstain ≤.10(用 Qwen ANS 曲线的 fa(dose)×scale 预测);
5. 四臂配方(baseline 现在冻结):
   - replay:三域 replay 2000(667/667/666);
   - uniform:6×100 + replay 1400;
   - heuristic(=Qwen 阶段的 worst-endpoint repair):ans_R400+ans_K400+ans_IF400 + replay 800;
   - predicted:步骤 4 输出;
6. seeds:predicted/uniform/replay × {42,43,44},heuristic × 42 → 10 runs(+2 calibration=12);
7. 预测向量/预测 U/预测 ranking 全部写入 LLAMA_PREDICTION_FREEZE.json 并 commit,之后才准开训;
8. 开牌判据(C-34#8):约束内 U_predicted vs U_uniform;vector calibration;worst branch。

## 禁止
看 base profile 或任何中间结果后修改配方/公式/阈值;Qwen 任何再训练。
