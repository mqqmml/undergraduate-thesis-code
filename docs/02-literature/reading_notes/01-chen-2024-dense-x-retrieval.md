阅读卡：稠密检索：该用什么检索粒度？（Dense X Retrieval: What Retrieval Granularity Should We Use?）

作者 / 来源：Tong Chen, Hongwei Wang, Sihao Chen 等（Microsoft / 中科大等），arXiv:2312.06648，EMNLP 2024

核心观点：
检索的基本单元不该是句子或段落，而应是"命题（proposition）"——把文本分解成原子化、自包含、可独立验证的事实陈述，语义更纯粹、粒度更细，能同时提升稠密检索与下游问答。

文章主要论据 / 关键内容：
- 提出命题作为新的检索粒度；
- 用 LLM 把段落自动分解为命题并配"固定 token 预算"做公平对比；
- 在 5 个开放域问答数据集上，命题检索在 top-20 段落召回率和下游 QA 上均优于句子/段落粒度；
- 开卷 QA 上命题索引增益更明显。

个人收获 / 思考：
粒度消融必须控制 token 预算，否则"越大越好"可能只是上下文更长的伪影；命题化思想可迁移到毕设的切块（chunk）策略设计。
