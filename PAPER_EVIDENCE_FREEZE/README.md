# PAPER_EVIDENCE_FREEZE — 论文唯一事实源(2026-08-17)
论文正文的每一个数字只准从本目录文件读取。含:Qwen 四组件曲线(e500)、K/IF 矩阵、SVAMP、
mixture 冻结+开牌、rescue 冻结+开牌、interaction correction、Llama calibration/verdict/prediction
三冻结件、final result+audit、retention 表、budget bridge。撤回台账见 qc/INSTRUCTION_C29/C32/C38。

新增(C-45,2026-08-17):rq1_paired_fragility.json — RQ1 same-item fragility 的 existing-data readout
(distractor 轴 529-fam 配对:placebo 均值 P(fail|orig correct)=.095,base=.119;仅由既有 scorer
summary 推导,无新训练/新推理;paraphrase 仅 50-fam 辅助层,不得升为 formal 证据)。
