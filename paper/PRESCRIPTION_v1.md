# 处方手册 v1.2(论文 §7;v1.1→v1.2 依验尸签字附则3 2026-07-12,规则 5 阶梯升级)

> 冻结文本,来源 `qc/BATCH2_RULINGS_verdict.md`。改动须新版本号 + 裁决。
> 每条规则后附证据锚(一条剂量曲线或一次对账)。

1. **特异组分:补上即可,60 题量级**(≤10% 掺量饱和;阶跃不是坡)。
   [NOTES_batch2_dose §1:fmt10 REd_format 83%,Δ+75;fmt20/36 无追加增益]
2. **毒性/效果验收必须双体裁做,且对照 pre-repair;哪个体裁显形不可先验假设**
   (v1.1 修订:GSM 里修复腔先显形,2wiki 里素题面先显形——域相关)。
   [NOTES_batch2_dose §2:drl25 修复腔先中毒;NOTES_2wiki:方向反转第四例 +
   全部训练臂修复腔低于 pre-repair]
3. **纯食谱是唯一致死剂型**(100% format 训哑无干净点;100% drills 教服从
   W_adopt 25%)。
   [NOTES_batch1 §4;ridge_l3_single_format_* 尸检]
4. **配比不重要:uniform 覆盖即可**(安全句定稿,★1 2026-07-12 结案;B 3-seed 后强句永久停用)。
   [NOTES_batch1 §2:A1≈B≈D;NOTES_b2_0b:修复腔里配比方向仍无对症优势]
5. **决策类修复:steering 一线,SFT 二线**(v1.2 升级)。数据层存在
   keep–override 结构性互斥(剂量律),SFT 必须二选一并付 keep 塌方税;
   激活层不付此税,两头全拿(E 臂 .760 > 全部训练臂,优势全在 keep+abstain)。
   SFT 保留给需要 99%+ 且接受 keep 代价的场景;能力病走工具。
   [E1b 互斥;NOTES_steering_e5b 可分离;NOTES_e_arm_autopsy 红利实测;COR-4]

验收体裁原则(贯穿 1-5):修复相关效应的可见度受体裁门控(CL-6)——
处方的每一步(补、踢、验)都必须声明在哪个体裁下测量。
