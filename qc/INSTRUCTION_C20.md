# CC_INSTRUCTION_C20 — 收敛版组会图集(零算力,全部冻结数据)

> 故事定稿版 = "趋势 → scaling law 假设 → held-out 验证协议 → 路线"。
> 已有 7 张(nf1–nf4 + figA/figB/figC)入 meeting_pack 照旧;本指令新增 5 张 + 1 张示意,
> **全部从封箱冻结数据/既有预测文件绘制,禁止任何新训练或新推理**。
> 风格沿 FIGURE_STYLE.md;每图脚注:数据源路径 + seed 数标注(单 seed 臂必须标明
> "single preregistered arm")。

## 新图 P — 趋势三:安慰剂效应四联(真实数据)
四个小面板,同一句话:"普通干净数据独自就会改变模型":
(a) 修复腔 overall:base .333 → cleanreplay .575;
(b) conduct 桶救活率:cleanreplay ≈73%(flip-overlap 地板);
(c) P1 keep:base .888 → cleanreplay .464(安慰剂独自砸 keep);
(d) 2Wiki 已知题 QA:5 → 34–56 新失败(含安慰剂臂,知识域税)。
Caption 落点:无 placebo 校正的组件效应必被高估——定律必须拟 placebo-adjusted delta。

## 新图 V — 趋势四:向量响应小矩阵(真实数据)
行 = {format@10%, drills@25%, conduct 单组分, cleanreplay};
列 = {目标桶 Δplacebo, 素题 O_acc, 修复腔 keep, 弃答保持};
格 = 带符号数值热力(红负绿正),只填有冻结数字的格,缺测格灰。
Caption:"同一份数据,一维是正数、另一维是负数——响应是向量不是标量。"
数据源:NOTES_batch2 / batch1_scores / P0c 弃答列。逐格数字溯源清单附 MANIFEST。

## 新图 L — 假设页:单式三曲线(示意,标注"示意")
ΔS = A(1−e^{−(n/τ)^α}),画 A>0(饱和收益)/ A≈0(无效平线)/ A<0(渐进损伤)三条,
参数表框注 A/τ/α 各自含义。脚注:"形态库另含阈值/分段形,由模型比较选择(见图 D)。"

## 新图 K — 验证协议第二例:keep 稀释曲线 held-out(真实数据,损伤方向)
数据 {0,15,33,100}% → {100,90,76,33}(+ 不训基线 83 横线)。
用 {0,15,100} 拟合带符号饱和式(A<0 方向),盲预测 33% 点,标注预测 vs 实测 .76 与误差。
与 nf3 成对呈现:一条收益方向、一条损伤方向,同一协议。拟合脚本入 repo,数字可复算。

## 新图 D — 形态比较判形演示(真实数据)
drills 素题 W_adopt {0,10,25,100} = {2, 1.3, 1.5, 25}:
用 {0,10,100} 三点分别拟"单调饱和"与"阈值/分段"两形态,各自预测 25% 点
(饱和形必然高估、阈值形≈2 贴实测 1.5)——当场演示"模型比较能判形"。
Caption:"不预设全组件同形;形态由 held-out 预测优劣裁决。"

## 新图 N — seed 噪声量尺(真实数据,6.2 合格线)
横条图:B 臂 overall ±.040(3 seed 全距)、A1 ±.025、C ±.039、弃答列 ±.15。
竖参考线:nf3 的预测误差 3.5pp 落在哪。
Caption:"预测误差必须显著小于 seed 噪声才算规律(合格线 6.2);弃答列噪声极大,
其预测判定必须 multi-seed。"

## 新图 R — 路线 pipeline 一页(示意)
画像(纯推理) → 每组件 2 个小剂量 pilot → 拟合/校准响应参数 → 预算内 argmax 配方 →
一次训练 → 与 uniform/人工比例/generic/按频率/补最差 五基线对照。极简流程图。

## 打包
以上并入 `~/Downloads/meeting_pack/` 新子目录 `05_convergent_story/`,
MANIFEST 追加各图行(含逐数溯源与 seed 标注核对列)。
新图 K/D 的拟合数与 nf3 一样走独立复算核对。完成回一句话 + MANIFEST 增量。
