# 周报

## 2026-10-02

- 初始化仓库，搭建目录结构
- 本周计划：确定选题、搭建仓库骨架
- 本周完成：仓库初始化、选题信息填充
- 遇到的问题：无

## 2026-10-06

- 本周计划：跑通 Baseline、完成问题分析、整理文献阅读卡
- 本周完成：
  - 构建《计算机网络》6 章 OCR 语料知识库（1078 chunk）；
  - 完成 30 题 v1.0 评测集标注与朴素 RAG Baseline 全链路评测；
  - 输出《Baseline 问题分析报告 v1》与《实验设计 v1.0》；
  - 新增 `knowledge_base/`、`evaluation/` 模块说明；
  - 产出 5 篇核心阅读卡；
- 遇到的问题：
  - nomic-embed-text 中文语义区分度弱，HitRate@5 仅 0.467；
  - KeyPointCoverage 逐字匹配导致 3/5 生成失败为误判；
  - 30 题样本量小，结论稳定性不足。

## 2026-10-07

- 本周计划：修正评测口径、扩充测试集到 v2.0、重跑 Baseline
- 本周完成：
  - 改造评测代码：检索深度扩到 top-50、gold 升级为 chunk-level、KPC 改为 token 重叠、新增 Faithfulness；
  - 为现有 30 题生成 chunk-level gold；
  - **弃用**旧三份 OCR 试卷（噪声大、无标准答案），改用 6 份带标准答案的新题源：
    计算机网络技术题库（112 页扫描版，RapidOCR）、试题库含答案打印版、02141 试题、
    期末试题及答案、笔试题；
  - 解析 382 道候选题，全自动质检（A1 去重 66 / A2 gold 映射 / A3 答案支撑 81 / A4 时代缺图过滤 27），
    eval-v2.0 冻结为 **238 题**（30 人工 + 208 新题），弃人工抽检表流程；
  - 检索口径基线（--no-gen）：HitRate@5=0.265、HitRate@50=0.656、MRR=0.164；
  - **Baseline v2.0 完整重跑完成**（238 题，检索 + 生成 + Faithfulness，耗时 6h48m）：
    HitRate@5=0.265 / @10=0.357 / @20=0.479 / @50=0.656、Recall@50=0.476、MRR=0.164、
    KPC=0.494、CitationRate=0.50、Faithfulness=0.339；
    失败类型：`rank_miss` 39.1%（93）/ `retrieval_miss` 34.5%（82）/ `ok` 21.4%（51）/ `generation_miss` 5.0%（12）；
  - 更新 README、milestones、issues、eval_stats、requirements；
  - 代码与评测集推送至 GitHub `origin/main`（`0acbcc5`、`107af84`）。
- 遇到的问题：
  - nomic-embed-text 中文区分度不足在 238 题上更明显（HitRate@5 从 0.467 降至 0.265），E2 换 embedding 优先级提高；
  - **首要瓶颈是排序而非召回**：`rank_miss`（39.1%）超过 `retrieval_miss`（34.5%），HitRate@5 与 @50 相差 0.39，说明引入 rerank 的收益空间最大；
  - Faithfulness 仅 0.339，生成环节幻觉偏多，需在 E3/E4 一并治理；
  - 对比型/多跳型题目占比偏低（自动质检过滤较严），后续可定向补充。
- 下周计划：
  - 启动 E1 检索方案对比（Dense / BM25 / Hybrid）；
  - 启动 E2 参数消融（chunk size / top-k / embedding）；
  - 引入 rerank 针对 `rank_miss` 做专项验证。
