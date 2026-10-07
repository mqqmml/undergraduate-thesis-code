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
- [ ] 至少比较两种有显著区别的检索方案（或固定 Baseline 后系统研究 chunk size、top-k、embedding 等设计对 Retrieval Recall / MRR / Hit Rate 的影响）
- [ ] 参数 / 组件消融实验（含 Faithfulness、回答完整度等指标）
- [x] 错误或异常情况分析
- [ ] 完整毕业论文

## 三、拓展目标

- [ ] 引入 Rerank 重排序模块
- [ ] Query Rewrite 查询改写
- [ ] Agentic RAG（智能体化检索增强）

## 四、技术路线

总体流程：**垂直领域知识库构建 → 文档切分与向量化 → 多方案检索对比（chunk size / top-k / embedding）→ 生成与质量评测（Recall / MRR / Hit Rate / Faithfulness / 完整度）→ 参数与组件消融 → 错误案例分析 → 检索策略优化（Rerank / Query Rewrite / Agentic RAG）**。

详见 [`docs/01-topic/technical_route.md`](docs/01-topic/technical_route.md)。

## 五、当前进展

- 当前阶段：**eval-v2.0（238 题）已冻结**，Baseline v2.0 重跑中（检索指标已完成，生成评测后台进行）。
- 最近完成：
  - 构建王道 408《计算机网络》6 章 OCR 语料知识库（373,650 字符，1078 个 chunk）；
  - 完成 30 题 v1.0 评测集标注与朴素 RAG Baseline 全链路评测；
  - 评测口径修正：检索深度扩到 top-50、gold 升级为 chunk-level、KPC 改分词重叠、引入 Faithfulness（qwen3:4b 裁判）；
  - eval-v2.0 扩充并冻结：从 6 份带标准答案的题库/试卷解析 382 道候选题，全自动质检（去重 66、时代/缺图过滤 27、gold 映射与答案支撑校验）后入选 208 题，合计 238 题；
  - 输出《Baseline 问题分析报告》《实验设计文档》与 5 篇核心阅读卡。
- 当前问题：
  - nomic-embed-text 中文区分度不足（I01），HitRate@5=0.265 / MRR=0.164，待 E2 换 embedding；
  - 对比型题目检索命中但答案覆盖低（I06），待 query rewrite 实验。
- 下一步：
  1. Baseline v2.0 完整重跑（生成 + Faithfulness）；
  2. 进入 E1/E2 检索方案与消融实验。

## 六、主要实验结果

| Experiment | Result | Status |
|---|---|---|
| baseline v1.0（30 题，旧口径） | HitRate@5=0.467 / MRR=0.276 / KPC=0.436 / CitationRate=0.60 | 已完成 |
| baseline v2.0 检索（238 题，新口径，--no-gen） | HitRate@5=0.265 / HitRate@50=0.656 / MRR=0.164 | 已完成 |
| baseline v2.0 完整（含生成 + Faithfulness） | 后台运行中 | 进行中 |
| exp01（检索方案对比） | - | 未开始 |
| exp02（参数消融：chunk / top-k / embedding） | - | 未开始 |

> v1.0 详细结果见 `results/baseline/summary.json`；v2.0 见 `results/baseline_v2/summary.json` 与 `data/eval/audit_report_v2.0.md`。

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

# 3. 完整评测（检索 + 生成 + Faithfulness，约 25–40 分钟）
python -m src.evaluate
```

---

## 协作约定

- 分支：`main` 保持可用；实验在 `exp/*` 分支进行
- 提交信息：`type(scope): 简述`，如 `exp(baseline): 添加复现脚本`
- 大文件（数据集、checkpoint、模型权重）一律不入库，用 `.gitignore` 排除
- 每周更新 `progress/weekly_log.md`
