阅读卡：RAGAS：检索增强生成的自动化评估（RAGAS: Automated Evaluation of Retrieval Augmented Generation）

作者 / 来源：Shahul Es, Jithin James, Luis Espinosa-Anke, Steven Schockaert，arXiv:2309.15217，EACL 2024

核心观点：
RAG 系统可以不做人工标注，用 LLM 自动计算忠实度、答案相关性、上下文相关性三条"无参考"指标，即可对检索与生成环节做细粒度评估。

文章主要论据 / 关键内容：
- 提出三条无参考指标（忠实度＝答案能否由检索上下文支撑、答案相关性、上下文相关性）；
- 在 WikiEval 等数据上与人工判断有较好一致性；
- 无需标准答案即可横向比较不同 RAG 配置。

个人收获 / 思考：
忠实度这类无标注指标很适合毕设的自动评测；但用 4B 小模型当裁判存在偏差风险，必须做人工一致性（kappa）校准才可采信。
