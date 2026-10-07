阅读卡：面向知识密集型 NLP 任务的检索增强生成（Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks）

作者 / 来源：Patrick Lewis, Ethan Perez, Aleksandra Piktus 等（Facebook AI / UCL / NYU），arXiv:2005.11401，NeurIPS 2020

核心观点：
把预训练的参数记忆（seq2seq 生成器）与非参数记忆（维基百科稠密向量索引，经 DPR 检索）结合并端到端微调，使知识密集型任务既能生成、又能为输出提供依据、还能热更新知识。

文章主要论据 / 关键内容：
- 提出 RAG-Sequence（整段生成共用同一文档）与 RAG-Token（每个 token 可对应不同文档）两种形式；
- 在开放域问答上取得最优，生成更具体、更多样、更符合事实；
- 事实验证接近当时最优流水线；
- 替换索引即可更新世界知识。

个人收获 / 思考：
两种原版形式都需端到端训练加隐变量边缘化，毕设的"先检索后生成"严格说属 retrieve-then-read 工程化形态而非原版 RAG，答辩要讲清这一区别。
