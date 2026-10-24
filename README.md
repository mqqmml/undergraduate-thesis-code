# 2027届本科毕业论文

## 基本信息

- 姓名：马武立夫
- 学号：202319120316
- 专业：智能科学与技术
- 指导教师：曾维
- 毕业论文题目：面向垂直领域的 RAG 问答系统设计与检索策略优化
- 研究方向：RAG / 大语言模型应用

## 一、研究问题

本论文的研究对象是**面向垂直领域的检索增强生成（RAG）问答系统**。通用大语言模型在垂直领域存在领域知识缺失、幻觉严重、回答不可溯源等问题，而朴素 RAG 方案在领域文档上常出现检索召回不准、切分粒度不当、生成忠实度不足的情况。本论文围绕一个明确的垂直领域构建知识库与评测问题集，系统研究文档切分（chunk size）、召回数量（top-k）、嵌入模型（embedding）等检索环节设计对召回质量（Recall / MRR / Hit Rate）与生成质量（Faithfulness、回答完整度）的影响，并在此基础上对检索策略进行优化，提升系统在垂直领域问答上的准确性与可靠性。

## 二、最低完成要求

- [x] 构建垂直领域知识库与评测问题集
- [x] 完成基础 RAG Baseline
- [x] 至少比较两种有显著区别的检索方案（或固定 Baseline 后系统研究 chunk size、top-k、embedding 等设计对 Retrieval Recall / MRR / Hit Rate 的影响）
- [x] 参数 / 组件消融实验（含 Faithfulness、回答完整度等指标）
- [x] 错误或异常情况分析
- [ ] 完整毕业论文

## 三、拓展目标

- [x] 引入 Rerank 重排序模块
- [ ] Query Rewrite 查询改写
- [ ] Agentic RAG（智能体化检索增强）

## 四、技术路线

总体流程：**垂直领域知识库构建 → 文档切分与向量化 → 多方案检索对比（chunk size / top-k / embedding）→ 生成与质量评测（Recall / MRR / Hit Rate / Faithfulness / 完整度）→ 参数与组件消融 → 错误案例分析 → 检索策略优化（Rerank / Query Rewrite / Agentic RAG）**。

详见 [`docs/01-topic/technical_route.md`](docs/01-topic/technical_route.md)。

## 五、当前进展

- 当前阶段：**E1 检索对比、E2 参数消融、E3 rerank 全部完成**，主结果表与分题型表已落盘，两周实验任务（老师 8 条）全部有数据支撑。
- 最近完成：
  - E1：Dense / BM25 / Hybrid(RRF) 三方案对比（238 题）；
  - E2：chunk 256/512/1024 × 三种检索、bge-m3 嵌入、top-k 3/5/10 生成消融，共 13 组实验；
  - E3：bge-reranker-base 重排序，人工 30 题 HR@5 0.633→0.900；
  - 老师第⑧条验证：同 30 题检索 HR@5 0.467→0.900，KPC 0.436→0.891，检索提升真实传导到生成质量；
  - 发现并量化评测集构造偏差（自动题 gold 偏词法），确立"全量 + 人工子集"双口径报告规范。
- 当前问题：
  - 自动生成题的 gold_chunks 由 idf 词重叠映射产生，偏向词法匹配（BM25 全量 0.744 vs 人工子集 0.533），论文必须双口径报告；
  - CitationRate 随 top-k 增大坍塌（0.967→0.700→0.133），大上下文下 qwen3:4b 不再标注引用；
  - 对比型/多跳型题目占比偏低，query rewrite 实验待做。
- 下一步：
  1. Query Rewrite 查询改写实验（缓解对比型、多跳型）；
  2. 进入 Agentic RAG 方向；
  3. 论文实验章节初稿。

## 六、主要实验结果

| Experiment | Result | Status |
|---|---|---|
| baseline v1.0（30 题，旧口径） | HitRate@5=0.467 / MRR=0.276 / KPC=0.436 / CitationRate=0.60 | 已完成 |
| baseline v2.0 检索（238 题，新口径，--no-gen） | HitRate@5=0.265 / HitRate@50=0.656 / MRR=0.164 | 已完成 |
| **baseline v2.0 完整（238 题，含生成 + Faithfulness）** | **HitRate@5=0.265 / @10=0.357 / @20=0.479 / @50=0.656；Recall@50=0.476；MRR=0.164；KPC=0.494；CitationRate=0.50；Faithfulness=0.339** | **已完成** |
| exp01（检索方案对比：Dense / BM25 / Hybrid） | 见下方 E1~E3 主结果 | 已完成 |
| exp02（参数消融：chunk / top-k / embedding） | 见下方 E1~E3 主结果 | 已完成 |

> 上表为 Baseline 阶段结果。E1~E3 完整矩阵见下。

### E1~E3 主结果（全量 238 题，--no-gen 检索口径）

| 实验 | 检索 | rerank | chunk | HR@5 | HR@50 | MRR |
|---|---|---|---|---|---|---|
| e2-chunk1024-bm25 | BM25 | - | 1024 | **0.777** | 0.979 | **0.588** |
| e1-bm25 | BM25 | - | 512 | 0.744 | 0.975 | 0.594 |
| e2-embed-bge-m3-hybrid | Hybrid | - | 512 | 0.719 | 0.971 | 0.517 |
| e2-chunk256-bm25 | BM25 | - | 256 | 0.685 | 0.966 | 0.513 |
| e1-hybrid | Hybrid | - | 512 | 0.580 | 0.958 | 0.409 |
| e2-embed-bge-m3-dense | Dense(bge-m3) | - | 512 | 0.559 | 0.895 | 0.369 |
| e1-dense | Dense(nomic) | - | 512 | 0.265 | 0.655 | 0.164 |
| e3-bm25-1024-rerank | BM25 | ✓ | 1024 | 0.664 | 0.979 | 0.481 |

### 人工 30 题子集（可信口径）

| 方案 | HR@5 | MRR | KPC | Faith | Citation |
|---|---|---|---|---|---|
| baseline（dense-512, top5） | 0.467 | 0.286 | 0.561 | 0.375 | 0.567 |
| baseline + BM25-1024 | 0.633 | 0.452 | - | - | - |
| **BM25-1024 + rerank** | **0.900** | **0.698** | - | - | - |
| + top-k=3 | 0.900 | 0.698 | 0.854 | 0.722 | 0.967 |
| + top-k=5 | 0.900 | 0.698 | **0.891** | 0.707 | 0.700 |
| + top-k=10 | 0.900 | 0.698 | 0.844 | 0.791 | 0.133 |

**核心结论**：
1. 检索方案排序：BM25 > Hybrid(RRF) > Dense（词法型语料 + 词法偏置评测集双因素）；
2. rerank 在人工题上收益最大（+0.267 HR@5），在自动题上被评测偏差掩盖（-0.113）——**必须双口径报告**；
3. KPC 倒 U 型峰值在 top_k=5；CitationRate 随 top_k 单调坍塌；
4. 检索提升真实传导到生成质量（同 30 题同口径：KPC 0.561→0.891，Faithfulness 0.375→0.707）。

**失败类型分布**（n=238，判定顺序：无 gold 命中→`retrieval_miss`；命中但不在 top-5→`rank_miss`；答案覆盖不足→`generation_miss`）：

| 失败类型 | 占比 | 题数 | 含义 |
|---|---|---|---|
| `rank_miss` | 39.1% | 93 | 证据在 top-50 内但排在 top-5 之后（可被 rerank 修复） |
| `retrieval_miss` | 34.5% | 82 | top-50 内完全没有 gold chunk（需换 embedding / 混合检索） |
| `ok` | 21.4% | 51 | 检索命中且答案覆盖达标 |
| `generation_miss` | 5.0% | 12 | 检索到但生成答案未覆盖关键点 |

> v1.0 详细结果见 `results/baseline/summary.json`；v2.0 见 `results/baseline_v2/summary.json`、`results/baseline_v2/per_question.csv`（逐题明细）与 `data/eval/audit_report_v2.0.md`。

## 七、仓库目录说明

| 目录 | 用途 |
|---|---|
| `docs/` | 选题、文献、系统设计、组会记录 |
| `knowledge_base/` | 知识库模块入口（语料、清单、索引的说明与复现流程） |
| `evaluation/` | 评测模块入口（评测集、指标、评测脚本与结果的说明） |
| `src/` | 源代码 |
| `configs/` | 配置文件（模型超参、实验配置等） |
| `scripts/` | 数据处理、训练、评估、绘图脚本 |
| `data/` | 数据集说明与元信息（原始数据不入库，见 `data/README.md`） |
| `experiments/` | 各组实验（baseline、exp01…），含配置与结果记录 |
| `results/` | 结果表格、图、日志、checkpoint（大文件不入库） |
| `thesis/` | 论文大纲、图、表、草稿、参考文献 |
| `progress/` | 里程碑、周报、问题跟踪 |

## 八、本人主要贡献

- 构建领域语料与评测集：完成《计算机网络》6 章 OCR 文本清洗、切分、索引，以及 30 题试点评测集标注；
- 实现朴素 RAG Baseline：包括文档加载、固定字符切分、FAISS 稠密检索、Ollama 本地生成、检索与生成指标计算；
- 诊断分析：基于 k=100 复算与相似度分布分析，定位当前 Baseline 瓶颈在于 embedding 中文区分度不足与排序偏后，撰写问题分析报告；
- 实验设计：制定 E0–E4 五类实验、对照组命名规范、预设成功判据与失败根因编码表；
- 代码与文档维护：仓库目录结构、README、里程碑、周报、阅读卡、指标口径修正。

## 九、参考项目与第三方代码

| 项目 | URL | License | 本项目修改内容 |
|---|---|---|---|
|  |  |  |  |

## 十、环境与复现

- OS：Windows 11
- Python：3.13.12（项目虚拟环境 `F:\undergraduate\.venv`）
- 核心依赖：LangChain / Ollama / FAISS / PyMuPDF / RapidOCR / jieba / rank-bm25
- 本地大模型：Ollama + `qwen3:4b`（生成）+ `nomic-embed-text`（嵌入）
- 模型路径：`OLLAMA_MODELS=D:\Model`

复现命令：

```bash
# 1. 建索引（分批嵌入，约 11 秒）
python -m src.index

# 2. 只评检索指标（秒级）
python -m src.evaluate --no-gen

# 3. 完整评测（检索 + 生成 + Faithfulness；238 题约 6.8 小时，30 题约 25–40 分钟）
python -m src.evaluate
```

---

## 协作约定

- 分支：`main` 保持可用；实验在 `exp/*` 分支进行
- 提交信息：`type(scope): 简述`，如 `exp(baseline): 添加复现脚本`
- 大文件（数据集、checkpoint、模型权重）一律不入库，用 `.gitignore` 排除
- 每周更新 `progress/weekly_log.md`
