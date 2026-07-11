# Batch-2 裁决欠账登记(2026-07-11,零算力三件)

> 复现:`python3 loop3/debts_b2.py` → `loop3/eval/debts_b2.json`。只报数。

## 1. B2-0c 稳定失败核判别力重算

核 = 安慰剂(cleanreplay@e4)救不活的桶内题:conduct 57 / format 172 /
phrasing 50 / scaffold 12。

| 臂 | conduct 核 | format 核 |
|---|---|---|
| A1(3s) | 40–44% | 73–80% |
| B | 39% | 86% |
| D | 49% | 83% |
| C 通用 CoT(3s) | **35–47%** | 3–13% |
| single_conduct | 44% | 64% |

**形态**:conduct 的"硬核"也不是修复特异的——C(不含修复组分)在核上救
35–47%,与 A1/D 同区间;判别力在核上仍未浮现,只是"任何像样训练"的地板从
73%(全桶)降到 ~40%(核)。**format 桶的组分存废结构在核上原样保留**
(73–93 vs 3–13)——它是唯一在全桶/核两个口径都特异的桶。

## 2. 素题 adopt 子集重打分(机制路由闭环)

**实测 n=31**(probe-instance,31 个不同题;裁决文写 48,按实测登记,
差异来源待对——可能是含 hard 池或 W 子集口径)。

| 臂 | correct | 仍 adopt | derail |
|---|---|---|---|
| 最好的臂(A1_s44 / C_s43) | 29–32% | 42–48% | 19–26% |
| cleanreplay | 23% | 42% | 35% |
| single_conduct | 23% | 45% | 32% |
| single_drills | **3%** | **61%** | 32% |

**形态**:adopt 类失败黏死——没有任何素题数据臂(包括对症的 single_conduct)
把它救过 1/3;所有臂 ≈ 安慰剂 ±9pp;drills 使其恶化。
机制路由闭环素材:**素题 adopt = 现有全部数据配方的盲区**,与处方手册第 5 条
(深层照抄病走对症/steering)的分工一致——它属于修复腔/steering 的辖区,
不属于数据配比的辖区。

## 3. 裁决4:abstain 增益 vs 组分构成(只登记,future work 钩子)

Pearson r(20 个臂点,y = retrieve_or_abstain acc):
conduct .078 / format .393 / phrasing .312 / scaffold .394 / rule .048 /
drills −.294 / **组分数(多样性轴).685**。
登记语:弃答增益与任何单一组分的相关都弱于与"混合了几种组分"的相关——
指向配方多样性(真协同或搭配偶然,不展开,不入 claim)。
