# NOTES_steering_e5b — R-25 判别 + R-26 投影(2026-07-09 收割)

_d_plain:840 条素题 corrupt 探针(240 原生 + 600 扩展),类 388/182(≥100/100 闸门 PASS),
最优层 **L12**(repair-mode 探针曾选 L8——探针换血,层也换了)。α=0 复现 floor 基线 ✓。_

## 四曲线对照(核心两行;E5 v3 = repair-mode 探针 d)

| 探针 | α16:resist | α16:mute(α0=9%) | ab\|res |
|---|---|---|---|
| d(repair-mode,E5 v3,L8) | 95% | **20%(+11pp)** | 39% |
| **d_plain(素题,E5b,L12)** | **94%** | **11%(+2pp ✓≤+5)** | 38% |

全曲线:α8 = resist 88%/mute 7%/bleed 0/A_lat 97%(全净);α16 = resist 94%/mute 11%/
bleed 5%(压线)/A_lat 94%(压线 −5pp)/素acc 79%;α32 过冲(resist 回落 88%,ab|res 崩到 21%)。

## R-25 判定:**A 支**

- 注册判据(mute ≤ α0+5pp 且 resist 上行):**94% resist / mute +2pp → 成立**。
- E5 v3 的 mute 税(+11pp)= **探针体裁混杂**(repair-mode 转录里 resist∧参与体裁混合),
  换干净探针后税消失 → **决策与作答意愿在激活层可分离;"捆绑"是训练管线的产物,
  不是模型几何的必然**。R-24 的"部分可分离"升级为"三件套全部可分离"(格式本就不同轴)。
- 压线项如实报:α16 带 bleed 5%(=闸门上限)与 A_lat −5pp(=判据边界)、素acc 79%;
  完全干净的运行点在 α8(resist 88%)。**steering 到手的 resist 上限 94% < SFT 的 99–100%**——
  单方向逼近但不等价,如实写。
- ab|res 全程 38–39%(至过冲前)——R-27 已锁句在 d_plain 上复核成立。

## R-26 投影仪器:null 结果(注册结局)

全部 ckpt、全部层、双矩阵:ratio(‖ΔW·d‖/随机基线)= 0.96–1.02 ≈ 1,低秩捕获 1–7%。
→ 按预注册记 **"no weight-space alignment at this granularity; instrument-limited"**。
预测 3(余弦排序/keep-only 负号)权重层维持 unresolved;keep-only 的**行为学**反推证据
(resist 33% ≪ floor 83%)地位不变(R-26)。

## 给 §4 终裁的材料(两件已齐,按裁决可解冻)

1. 已锁句:"决策是可推动的低维杠杆,推它不碰计算"(两个探针下都复核)。
2. 新增候选主张:"**决策可单卖**——干净探针下 steering 至 94% resist 无 mute 税;
   SFT 的捆绑(格式+作答抑制+决策)在激活层可拆"。
3. 边界如实:94%<99%(steering≠SFT 等价);α16 压线项;权重层对齐 instrument-limited。
