# Loop 3 签字裁决(2026-07-13)【存档】

①系数表批准但改身份:不做 A2 配置,做**预注册预测表**(对单组分臂实测 RE 的预测,逐格打分)。
时序重排:Batch1 = 六单组分(RE 测量仪)+ A1+B+C+D+E+clean-replay;Batch2 = A2 用实测 RE 配比
→ A2 从 matched-by-prior 变 **matched-by-measured-rescue**。
②预算两档:单组分固定 600 条/臂(token 对齐,不按 prevalence 缩放);混合臂 A1/A2/B/C/D 统一
2000 条量级 token 对齐;E 零数据。conduct 单组分与 E1b 配置一致时审计后复用 ckpt。
③3-seed:A1、A2(终配置)、C ×{42,43,44};B/D/E 单 seed 加披露。
附则:(a) D 臂确切置换现在写死进 prereg;(b) format 组分定义=**"在格式约束下算对"的示范**,
不是"格式合规"示范;出血监控逐臂跑;(c) 单组分 ckpt 全保留(Loop 5 ΔW 几何依赖)。
模式:凡"我们假设"能换成"我们实测"的,都换掉。
