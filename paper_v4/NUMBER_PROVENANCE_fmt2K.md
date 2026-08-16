# 数字对账:Format→Knowledge candidate collapse(C-42 #1)

## 论文唯一口径(正式)
`PAPER_EVIDENCE_FREEZE/transfer_matrix_k500.json`
- base: `cc_attempt.decision_acc = .608`, `cc_attempt.final_acc = .602`, `contract = .992`
- FMT-0060-S42: decision `.070`, final `.208`, contract `.978`
- (FMT-0240 `.224`, FMT-2000 `.244` — 非单调,60 最深)
来源:K-500 formal eval(500 families、donor 独立池、hard distractor、K-eval-v1 修复版 scorer、65 ckpt,单 ckpt=s42)。
**正文引用形态:decision .61→.07@60(contract 完好 ≈.98–1.0;final .60→.21 同步恶化)。**

## 被取代版本(REPORT_v2 时代)
`prescription/knowledge/transfer_matrix_k_v1.json`(50-family 原型评测,修复前仪器代际):
decision `.447→.120@120→.087@960`、final `.567→.167`(FMT 3-seed 均值,REPORT_v2 汇总路径)。
**取代原因**:①评测规模 50→500 families;②donor 池与主评测未隔离(C-30 判为设计缺陷)→ K-500 改独立 donor;③distractor 换 hard 档;④剂量报告点不同(120/960 vs 60/240/2000)。两套数字方向一致(判定崩塌、contract 完好),差异来自仪器与规模升级,非矛盾。
**处置**:REPORT_v2 相应行标 superseded;论文只用 K-500 口径,并在附录 provenance 表登记本对账。
