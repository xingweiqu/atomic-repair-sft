# CC_INSTRUCTION_C19b — 组会图打包(零算力,立即执行)

> 目标:把组会所需全部图打包到 `~/Downloads/meeting_pack/`,Xingwei 自行整合排版。
> 不重画、不改数,只收集+核对+打包。

## 1. 收集清单(两个来源合并)

**来源 A:顾问四图**(Xingwei 会放进 repo 或直接给你,文件名如下):
- `nf1_law_concept.png` — 响应定律结构(示意图)
- `nf2_three_shapes.png` — 三种实测剂量形态(封箱数据)
- `nf3_pilot_fit.png` — 拟合试点预演(held-out 20% 盲预测 +3.5pp)
- `nf4_two_camps.png` — 文献两营定位图

**来源 B:你侧 C-19 已产出的**:
- `figA_variance.png` — P0c 方差归因(Operation 轴主导)
- `figB_abstain_tax.png` — 230/231 弃答税大字报
- `figC_p1_table.png` — P1 硬停七行表(美化版)
- (若 V-2 联合分表已出图,一并入包;未出则不含,不补做)

**来源 C:旧资产精选**(从归档论文 figs/ 直接拷,不改):
- fig1 诊断画像、fig7 验证矩阵、记分卡 Table 2 的导出图。

## 2. 打包前核对(每张 30 秒)

- 逐张过一遍:无 `??`、无模板残渣、图内数字与来源文件一致(nf2/nf3 的数
  对 NOTES_batch2 与 keep 剂量律冻结值抽查即可);
- 顾问 nf3 的拟合数(A=74.5, τ=0.5, 预测 82.5 vs 实测 79.0, 误差 +3.5pp)
  用你本地脚本独立复算一遍——**顾问出的数也走溯源核对,规矩对所有人生效**;
  复算不一致立即报,一致则在 manifest 里记 "independently verified"。

## 3. 打包结构

```
~/Downloads/meeting_pack/
  01_new_direction/   nf1–nf4
  02_p0c_findings/    figA, figB
  03_p1_hardstop/     figC (+ V-2 表若有)
  04_legacy/          旧画像/验证矩阵/记分卡
  MANIFEST.md         每张一行:文件名 | 一句话内容 | 数据源路径 | 核对状态
```

## 4. 交付

打包完成回一句话 + MANIFEST.md 内容贴出。不做 slides、不写讲稿——排版归 Xingwei。
