阅读卡：检索增强大语言模型中的查询改写（Query Rewriting in Retrieval-Augmented Large Language Models）

作者 / 来源：Xinbei Ma, Yeyun Gong, Pengcheng He, Hai Zhao, Nan Duan（上海交大 / 微软），arXiv:2305.14283，EMNLP 2023

核心观点：
在 RAG 中先对用户原始查询做改写（"改写—检索—阅读"），能让检索与阅读更有效，且改写器可用强化学习、以最终答案质量作奖励来端到端优化。

文章主要论据 / 关键内容：
- 提出 Rewrite-Retrieve-Read 框架；
- 改写器既可用大模型提示实现，也可用强化学习（以阅读器/答案质量作奖励）训练；
- 在开放域问答上改写带来一致提升。

个人收获 / 思考：
该文后端是 web 搜索，与本地 FAISS 检索不可直接类比；RL 训练本课题做不了，毕设只能做 prompt 级/LLM 改写，需明确定位。
