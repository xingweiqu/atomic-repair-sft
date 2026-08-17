# INSTRUCTION C-46 (2026-08-17) — 暂停扩写,先做 Fig.1–5 真图

为啥一个图都没有?现在暂停继续扩写正文。当前 PDF 只有 figure TODO 和 caption,没有真正的图。优先完成并插入 Fig.1–Fig.5,所有图必须从 frozen evidence artifacts 自动生成,并保存 source_data + plotting script。

- Fig.1 用 atomic-profile tile matrix,不用 radar;
- Fig.2 画四类 repairability dose-response;
- Fig.3 画 cross-domain collateral/reversal;
- Fig.4 左边 frozen additive prediction vs actual,右边 carrier/diversity rescue;
- Fig.5 画 Llama freeze chronology + predicted/actual U + Original-vs-U Pareto。

生成后重新编译 PDF,确保正文引用和 caption 对应,再继续写作。

## 执行记录
- 管线:atomic-repair-paper/figs_v4/make_figs.py,只读 atomic-repair-sft/PAPER_EVIDENCE_FREEZE/(+ 仓内 ktgt/rescue spec),每图落 figs_v4/source_data/figN_source.json,输出 figures/fig{1..5}_*.pdf;build_pdf.sh 恢复"先生成图再编译"。
- 端点核对(图必须画 artifact 真值):interface=format.contract_exact(.706→.990@30→1.0@60);format-MAIN=format.main(.263→.298);fix=wc_attempt.joint(.784→.631@120/.706@960/.689@2000);KEEP=cc_attempt.joint(.902→.492@2000);adopt=wc_attempt.adopt(.109→.238@60);EVD=distractor.acc_exact(.843→+0-3pp);ANS=insufficient.insufficient_stop(.165→.932@480→1.0)+suff_ctr.false_abstain(.011→.106@1822,跨 .10);KRV 反转=ksparse+ktgt wc joint(0000:.192/.358/.138 → 1493:.000×3)。
- **数字更正**:正文原写 format retention "original .83±.02" 与 freeze 不符,artifact 实值 FMT 网格 original.acc_exact .8815–.9168 → 更正为 ".90±.02"(tex+MD 全改,C-45 引入自旧 DRAFT,来源不明,已废)。
