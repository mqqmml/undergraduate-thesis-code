# knowledge_base — 垂直领域知识库模块

> 本目录是知识库模块的**入口索引**，实际数据文件按既有路径存放（见下表），以免破坏已跑通的配置与可复现链路。

## 一、模块职责

构建并维护本课题的垂直领域（计算机网络）知识库：原始语料 → OCR 抽取 → 文档切分 → 向量化 → 建立检索索引。

## 二、内容清单与位置

| 内容 | 路径 | 是否入库 |
|---|---|---|
| 原始语料（OCR 后 Markdown，6 章 373,650 字符） | `data/raw/01~06-*.md` | ❌ 版权原因不入库 |
| 语料清单与规模统计 | `data/metadata/corpus_manifest.md` | ✅ |
| OCR 抽取脚本（可复现全流程） | `scripts/ocr_extract.py` | ✅ |
| 切分产物（1078 个 chunk） | `data/processed/chunks.jsonl`、`index/baseline/chunks.jsonl` | ❌ |
| 向量索引（FAISS） | `index/baseline/{index.faiss, index.pkl}` | ❌ |
| 索引构建代码 | `src/index.py`、`src/chunk.py` | ✅ |

## 三、语料来源

- **书目**：王道考研 2027《计算机网络复习指导》（408 统考复习指导系列），扫描版 PDF 316 页
- **领域范围**：考纲六章全部——体系结构、物理层、数据链路层、网络层、传输层、应用层
- **规模**：373,650 字符（约 37 万字），PDF 第 13–316 页
- **版权**：仅供本机学术研究与毕业论文实验使用，不上传仓库，论文引用时注明书目信息

## 四、复现流程

```bash
# 1. OCR 抽取（需本地准备教材扫描版 PDF；输出到 data/raw/）
python scripts/ocr_extract.py

# 2. 建索引：切分 + 分批嵌入 + 写入 FAISS（结果写入 index/baseline/）
python -m src.index

# 3. 检索自测
python -m src.retrieve
```

切分与嵌入参数全部在 `configs/<实验名>.yaml` 中：`chunk.size / chunk.overlap / embedding.model / index.embed_batch`。
**换 embedding 模型或换 chunk 参数必须重建索引**，索引目录按实验名分离（`index/<实验名>/`）。

## 五、已知质量问题（作为论文 limitation 素材）

1. OCR 偶发错字（如"接口"→"接和"），正文识别率约 98%+
2. 数学公式、二进制运算过程、表格类内容识别失真 → 计算类题目在评测集中单列，不混入总均值
3. 拓扑图、状态转移图的 caption 混入正文，图像本身丢失
4. 个别水印碎片（`KUKU` 等）未完全滤除

详见 `data/metadata/corpus_manifest.md`。

## 六、后续规划

若需将语料与索引物理迁移至本目录，必须同步修改三处，否则评测链路会断：

1. `configs/*.yaml` 的 `corpus.raw_dir`、`index.persist_dir`
2. `.gitignore` 中排除 `data/raw/` 的规则
3. `src/config.py` 的路径解析

迁移后需重跑 `python -m src.index` 与 `python -m src.evaluate --no-gen` 验证指标不变。
