# evaluation — 评测模块

> 本目录是评测模块的**入口索引**，实际代码与数据按既有路径存放（见下表），保持与已跑通的评测链路一致。

## 一、模块职责

构建垂直领域问答评测集，实现检索质量与生成质量的自动评测，产出可复现的实验指标与失败分析数据。

## 二、内容清单与位置

| 内容 | 路径 | 是否入库 |
|---|---|---|
| 评测集（30 题 v1.0） | `data/eval/questions.jsonl` | ✅ |
| 评测集统计与质检记录 | `data/metadata/eval_stats.md` | ✅ |
| 指标实现（纯 Python，无 LLM 依赖） | `src/metrics.py` | ✅ |
| 评测主脚本 | `src/evaluate.py` | ✅ |
| 生成模块（被评测调用） | `src/generate.py` | ✅ |
| 结果：汇总指标 | `results/<实验名>/summary.json` | ✅ |
| 结果：逐题明细 | `results/<实验名>/per_question.csv` | ✅ |
| 结果：检索日志 | `results/<实验名>/retrieval_log.jsonl` | ✅ |

## 三、评测集规格（v1.0）

- 规模 30 题：事实型 8 / 对比型 8 / 过程型 8 / 多跳型 4 / 计算型 2，覆盖全部 6 章
- 字段：`id`、`type`、`difficulty`、`question`、`gold_answer`、`gold_evidence`（语料逐字片段 1–3 条）、`key_points`
- 质检：30/30 题 gold_evidence 归一化后可在语料中逐字命中；key_points 均出现在 gold_answer 中
- 计划：中期前扩充至 150–300 题，冻结为 v2.0，与 v1.0 结果分开报告

## 四、指标定义

| 层 | 指标 | 判定方式 |
|---|---|---|
| 检索 | HitRate@k | top-k 内是否含任一 gold_evidence（是记 1） |
| 检索 | Recall@k | top-k 命中证据数 / 该题全部证据数 |
| 检索 | MRR | 第一条命中证据排名的倒数 |
| 生成 | KeyPointCoverage | 答案覆盖 key_points 的比例（归一化后逐字包含判定） |
| 生成 | CitationRate | 答案中是否含 `[片段x]` 标注 |
| 生成 | Faithfulness | ⬜ 待引入（RAGAS + 本地裁判 + 人工标注校准） |
| 失败分类 | failure_type | `ok` / `retrieval_miss` / `rank_miss` / `generation_miss` |

## 五、用法

```bash
python -m src.evaluate              # 完整评测：检索 + 生成 + 指标（30 题约 25 min）
python -m src.evaluate --no-gen     # 只评检索指标（秒级，用于快速筛选配置）
python -m src.evaluate --limit 5    # 只评前 5 题（调试用）
python -m src.evaluate --config configs/e1-rerank.yaml   # 指定实验配置
```

结果统一写入 `results/<配置中的 name>/`，实验名与配置文件 `name` 字段一致。

## 六、当前 Baseline 结果锚点

HitRate@5 = 0.467 ｜ MRR = 0.276 ｜ KeyPointCoverage = 0.436 ｜ CitationRate = 0.60
失败分布：retrieval_miss 43.3% / ok 30% / generation_miss 16.7% / rank_miss 10%

完整分析见 [`../docs/03-design/baseline_problem_analysis.md`](../docs/03-design/baseline_problem_analysis.md)。

## 七、已知口径问题（待修正，修正前不宜做方案对比）

| 问题 | 影响 | 计划 |
|---|---|---|
| 评测时 `max_k = 10`，排名 > 10 一律记为 retrieval_miss | 掩盖"排序偏后"这一类问题（实测 13 题中有 9 题是排名 11–100） | 提高到 20–50，重跑失败分类 |
| gold_evidence 逐字匹配 | 切分边界错位即判未命中，低估检索能力 | 改为 chunk 级标注或允许 ±1 chunk 邻域命中 |
| KeyPointCoverage 逐字关键词匹配 | 对改写、缩写零容忍，实测 5 例生成失败中 3 例为误判 | 扩充同义词表 / 改用嵌入相似度 / 引入 LLM 裁判并人工校准 |

## 八、实验纪律

- 评测集冻结后不得中途修改；如需修改，另立版本号并重跑全部对比实验
- prompt 模板属于实验变量，一经确定，对比实验期间不得单独调整
- 任何"某方案更优"的结论必须附：配置路径、样本量、效应量与 bootstrap 置信区间、失败反例
