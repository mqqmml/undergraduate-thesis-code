阅读卡：面向开放域问答的稠密段落检索（Dense Passage Retrieval for Open-Domain Question Answering）

作者 / 来源：Vladimir Karpukhin, Barlas Oğuz, Sewon Min 等（Facebook AI），arXiv:2004.04906，EMNLP 2020

核心观点：
开放域问答不必依赖稀疏的 BM25，用双塔稠密编码器把问题和段落映射到同一向量空间、以内积做检索，仅用少量问答对训练就能在段落召回上大幅超越 BM25。

文章主要论据 / 关键内容：
- 双编码器（独立的问题塔与段落塔）架构；
- 用 in-batch negatives 作高效训练技巧；
- top-k 检索准确率与下游问答表现强相关；
- 在多个开放域问答基准上刷新当时最优结果。

个人收获 / 思考：
双塔可离线预计算文档向量，这正是"换 embedding 必须整体重建索引"的根因，是毕设 embedding 消融实验的工程前提。
