# CONTRACT_TRAIN — 训练契约(lawv1;2026-08-04 draft;Gate-3 冻结)

> 数值来源:loop3/P2a 实跑世系 config(configs/loop3/l3_cleanreplay_s42_e4_sft.yaml),
> 非新发明;lawv1 差异项显式标注。Gate-2 smoke 负责验证本契约每一条可执行。

## 1. 模型与输入格式([FROZEN],hash 项 Gate-2 落值)

| 项 | 值 |
|---|---|
| model checkpoint | `/mnt/hdfs/xwqu/Qwen3-8B`(instruct;== 服务器既有全部实验用模型) |
| model hash | Gate-2 时 `sha256(model.safetensors.index.json + config.json)` 写入 environment.txt |
| tokenizer | 同 checkpoint 目录自带,revision 同上 |
| chat template | LLaMA-Factory `template: qwen`;Gate-2 时 dump 一条渲染样例(含特殊 token)入 repo 作为对照件 |
| system message | 空(不注入自定义 system;模板默认行为为准,渲染样例为证) |
| thinking mode | 关(qwen 模板非 thinking 渲染;评测侧同样关,见 CONTRACT_EVAL) |
| BOS/EOS | 模板默认;不手工增删 |
| loss mask | assistant target-only(LF sft 默认:prompt 全 mask);**Gate-2 用 label!=-100 计数核验** |
| reasoning token | target 内的简短推理参与 loss(它是 target 的一部分);无独立 thinking 段 |
| packing | **off**(不 packing,一条一样本) |
| truncation | 右截断;cutoff_len=2048(lawv1 差异项:loop3 为 1024,因 revision/evidence 条目更长;Gate-2 核验 0 条被截断,否则回报) |

## 2. 优化器配置([FROZEN];唯一模板 configs/lawv1/train_base.yaml,由 run 脚本只改 dataset/output/seed/epochs 四行)

```yaml
model_name_or_path: /mnt/hdfs/xwqu/Qwen3-8B
template: qwen
cutoff_len: 2048
packing: false
stage: sft
do_train: true
finetuning_type: full
deepspeed: configs/ds_z3_config.json
precision: bf16 (bf16: true)
optimizer: adamw_torch(LF 默认)
learning_rate: 1.0e-5
weight_decay: 0.0
warmup_ratio: 0.03
lr_scheduler_type: cosine
per_device_train_batch_size: 4     # micro batch
gradient_accumulation_steps: 4
# global batch = 4 x 4 x 8 GPU = 128
max_grad_norm: 1.0 (LF 默认,显式写出)
num_train_epochs: 2
max_steps: -1                       # 由 epochs 决定;见 §3 步数恒定性
seed: 42                            # 锚点臂 43/44
gradient_checkpointing: true
logging_steps: 10
save_steps: 100000                  # 即只存末位
save_total_limit: 1
report_to: none
```

## 3. 训练预算控制([FROZEN])

主控制量(顾问建议采纳):**optimizer steps 恒定 + 总 assistant target-token exposure 恒定**;examples 与 n_d 作第二横轴报告。

实现:全臂 2000 examples、global batch 128 ⇒ **每臂恒 32 updates**(⌈2000/128⌉×2 epochs;LF drop_last 行为 Gate-2 核实并记录实际 updates);token exposure 由 DOSE_DEFINITION 的同桶等 token 替换保证(T_total ±1%)。

每 run 必录(train_log.jsonl + run_manifest.json):input tokens 总量、target(loss)tokens 总量、实际 updates。**任何两臂 loss-token 总量差 >2% ⇒ 该臂标 BUDGET_VIOLATION,不得静默进曲线。**

## 4. Checkpoint 规则([FROZEN])

- 主结果 = **final checkpoint 唯一**;
- 不保存中间 ckpt(save_steps=100000);如未来做学习轨迹,须开 amendment、显式 trajectory run,且中间 ckpt **绝对禁止**用于挑主结果;
- 禁止按 eval 选 best checkpoint,无例外。

## 5. Seed 规则([FROZEN],开跑前写死,与首 seed 结果无关)

| 臂 | seeds |
|---|---|
| placebo(dose-0) | 42, 43, 44 |
| 每组件固定锚点 n ∈ {240, 2000} | 42, 43, 44 |
| 其余剂量 {30,60,120,480,960} | 42 |
| 自适应追加(≤1 点/组件) | 42,43,44;run_id 带 `-ADP`,标 adaptive refinement,不并入预注册确认 |

## 6. 执行环境

bringup.sh 为唯一环境入口(含 deepspeed==0.19.2、vllm==0.12.0 pin);训练落本地盘 `/opt/tiger/lawv1_local/<run_id>` 再 cp HDFS(m2 os-error-38 教训);environment.txt 记录 pip freeze + torch/cuda 版本 + hostname。
