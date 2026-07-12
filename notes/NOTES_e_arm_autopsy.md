# E 臂 .760 硬停验尸单(顾问拦截令 2026-07-12;fig4 定稿前置)

> 触发:实测修复腔 Δ安慰剂 +18.5pp / Δpre-repair +42.7pp,与冻结 P-E-2(<+10pp)
> 矛盾 → 强制硬停。四项体检如下,数据全部来自入库文件。

## (a) 评分通道对齐 ✅(带披露①)

同一 strict scorer(score_repair,与全部臂同路径;非 JSON 输出走同一
final_field 回退,对 E 无特殊通道)。**Schema 合法率:E 75.0% vs
pre-repair 30% vs B 臂 96%**——E 的 .760 是在 25% 解析失败的惩罚下拿到的,
通道无虚增;**但"一根方向使 JSON 合法率 30→75%"本身入披露①:
方向不纯是决策向,携带遵约/体裁成分**(与 CL-3 的"决策可分离"表述需并读)。

## (b) 逐 policy 拆分 ✅(弃答虚增假说被否;带披露②)

vs pre-repair(总 +42.7pp)按 n 加权贡献:keep +13.1 / verify +9.8 /
override +7.9 / recompute +6.9 / **abstain 仅 +5.0(占 12%)**——增益是宽谱的,
不是弃答单点。**vs 安慰剂(+18.5pp)的拆分更有信息(披露②)**:
keep **+.413**、abstain **+.35**、override **0**、recompute **0**、verify −.06
——E 对训练臂的全部优势集中在两个纯决策策略上:**不乱改对的答案(keep)、
该弃时弃**;计算类策略与安慰剂持平。机制读法:训练臂付了 keep 塌方税
(安慰剂 keep .481),steering 不付——E 赢在"决策面无损安装",
与 CL-3 完全同构,不是新魔法。

## (c) 方向/协议出处 ✅

d = steering/out_e5b/directions_plain.pt(E5b 冻结)L12,α=8(E5b 甜点,
未外推);HF generate do_sample=False(贪心单次);Steer hook = 每 forward
在 L12 输出加 α·d 一次(与 E5b 同一类、同一语义),推理后 remove。
代码锚:loop3/e_arm.py(LAYER/ALPHA 常量)、steering/e5_steering.py:145-166。

## (d) 反面体检(全局退化排除)✅

素题同套探针:O_acc 92.8% vs pre-repair 93.5%(−0.7pp,无实质损伤);
W_adopt 1.3%;W_mute 10.6%(<12% 闸门,压线披露)。非"全局退化碰巧撞对"。

## 验尸结论(供顾问签字)

四项通过;.760 为真读数,无通道伪影。**带两条机制披露入档**:
①方向携带遵约成分(30→75%);②对训练臂的优势 = keep+abstain 决策面,
计算面与安慰剂持平。P-E-1/P-E-2 双 MISS 如实入记分卡。
签字后 fig4 定稿(caption 已按此重写,含 MISS 记分与披露②一句)。
