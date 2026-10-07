# 问题跟踪

| 编号 | 日期 | 问题描述 | 严重度 | 状态 | 解决方案 |
|---|---|---|---|---|---|
| I01 | 2026-10-06 | nomic-embed-text 中文语义区分度弱，top-1 余弦集中、无关段落分数高于正确答案 | 高 | open | E2-embed 实验换 bge-m3 / bge-large-zh 重建索引 |
| I02 | 2026-10-06 | 30 题样本量小，单题权重 3.3%，指标波动风险大 | 中 | closed | eval-v2.0 扩到 238 题（30 人工 + 208 新题源自动质检入选） |
| I03 | 2026-10-06 | gold_evidence 字符串匹配受 chunk 边界错位影响，会误判检索失败 | 高 | closed | 升级为 chunk-level gold（gold_chunks），命中判定以 chunk_id 为准 |
| I04 | 2026-10-06 | KeyPointCoverage 逐字匹配口径偏严，把正确答案判为 0 分 | 高 | closed | 改为 jieba 分词后 token 重叠率判定（阈值 0.5） |
| I05 | 2026-10-06 | 缺少直接度量“幻觉”的指标 | 中 | closed | 引入 Faithfulness（RAGAS 风格，qwen3:4b 裁判），需人工抽检校准 |
| I06 | 2026-10-06 | 对比型问题检索命中 0.50 但 KPC 仅 0.12，检索到但答不出 | 高 | open | E3-query rewrite / 对比型专用 prompt 实验 |
| I07 | 2026-10-07 | 试卷 OCR 解析有噪声，部分题干/选项粘连，影响 eval-v2.0 质量 | 中 | closed | 弃用旧三份 OCR 试卷；改用带标准答案的 6 份新题源 + 全自动质检（A1 去重/A2 gold 映射/A3 答案支撑/A4 时代缺图过滤），见 `data/eval/audit_report_v2.0.md` |
| I08 | 2026-10-07 | 计算型题目受 OCR 公式/表格失真影响，检索与生成均困难 | 中 | open | 计算题单列统计，不混入总均值；论文 limitation 明示 |
| I09 | 2026-10-07 | **排序偏后是首要瓶颈**：Baseline v2.0 失败类型中 `rank_miss` 占 39.1%（93 题）> `retrieval_miss` 34.5%（82 题），HitRate@5=0.265 vs @50=0.656，证据多在 top-50 内但排不进 top-5 | 高 | open | E1 引入 rerank（bge-reranker / monoT5）对 top-50 候选重排；同时对比 BM25 / Hybrid 检查是否为稠密检索排序退化 |
| I10 | 2026-10-07 | Faithfulness 仅 0.339，生成环节幻觉明显（另有 5.0% `generation_miss`） | 中 | open | E3/E4 收紧生成 prompt（强制引用上下文、拒答机制）+ 答案覆盖度评估；必要时换更大生成模型对比 |
