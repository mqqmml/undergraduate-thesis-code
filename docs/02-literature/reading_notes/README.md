# 精读阅读卡索引

约定：每张卡片记录一篇文献在**本课题中承担的角色**（借用它的什么、精读哪些章节、读后必须能回答什么），而非论文摘要。
卡片模板字段：一句话定位 / 为什么必须读 / 核心问题 / 方法与关键设计 / 主要结论 / 借鉴三件事 / 精读章节指引 / 读后应能回答 / 引用位置 / 注意与局限。

| # | 文献 | 角色 | 精读章节 | 状态 |
|---|---|---|---|---|
| 01 | [Chen 2024, Dense X Retrieval](01-chen-2024-dense-x-retrieval.md) | ★ 立论根基：chunk size（检索粒度）是核心自变量 | §1 引言、§3 三种粒度定义、§5 实验设置（固定 token 预算的控制方法）、§6 结论 | ⬜ 待精读 |
| 02 | [Karpukhin 2020, DPR](02-karpukhin-2020-dpr.md) | Baseline 检索方案来源（双塔 + FAISS） | §2 双塔结构、§3.1 in-batch negatives、§4 实验指标 | ⬜ 待精读 |
| 03 | [Es 2024, RAGAS](03-es-2024-ragas.md) | 评测章节方法依据（Faithfulness 的定义） | §3 指标定义、§4 与人工评估的一致性实验 | ⬜ 待精读 |
| 04 | [Ma 2023, Query Rewriting](04-ma-2023-query-rewriting.md) | 拓展目标②方法来源（Rewrite-Retrieve-Read） | §3 方法框架图、§4 实验设计 | ⬜ 待精读 |
| 05 | [Lewis 2020, RAG](05-lewis-2020-rag.md) | Baseline 定义来源，第一章必引，**答辩高频** | §2 架构（RAG-Sequence vs RAG-Token）、§5 主实验表 | ⬜ 待精读 |

**读的顺序建议**：05（建立整体框架）→ 02（搞清自己的检索方案）→ 01（找到自己的研究变量）→ 03（定评测方法）→ 04（规划优化实验）。

引用一律以 [`../verified_references.md`](../verified_references.md) 登记的著录为准，未登记文献不得写入论文。
