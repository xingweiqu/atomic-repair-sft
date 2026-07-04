# QUEUE_STATUS(2026-07-07 更新)

## 已完成
- 账本线:Loop0/1/1.5 全部;R-17 重记账;C-9 入闸+追溯(C9_RETRO)
- E1 硬停+裁决落地;E1b/E1c/E3追溯 configs+PREREG_e1b(先于训练)
- E2 pass@8 合并池(四桶 569/86/158/1806;难桶富裕、中间桶瘦→报顾问)
- E3 3-seed(单 op resist 99/100/100 稳)
- **E5 包**:steering/e5_steering.py(extract/sweep/align,裸 torch)+ PREREG_steering
- **E4 筛选脚本**:scripts/e4_screen_2wiki.py(域选择等 Xingwei)
- casebox 12 条真实转录;T5 设计稿(等点头)

## 服务器可跑(等指令下发)
- batch-4a:E1b/E1c/E3追溯(19 sft + 38 predicts)
- batch-4b:E5 extract+sweep(单卡,可与 4a 并行;align 等 4a ckpt)
- E4 筛选(单卡插空,产出 notes/e4_2wiki_screen.json → Xingwei 拍板)

## 本地待开发
- **Tier 2 生成器(learnability_family/)** — 最后一个大件,触发 Batch-4(Loop 2B)
- GSM-hard 注入 dry-run 50 题(Loop 2A prep,依赖桶边界确认)

## 卡点
- 中间桶瘦(86/158 < spec 500)→ Loop 2A 桶设计需顾问表态
- T5 等 Xingwei 点头后补预注册条目
