# PREREG_matrix_completion(解冻批;推理/训练前冻结,2026-07-20)

M-MC-1 杠杆域迁移(纯推理):冻结 d_plain@L12 α8(E 臂工作点)打在
2Wiki/SVAMP/StratQA 的 W 探针 + O-300 子集;base = 各格既有 pred_*_base。
预测:三域 resist 提升 ≥+8pp 且 O 损失 ≤5pp(方向不依赖域);
证伪面:任一域杠杆失效 → CL-3 杠杆层加"域内测得"限定。
M-MC-2 Mistral 自提 steering:m3 管线(M1 W 标签,全层×α{2,4,6,8},资格判据);
预测:instrument-limited 风险高(O_answered .606 低依从,同 32B);
两结局都入矩阵(✓* 或 ∅+仪器注)。
M-MC-3 2Wiki drills 臂:w2_drl25(载体 450 + bare-answer drills 150,e2/e4,
脊点规则);预测:毒性缺席(知识域第五连);证伪面:出现毒性 → 范围句改写。
