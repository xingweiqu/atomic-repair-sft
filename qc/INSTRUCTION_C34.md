# CC_INSTRUCTION_C34 — 收口令(2026-08-15,要点存档)

目标:完成三域 response → mixture prediction → held-out 闭环,不再增加 single-component 现象。
0. 口径修正:ANS 曲线实为 50/26/20-family(禁写 4/4 均 529);ANS 网格不重训,16 ckpt 立即用 eval-500 补评并重生成曲线/bootstrap/Pareto/onset/LODO;
1. IF 稀疏立即跑 Format/Evidence-v2.1/Answerability × {placebo, frozen onset, high}(ANS onset 用预注册规则不得用 26-family 事后选);Revision 单独 gate 不阻塞;
2. K targeted 复现 8 runs:KRV/KAN 的 placebo/high × s43/44(验 all-KEEP 反转与 ANS 代价;复现即停,不复现才扩);
3. budget-bridge audit:各 placebo 的 hash/exposure/updates 对账,用现有 22/30/36 步 placebo 估 nuisance;不够才补最小 bridge runs;禁重跑网格;
4. Utility 层级制:Domain→Branch→Condition→Leaf;五 branch 各一 primary(base=original paired;robustness=distractor paired;candidate=cc/wc paired joint;answerability=paired+false-abstain 硬约束;interface=semantic MAIN);family→branch→domain 宏平均;U=(U_R+U_K+U_IF)/3;禁 flat row average;
5. 四件齐(ANS 补评/K seeds/IF sparse/IF score matrix)即冻结三域统一模型;不再加 dose/component/seed/margin 模板;
6. mixture 变量剪枝:无净收益或违约候选置 0/极低上限,规则在开牌前冻结;
7. 六臂预注册:replay/uniform/failure-freq/worst-repair/predicted-optimal/retention-constrained;训前冻结全配比+预测+hash;同预算同 schedule;
8. 判据:ranking/vector calibration/decision usefulness(retention+cc-joint+false-abstain+worst-branch 阈内);
9. interaction rescue:误差>噪声时最多 6 个 targeted runs,不做全因子;
10. held-out:Llama-3.1-8B 不重 discovery;base profile+少量 calibration+shape 重标定+预测 recipe+基线+预注册 seeds;
11. 调度照 C-33;优先级:ANS 补评→IF sparse→K targeted→缺失 formal eval→mixture→held-out。
