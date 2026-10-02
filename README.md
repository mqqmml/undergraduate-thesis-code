# undergraduate-thesis-code

2027 届本科毕业设计工作仓库（题目待定，见 `docs/01-topic/topic_confirm.md`）。

## 目录结构

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

## 约定

- 分支：`main` 保持可用；实验在 `exp/*` 分支进行
- 提交信息：`type(scope): 简述`，如 `exp(baseline): 添加复现脚本`
- 大文件（数据集、checkpoint、模型权重）一律不入库，用 `.gitignore` 排除
- 每周更新 `progress/weekly_log.md`
