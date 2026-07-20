# 出门 lint 三项(C-14 W0 固化;每次 push 论文前过)
1. `Figure ??` 断引用 = 0(脚本:soundness-audit §1,本仓 python 一行);
2. 图文数字一致(图为准;差异只准以对账脚注存在,溯源数据文件——铁律 0);
3. 模板残渣(页眉年份/finalcopy 状态/合并冲突标记/math-mode unicode)。
4. **venue/年份核对**(C-15 新增):页眉 = ICLR 2027(sty 已 patch;
   投稿时换官方 2027 kit + \iclrfinalcopy)。

5. **truth table 反向巡检通过**(paper/CLAIM_TRUTH_TABLE.md ↔ abstract/正文/caption/Scope/Appendix 一致;C-17 永久项)。
6. **禁令措辞跨行扫描 PASS**(python3 lint_banned.py;C-17 验收教训:换行断词躲过单行 grep)。
