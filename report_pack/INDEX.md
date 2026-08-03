# report_pack/INDEX.md — 组会汇报材料清单(C-19;2026-08-04 交付)

> 全部零新算力;每个数字溯源到 repo 数据文件(路径在各图脚注/meta)。
> 生成脚本:`report_pack/make_report_pack.py`;产物在 `report_pack/out/`。

## ⚠️ 更正声明(先读)

C-19 指令里图 B 的大字报数字写的是 "230/231"。按禁令要求的首亮前口径自查,
从 `prescription/p0c/p0c_scores.json` 实算结果是 **214 / 230**
(判据:8 个 INSUFFICIENT 格 R 均值 < 0,严格低于 base .4625;231 条目含 BASE)。
16 个例外**全部**是同一个 bend_f 合成臂的 16 个 step-checkpoint(R +.017~+.049),
NOTES_p0c_pilot.md 当时只登记了其中一个——**记账笔误,已在该 NOTES 追加更正**。
定性不变(除一个合成域训练运行外全部受损),但图 B 与口头汇报请用 214/230。

## 汇报五段 → 素材对照

| 段 | 用哪几页 |
|---|---|
| ① 转向声明 | 旧组会 docx §Opening(缝)+ §Step 0(三幕)+ §Back to the main thread;论文成品图 Fig1/Fig2/Fig3/Fig7 + Table 2(见下) |
| ② 新仪器(五轴/16 格) | `prescription/SCHEMA_axes.md` 的五轴表 + 旧资产安置表(口头讲,无新图) |
| ③ P0c 重审 | **figA_variance**(Operation 主导,Evidence≈0) |
| ④ 弃答税 | **figB_abstain_tax**(214/230 大字报 + 保持率直方图) |
| ⑤ P1 硬停侦探故事 | **figC_p1_table**(二分双落空+两处红标)→ **figD_v2_table**(V-2 初读,preliminary) |
| ⑥ 下一步 | 口头:Phase 2a 组件×剂量响应地图已开跑(60→600/2000 两段式);**不提三向实验任何预期**(C-19 禁令) |

## 新制素材(report_pack/out/)

| 文件 | 讲什么 | 数据源 |
|---|---|---|
| figA_variance.{pdf,png} | 旧"体裁效应"在 factorial 坐标下几乎全由 Operation 轴承载(η²=.203);Evidence≈0(.0002)。方法:2⁴ 平衡 ANOVA(ckpt 内中心化 R),两阶交互列出,余项 46.1% | prescription/p0c/p0c_scores.json(230 训练 ckpt + base) |
| figB_abstain_tax.{pdf,png} | 弃答普适税:214/230 训练 ckpt 损伤"信息不足应答不可答";唯一例外=bend_f 合成臂 | 同上 |
| figC_p1_table.{pdf,png} | P1 硬停表:二分双落空;红标=安慰剂独砸 keep(.888→.464)与 base override .242(盲从) | prescription/p1/p1_scores.json + p0c preds 重算核对 |
| figD_v2_table.{pdf,png} | V-2 联合分五行表(preliminary, zero-compute re-read;只出数不出结论) | prescription/p1/v2_audit.json(n_fam=170) |

各图 caption 草稿与口径细节见同名 `.meta.md`。

## 归档论文成品图(report_pack/out/paper/,直接可投影)

| 论文编号 | 文件 | 这页讲什么 |
|---|---|---|
| Fig 1 | fig1_profile.pdf | 修复训练买到什么:能力画像(哪些格涨、哪些格不动) |
| Fig 2 | fig4_recipe.pdf | 配药:组件拆解——每个训练组分各买到哪块收益 |
| Fig 3 | fig5_dose.pdf | 剂量:数据量-效果曲线与"多少数据够"的配方律 |
| Fig 7 | fig9_matrix.pdf | 验证矩阵:主张×检验的全覆盖记分(REVERSE=0) |
| Table 2 | paper_v3/sections/A1_scorecard.tex | 记分卡:全部旧结论逐条的存活/收窄/处死判定 |

## 旧组会 docx 引用(①转向声明用)

文件:`~/Downloads/GroupMeeting_Repair_EN.docx`。
**该 docx 无渲染分页信息(生成后未经 Word 排版),无法如实标页码——按节名引用,**
现场打开后页码以实际渲染为准:

- §Opening: "the gap this whole PhD is about"(缝)
- §Step 0: "the question inherited from Act One"(三幕)
- §Step 1: "the audit — decompose every point of gain"(账本)
- §Step 3: "how much data is enough? — a crash that yielded a recipe law"(山脊/剂量律;注:在 C-19 写的"§开场–§第2步"范围之外,如实标注)
- §Back to the main thread: "where the three acts stand"(转向落点)

## 禁令自查记录

- 零新实验、零新训练;figA 的方差分解与 figB 的计数是对既有 p0c_scores.json
  的重新汇总(方法名如实入脚注);V-2 表为已 commit 预测流程后算出的既有
  v2_audit.json 重读(NOTES_v2_audit.md,2026-08-03);
- 三向(P2-1)实验的预期与结果:全包未出现;
- 图 A/B 口径自查:已做,产出上方更正声明(230/231→214/230)。
