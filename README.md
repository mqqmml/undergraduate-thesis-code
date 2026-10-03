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

- [ ] 构建垂直领域知识库与评测问题集
- [ ] 完成基础 RAG Baseline
- [ ] 至少比较两种有显著区别的检索方案（或固定 Baseline 后系统研究 chunk size、top-k、embedding 等设计对 Retrieval Recall / MRR / Hit Rate 的影响）
- [ ] 参数 / 组件消融实验（含 Faithfulness、回答完整度等指标）
- [ ] 错误或异常情况分析
- [ ] 完整毕业论文

## 三、拓展目标

- [ ] 引入 Rerank 重排序模块
- [ ] Query Rewrite 查询改写
- [ ] Agentic RAG（智能体化检索增强）

## 四、技术路线

总体流程：**垂直领域知识库构建 → 文档切分与向量化 → 多方案检索对比（chunk size / top-k / embedding）→ 生成与质量评测（Recall / MRR / Hit Rate / Faithfulness / 完整度）→ 参数与组件消融 → 错误案例分析 → 检索策略优化（Rerank / Query Rewrite / Agentic RAG）**。

详见 [`docs/01-topic/technical_route.md`](docs/01-topic/technical_route.md)。

## 五、当前进展

- 当前阶段：开题准备（选题已确认，技术路线细化中）
- 最近完成：初始化仓库目录结构，确认论文题目与最低完成要求
- 当前问题：垂直领域与评测问题集尚未选定
- 下一步：确定具体垂直领域，构建知识库与评测问题集，跑通 RAG Baseline

## 六、主要实验结果

| Experiment | Result | Status |
|---|---|---|
| baseline（基础 RAG） | - | 未开始 |
| exp01（检索方案对比） | - | 未开始 |
| exp02（参数消融：chunk size / top-k / embedding） | - | 未开始 |

## 七、仓库目录说明

| 目录 | 用途 |
|---|---|
| `docs/` | 选题、文献、系统设计、组会记录 |
| `src/` | 源代码 |
| `configs/` | 配置文件（模型超参、实验配置等） |
| `scripts/` | 数据处理、训练、评估、绘图脚本 |
| `data/` | 数据集说明与元信息（原始数据不入库，见 `data/README.md`） |
| `experiments/` | 各组实验（baseline、exp01…），含配置与结果记录 |
| `results/` | 结果表格、图、日志、checkpoint（大文件不入库） |
| `thesis/` | 论文大纲、图、表、草稿、参考文献 |
| `progress/` | 里程碑、周报、问题跟踪 |

## 八、本人主要贡献

明确说明本人完成的代码、实验、数据和论文工作。若使用第三方项目，应注明来源。

> 待填写（随论文推进持续更新）。

## 九、参考项目与第三方代码

| 项目 | URL | License | 本项目修改内容 |
|---|---|---|---|
|  |  |  |  |

## 十、环境与复现

Python / MCU / FPGA / OS / 依赖版本等。

> 待填写。

---

## 协作约定

- 分支：`main` 保持可用；实验在 `exp/*` 分支进行
- 提交信息：`type(scope): 简述`，如 `exp(baseline): 添加复现脚本`
- 大文件（数据集、checkpoint、模型权重）一律不入库，用 `.gitignore` 排除
- 每周更新 `progress/weekly_log.md`
