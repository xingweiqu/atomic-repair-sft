# Loop 3 Batch-1 判定页(2026-07-10)

> 本页是 `PREREG_loop3.md` 的判定记录;prereg 原文一字未改。
> 裁决人:Xingwei/顾问(原文见 `qc/LOOP3_RULINGS_batch1_verdict.md`);CC 只执行。

## 1. 臂结局判定

预注册三种合法结局:(i) 画像配比优 (ii) 均匀优 (iii) 无差异。
**判定:结局 (iii) 的强化版**——素题体裁下,在 conduct/phrasing/scaffold/rule
四桶,A1≈B≈D≈C≈cleanreplay(Δ 安慰剂 ±16pp 内);唯一配方特异的桶是
format(含 format 组分 +70~79pp,不含 ≈0)。诊断的可操作内容由
"按画像配比例"塌缩为"特异组分要有,毒性组分要踢,其余归任何干净数据的地板效应"。

## 2. A2 臂:non-executable as preregistered(不是 skipped)

预注册公式 A2_k ∝ prevalence_k × RE_k(实测) 的前提——各桶存在特异修复系数——
被 Batch-1 实测**证伪于 5 桶中的 4 桶**(特异效应 = 臂−cleanreplay ≈ 0;
format 桶的系数因 single_format 无干净工作点而不可测)。
公式的输入量不存在,臂无法按注册执行。据此 A2 入档为
**non-executable as preregistered**,归因于预注册前提被数据证伪,非执行方跳过。

## 3. 预测表判定(照单全收)

2 HIT(phrasing、scaffold raw)/ 1 方向 HIT(drills 方向对、漏报危害)/
3 MISS(conduct .95→特异+2;rule .90→−9;format .60→前提失败不可测)。
核心失准句已入 `paper/CLAIMS.md` 修正记录:
"修复率≈组分与桶的匹配度"假设被"高非特异地板 + 特异信号稀少"替换。

## 4. Loop 5 预注册追加(权重几何组,训练前冻结)

- **追加预测 P-L5-drills:cos(d, ΔW_drills) < 0**,其中 d = steering 修复方向,
  ΔW_drills = single_drills 脊点 ckpt 相对底模型的权重差——
  行为学"反向疫苗"第二例(drills、keep)的权重级验证。
- 单组分 ckpt 保留令确认:HDFS `/mnt/hdfs/xwqu/loop3/output/l3_single_*` 不得清理。

## 5. Batch-2 重定向(入口)

1. **B2-0(零算力,先行)**:(a) 翻转重叠审计(跨臂/跨 seed 被救活题集合重叠度
   → 决定 Fig 1 prevalence 的不稳定性折扣脚注);(b) 体裁对账(Batch-1 现有
   14 脊点 ckpt 跑修复腔 corrupt 评测,免重训;检验"配比重要性随体裁翻转")。
2. **B2 训练 = 三条剂量曲线**(prereg 另立 `PREREG_batch2.md`,训练前冻结):
   format 掺量 0/10/20/36%(毒性稀释阈值);drills 掺量 0/10/25%(服从类数据
   危害剂量律);scaffold+format 对照臂(94% 异常:桶吃"结构"还是"JSON 约束")。
