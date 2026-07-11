# Loop 5 ΔW 几何 + P-L5-drills 判定素材(2026-07-11)

> 预注册:prereg/ADJUDICATION_loop3_batch1.md §4,cos(d, ΔW_drills) < 0。
> 操作化(loop5/delta_w.py 头部披露,沿 w_projection 冻结约定):
> M1 = cos(ΔW_drills^T d, ΔW_ref^T d)(沿 steering 方向 d 的写入内容对齐,有符号);
> M2 = 组分 ΔW 两两 vec-cos(o_proj+down_proj,L8/L12)。
> 数据:loop5/delta_w_geometry.json。

## M1(主判定,ref ∈ {single_conduct, A1})

| 对 | 全层均值 | L8 | L12 |
|---|---|---|---|
| drills vs conduct | **+0.134** | +0.186 | +0.144 |
| drills vs A1 | **+0.144** | +0.180 | +0.121 |
| cleanreplay vs conduct(对照行) | +0.355 | +0.207 | +0.154 |
| cleanreplay vs A1(对照行) | +0.403 | +0.285 | +0.201 |

**P-L5-drills 判分:MISS**——符号为正,不是反对齐。
幸存的序数信号:drills 的对齐度只有中性对照(cleanreplay)的 **1/3**
(+0.13~0.14 vs +0.35~0.40)——权重级的"反向疫苗"呈现为**去相关/离流形,
不是反号**。行为学危害(W_adopt 25%、修复腔 keep 塌方)对应的是
"往别处去的更新",不是"往反方向去的更新"。

## M2(两两 vec-cos @L8)

全部为正(共享微调方向,已知现象);**drills 是全场孤立点**:
它与所有臂的 cos 都是最小值(0.06–0.24),其余臂间 0.4–0.6。
drl25(稀释剂量)与 cleanreplay cos=0.625(载体主导,与剂量曲线行为一致)。

## 登记语(不判定)

符号预测失准方向本身有信息:危害组分在权重上不是"负修复",是"第三个方向"。
若要保留"反向疫苗"这个词,它只能指行为学(素题 adopt、修复腔 keep 塌方),
不能指权重几何——措辞归顾问。
