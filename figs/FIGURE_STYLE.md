# FIGURE_STYLE — 论文图统一样式(C-12 A1 固化;全部图共用,禁止逐图手调)

> 来源:qc/INSTRUCTION_C12.md A1 + paper skills(figure-as-argument)。
> 所有作图脚本 `from figs.style import *`(rc 配置唯一入口 figs/style.py)。

## 硬规范

1. **色板 = Okabe-Ito**(色盲安全,固定语义分配,跨图一致):
   - A1 画像配比 `#0072B2`(蓝) - B 均匀 `#009E73`(绿) - C 通用 CoT `#E69F00`(橙)
   - D 反转 `#CC79A7`(紫红) - cleanreplay/安慰剂 `#999999`(灰)
   - drills/毒性 `#D55E00`(朱红) - format 组分 `#56B4E9`(浅蓝) - 其他组分按序取余
2. **单 seed 数据点视觉区分**:空心 marker(`mfc='none'`)或虚线;caption 必注
   "hollow = single seed"。3-seed 臂:实心 + 误差棒(min-max,n=3 不画 std)。
3. **灰化数据禁入图**:n_matched<50、污染对照(pass@8 v1、E5 v1、v1 误跑四份)、
   Batch-1 里被裁决停牌的比较,一律不出现。
4. 输出:`figs/out/fig{N}_{slug}.pdf`(矢量,正稿)+ `.png`(300dpi 预览,审图包)。
5. **三件套**(每图,进 `figs/out/fig{N}_{slug}.meta.md`):caption 草稿 /
   数据来源文件路径(可点开)/ 支撑的 CLAIMS 编号。
6. 字体 sans(DejaVu Sans),基准字号 9(标签)/8(刻度)/10(面板标题);
   线宽 1.5(主)/1.0(辅助);figsize 单栏 (3.5, 2.6)、双栏 (7.0, 2.8);
   spines 只留左下;grid 只开 y 轴 alpha=.25。
7. **图即论点**(skill Rule 8):每张图的 caption 第一句 = 它支撑的 claim 句,
   不是"X vs Y 的曲线";画不出 claim 句的图不做。

## rc 配置(figs/style.py 唯一入口)

```python
OKABE = dict(A1="#0072B2", B="#009E73", C="#E69F00", D="#CC79A7",
             placebo="#999999", drills="#D55E00", format_="#56B4E9",
             conduct="#F0E442", scaffold="#009E73", extra="#000000")
import matplotlib as mpl
mpl.rcParams.update({
    "font.family": "sans-serif", "font.size": 9,
    "axes.titlesize": 10, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "lines.linewidth": 1.5, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.alpha": 0.25,
    "figure.dpi": 120, "savefig.bbox": "tight", "pdf.fonttype": 42,
})
```
