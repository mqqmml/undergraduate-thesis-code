# 技术路线

## 题目

面向垂直领域的 RAG 问答系统设计与检索策略优化

## 总体思路

针对一个明确的垂直领域，构建领域知识库与评测问题集，搭建基础 RAG（检索增强生成）问答系统作为 Baseline；随后系统研究检索环节各设计因素（chunk size、top-k、embedding 模型等）对检索质量（Recall / MRR / Hit Rate）与生成质量（Faithfulness、回答完整度）的影响，通过对比实验与消融实验定位瓶颈，最后引入 Rerank、Query Rewrite、Agentic RAG 等策略完成检索优化。

## 技术选型（初版，随进展更新）

| 模块 | 方案 | 备选 |
|---|---|---|
| LLM 推理 | Ollama 本地部署 | 云端 API |
| 检索框架 | LangChain / LangGraph | LlamaIndex |
| 向量库 | FAISS | Neo4j（图检索）、Chroma |
| Embedding | bge-m3 / bge-large-zh | text-embedding 系列 |
| 评测 | RAGAS（Faithfulness 等）+ 自建检索评测集 | TruLens |
| 后端服务 | FastAPI | — |

## 实验设计概览

| 实验 | 内容 | 指标 |
|---|---|---|
| Baseline | 基础 RAG（固定切分 + 向量检索 + 直接生成） | Recall / MRR / Hit Rate / Faithfulness / 完整度 |
| 对比实验 | ≥2 种有显著区别的检索方案（如：稠密向量检索 vs BM25/混合检索，或不同 embedding） | 同上 |
| 消融实验 | chunk size、top-k、embedding 等逐一更换 | 同上 |
| 优化实验 | Rerank / Query Rewrite / Agentic RAG | 同上 + 端到端回答质量 |

详细实验设计见 [`../03-design/experiment_design.md`](../03-design/experiment_design.md)。

## 阶段计划

- [ ] 阶段一：确定垂直领域，构建知识库与评测问题集（进行中）
- [ ] 阶段二：搭建 RAG Baseline 并跑通全链路
- [ ] 阶段三：检索方案对比实验 + 参数消融
- [ ] 阶段四：检索策略优化（Rerank / Query Rewrite / Agentic RAG）
- [ ] 阶段五：错误案例分析、论文撰写与定稿
