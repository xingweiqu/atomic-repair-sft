# GATE2_SMOKE_REPORT — 三个端到端 smoke run(2026-08-05;单 seed 42;lq 单机)

> RUN_MATRIX_smoke 三行全 OK:build→train(full FT z3)→ckpt→vllm 评测(518 行)→双层打分→12 件套落盘(DONE 均通过行数校验)。
> 产物:prescription/lawv1/runs/SMK-{PLAC-0000,FMT-0060,FMT-0200}-S42/。
> base 已在同一 v1.2.1 评测集上重测(pred_base_v121),四臂同尺可比。

## 1. 管线验收(C-24 #7)

| 检查 | 结果 |
|---|---|
| Token 预算 | 三臂总 target tokens 偏差 ≤0.06%(2% 线内);q_d=0/.011/.039 实测 |
| 训练 | 三臂各 2 epochs 正常收敛(FMT200 末 loss .78);ckpt hash 落盘 |
| 评测 | 各 518/518 行,无缺漏;greedy 确定性 |
| 工件 | 12 件套 × 3,含 environment/git_commit/data_manifest |
| 成本 | 单臂训练 ~86s(600-750 条)+ 评测 ~6min;三臂总计 <40min |

## 2. 四臂读数(n=50/条件,insufficient 系 26;**单 seed,方向性读数**)

| endpoint | base | PLAC | FMT60 | FMT200 |
|---|---|---|---|---|
| original | .84 | .78 | .80 | .76 |
| paraphrase | .90 | .80 | .76 | .80 |
| distractor | .76 | .68 | .68 | .70 |
| **format contract_exact** | **.78** | **.54** | **.76** | **.96** |
| format schema | 1.00 | .90 | .96 | .98 |
| **format MAIN(schema∧content)** | **.34** | **.46** | **.38** | **.24** |
| insuf 自由文本 stop | .23 | .19 | .23 | .19 |
| insuf_ctr joint(受控) | 1.00 | 1.00 | 1.00 | .96 |
| suff_ctr joint / false-abstain | .92/.04 | .92/0 | .92/0 | .88/0 |
| wc_attempt joint / adopt | .82/.02 | .76/.08 | .80/.02 | .78/.04 |
| cc_attempt joint | .74 | .82 | .86 | .76 |

## 3. 三条主发现(全部标注:单 seed、原型规模)

1. **format 的剂量响应已现形,且是向量不是标量**:contract_exact 单调救活
   .54(placebo)→.76(60)→**.96(200)**;但 format MAIN 同时 .46→.38→**.24**——
   格式合规学会了,直答内容被高剂量砸了;original 同步微降。同一份数据一维正一维负,
   蓝图"向量响应"命题在 smoke 里就实证了;
2. **placebo 独立效应可测**:纯 replay 使 original −6pp、format exact −24pp、
   cc_attempt +8pp——F(N) 项非零,placebo-adjust 的必要性再次坐实;
3. **接口效应 ≫ 训练效应(弃答向)**:受控 STATUS 下四臂全在 .96–1.00,
   自由文本下全在 .19–.23——insuf_ctr 在 GSM 原型上已饱和,**做 answerability 的
   剂量曲线必须用自由文本层或更难的受控探针**(报顾问定夺)。

## 4. 顺带的模板敏感度记录

candidate 契约从 v1.2 措辞(三行式)改为 v1.2.1 措辞(真两行式)后,base 的
cc_attempt joint 从 .88 → .74(同题同模型 greedy)。措辞级 14pp,继续支撑
"受控接口 + 模板审计"路线。

## 5. 待办(Stage A 前)

模板审计脚本(margin/BPB);answerability 受控探针加难或改自由文本主读出(候顾问);
正式 2000-carrier 构建+审核;paraphrase 扩产改写机决策。
