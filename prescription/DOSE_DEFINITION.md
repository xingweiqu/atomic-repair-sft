# DOSE_DEFINITION — 剂量定义冻结文件(lawv1;2026-08-04 draft → 章程 commit 时冻结)

> 回应 REVIEW_lawv1_v1 第一条:横轴必须是组件剂量,不能混入 token 长度/抽样/模板效应。

## 1. 双剂量定义

- **主分析横轴** q_d = component assistant-target tokens / total assistant-target tokens(token 份额);
- **同时报告** n_d = component examples(名义剂量,网格标签仍用 {0,30,60,120,240,480,960,2000} 条)。
- 每个臂的实际 (n_d, q_d, 总 target tokens, optimizer steps) 落入 `dose_manifest.json`(冻结后 hash 入 commit);law 拟合对 q_d 做,图上双轴标注。

## 2. Token 预算恒定

- 全部臂固定**总 assistant-target tokens** T_total = 2000 条 carrier replay pool 的 target-token 总量(容差 ±1%);
- 替换按 token 记账:插入组件条目后,从 replay 的**同长度桶**移除等量 target tokens(桶按 target 长度分 5 桶:<50/50-100/100-200/200-400/≥400);
- epochs=2、batch 配置、lr/schedule 全臂一致 → optimizer token 暴露量近恒定;实际 steps 记入 manifest,不假设完全相等。

## 3. 嵌套替换(nested substitution)

- 每组件 2000 条池子先建好,用**冻结种子(seed=20260804)**洗牌一次;剂量 = 前缀:D_30 ⊂ D_60 ⊂ … ⊂ D_2000;
- replay 的移除顺序同样按冻结顺序(每长度桶内冻结移除序),保证 60→120 的差异只有"新增60条组件数据+对应移除的 replay",无重抽样噪声;
- 全部剂量共用**同一个 carrier pool**(同一份 2000 replay);carrier pool 本身多任务混合、构成冻结。

## 4. 长度匹配申报

- 生成组件数据时对 target 长度做软约束(目标:各组件池 target 长度分布与 replay 池的桶分布 JS 散度 < 0.1);做不到的组件(如 selective revision 天然更长)**如实申报**在 manifest,由同桶替换吸收一阶差异,残余差异列为 limitation;
- 禁止为凑长度截断/注水答案内容。

## 4b. 执行细则(v1.2,C-23 #5;smoke 前冻结,据 gate1 实测 token 统计落值)

1. **横轴**:law 拟合主轴 = q_d(组件 assistant-target-token 份额,实测值);
   副轴同时报 n_d(examples)与 b_d(family bundles);三者都入 dose_manifest;
2. **配对组件的剂量单位**:selective_revision 与 answerability 的 1 个 dose unit =
   1 个 **family bundle = 一对样本**(keep+fix / sufficient+insufficient),配对永不拆散;
   名义剂量 n 仍按 examples 计(网格值全为偶数,n examples = n/2 bundles);
   evidence/format 的 bundle = 单条;
3. **嵌套**:剂量 = 冻结洗牌后 bundle 列表的前缀(D_30 ⊂ D_60 ⊂ …),按 bundle 为原子;
4. **replay 匹配**:替换按 token 记账——插入组件条目后,从 carrier 的同 target-长度桶
   (5 桶)按冻结移除序删除 replay,直至被删 target tokens 与插入量差 ≤1%;
   组件间 target 长度差(实测 format≈11 vs evidence≈111 tok)由此吸收:同一名义 n 下
   各组件被删除的 replay 条数不同,但 **总 target-token exposure 恒定**;
5. **恒定量**:T_total(全臂 assistant-target tokens)与 optimizer updates(恒批次下自动恒定)
   为双恒定;任何臂偏差 >2% 标 BUDGET_VIOLATION;
6. **token 计量器**:唯一认定 = 训练用模型 tokenizer(Qwen3-8B)实测,禁止词数近似;
   每臂 manifest 记 input/target/total tokens、bundles、examples、桶分布、池 hash。

## 5. 与 P2a 的差别申报

P2a 为纯组件剂量(不替换、总量随剂量变);lawv1 为替换式恒 token 预算。两者数字不直接可比,Phase-1 归档拟合时 P2a 曲线单独标注设计类型。
