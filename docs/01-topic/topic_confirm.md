# 选题确认

- **题目**：面向垂直领域的 RAG 问答系统设计与检索策略优化
- **研究方向**：RAG / 大语言模型应用
- **指导教师**：曾维
- **确认日期**：2026-10-02
- **状态**：已确认

## 导师建议的最低完成要求

1. 建立明确垂直领域知识库搭建与评测问题集
2. 完成基础 RAG Baseline
3. 至少比较两种有显著区别的检索方案（或固定 Baseline 后系统研究 chunk size、top-k、embedding 等设计对 Retrieval Recall / MRR / Hit Rate 的影响）
4. 跑通并做参数 / 组件消融实验（含 Faithfulness、回答完整度等指标）
5. 分析错误案例

## 拓展目标

- Rerank（重排序）
- Query Rewrite（查询改写）
- Agentic RAG

## 备注

- 题目来源于导师给的选题表（2026-10 确认）
- 可与华清远见实训的 Agentic RAG 智能问答系统项目（LangChain/LangGraph + FAISS + Neo4j + FastAPI + Ollama）联动，实训积累可作为 Baseline 与工程基础
- 垂直领域待定：需选择语料可得、有明确评测集构建方式的领域
