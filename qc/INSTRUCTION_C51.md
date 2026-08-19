# INSTRUCTION C-51 (2026-08-19) — "你就一直跑"

持续自主运行授权:v3 立即开跑并保持循环直至闭环。v3 = composition-damage 直接拟合(替代 N=2 线性缩放 guard):
qwen3-1.7b + llama31-8b × 5 个小混合校准臂,扫 (total, coverage, ANS-share):
CD300 {F60,E60,R0,A120,P60} / CD600 {F120,E120,R60,A180,P120} / CD900 {F180,E180,R60,A300,P180} /
CD1200d {F240,E240,R120,A360,P240} / CD1200c {F240,A960}(2-cell 集中)。
读 clean+FA+U → 拟合 composition damage(clean_offset(total,coverage), fa_offset(ans,total))→ optimizer v3(Opt-U+Opt-Loss,PARA 走注册 law)→ PREDICTION_FREEZE_V3 先 commit → prospective v3(目标:双模型全绿)→ V3_REPORT。
