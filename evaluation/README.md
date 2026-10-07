# evaluation — 评测模块

> 本目录是评测模块的**入口索引**，实际代码与数据按既有路径存放（见下表），保持与已跑通的评测链路一致。

## 一、模块职责

构建垂直领域问答评测集，实现检索质量与生成质量的自动评测，产出可复现的实验指标与失败分析数据。

## 二、内容清单与位置

| 内容 | 路径 | 是否入库 |
|---|---|---|
| 评测集（238 题 v2.0，当前使用） | `data/eval/questions_v2.0.jsonl` | ✅ |
| 评测集（30 题 v1.0，历史版本） | `data/eval/questions.jsonl` | ✅ |
| 评测集（30 题带 chunk gold） | `data/eval/questions_v1.1.jsonl` | ✅ |
| 冻结清单与 sha256 | `data/eval/eval_v2.0_manifest.json` | ✅ |
| 自动质检报告 | `data/eval/audit_report_v2.0.md` | ✅ |
| 评测集统计 | `data/metadata/eval_stats.md` | ✅ |
| 指标实现（纯 Python，无 LLM 依赖） | `src/metrics.py` | ✅ |
| Faithfulness 裁判（LLM-as-judge） | `src/judge.py` | ✅ |
| 评测主脚本 | `src/evaluate.py` | ✅ |
| 生成模块（被评测调用） | `src/generate.py` | ✅ |
| 构建与 gold 映射脚本 | `scripts/build_eval_v2.py`、`scripts/map_gold_chunks.py` | ✅ |
| 结果：汇总指标 | `results/<实验名>/summary.json` | ✅ |
| 结果：逐题明细 | `results/<实验名>/per_question.csv` | ✅ |
| 结果：检索日志 | `results/<实验名>/retrieval_log.jsonl` | ✅ |

## 三、评测集规格（v2.0，238 题，已冻结）

- 规模 238 题 = v1.1 保留 30 题（人工标注）+ 新题源自动质检入选 208 题
- 题型：事实 147 / 计算 45 / 过程 20 / 对比 17 / 多跳 9
- 题源：计算机网络技术题库（yscl，扫描件 OCR）、试题库含答案打印版、02141 试题、期末试题及答案、笔试题
- 字段：`id`、`type`、`question`、`gold_answer`、`gold_chunks`（chunk_id 列表，命中判定依据）、`gold_evidence`（仅 v1.0 30 题保留可读片段）、`key_points`、`options` / `answer_letter`（选择题）、`source`
- 质检（全自动，取代人工填表）：A1 去重 66 / A2 gold 映射失败 / A3 答案支撑不达标 81 / A4 时代缺图过滤 27
- v1.0（30 题）作为历史版本保留，结果与 v2.0 分开报告

## 四、指标定义

| 层 | 指标 | 判定方式 |
|---|---|---|
| 检索 | HitRate@k | top-k 内是否含任一 gold chunk（k ∈ {1,3,5,10,20,50}） |
| 检索 | Recall@k | top-k 命中 gold chunk 数 / 该题全部 gold chunk 数 |
| 检索 | MRR | 第一条命中 gold chunk 排名的倒数 |
| 生成 | KeyPointCoverage | jieba 分词 + 归一化后的 token 重叠率（阈值 0.5） |
| 生成 | CitationRate | 答案中是否含 `[片段x]` 标注 |
| 生成 | Faithfulness | RAGAS 风格：答案拆 claims，逐条判是否被检索上下文支撑（qwen3:4b 裁判） |
| 失败分类 | failure_type | `ok` / `retrieval_miss`（top-50 内无 gold）/ `rank_miss`（top-50 内有 gold 但不在 top-5）/ `generation_miss`（检索到但答案覆盖不足） |

## 五、用法

```bash
python -m src.evaluate --no-gen     # 只评检索指标（秒级，用于快速筛选配置）
python -m src.evaluate              # 完整评测：检索 + 生成 + Faithfulness
python -m src.evaluate --limit 5    # 只评前 5 题（调试用）
python -m src.evaluate --config configs/baseline_v2.yaml   # 指定实验配置
```

结果统一写入 `results/<配置中的 name>/`，实验名与配置文件 `name` 字段一致。

## 六、当前 Baseline 结果锚点

**Baseline v2.0（238 题，新口径，2026-10-07，耗时 6h48m）**

HitRate：@1 0.067 / @3 0.193 / @5 **0.265** / @10 0.357 / @20 0.479 / @50 **0.656**
Recall：@5 0.153 / @50 0.476 ｜ MRR **0.164**
生成：KeyPointCoverage **0.494** ｜ CitationRate 0.500 ｜ Faithfulness **0.339**

失败分布：`rank_miss` 39.1%（93）/ `retrieval_miss` 34.5%（82）/ `ok` 21.4%（51）/ `generation_miss` 5.0%（12）

> **核心结论**：失败类型中排序问题（39.1%）已超过召回问题（34.5%），HitRate@5=0.265 而 @50=0.656——即大量 gold 证据「检索到了但排不进前 5」，**rerank 是收益最大的优化方向**（I09）。

历史锚点（v1.0，30 题，旧口径）：HitRate@5 = 0.467 ｜ MRR = 0.276 ｜ KPC = 0.436 ｜ CitationRate = 0.60；
旧口径失败分布 retrieval_miss 43.3% 系 `max_k=10` 截断所致，v2.0 已修正。

完整分析见 [`../docs/03-design/baseline_problem_analysis.md`](../docs/03-design/baseline_problem_analysis.md) 与 `results/baseline_v2/`。

## 七、口径修正记录（已于 v2.0 完成）

| 原问题 | 影响 | 处理 |
|---|---|---|
| `max_k = 10`，排名 > 10 一律记为 retrieval_miss | 掩盖「排序偏后」这一类问题 | ✅ 已扩到 top-50，新增 `rank_miss` 类别（现占 39.1%） |
| gold_evidence 逐字匹配 | 切分边界错位即判未命中，低估检索能力 | ✅ 已改为 chunk-level gold（`gold_chunks`，`match: chunk`） |
| KeyPointCoverage 逐字关键词匹配 | 对改写、缩写零容忍 | ✅ 已改为 jieba 分词 token 重叠率 |
| 缺少幻觉度量 | 无法量化生成忠实度 | ✅ 已引入 Faithfulness（LLM-as-judge），全量 238 题已跑 |
| 抽样人工核验（原计划 30 题填表） | 人工成本高 | ⬜ 待定：自动质检已就位，人工抽查作为可选校准，尚未执行 |

## 八、实验纪律

- 评测集冻结后不得中途修改；如需修改，另立版本号并重跑全部对比实验
- prompt 模板属于实验变量，一经确定，对比实验期间不得单独调整
- 任何"某方案更优"的结论必须附：配置路径、样本量、效应量与 bootstrap 置信区间、失败反例
