# 已核实参考文献

- 课题：面向垂直领域的 RAG 问答系统设计与检索策略优化 ｜ 垂直领域：计算机网络
- 著录标准：GB/T 7714-2015 ｜ 核验日期：2026-10-03
- 核验说明：以下 13 篇的标题、作者、年份、出处、页码、DOI 均已与出版方页面（ACL Anthology / 会议官网）逐条核对一致。
- PDF 存放：`F:\qq文件\毕业论文\参考论文\`
- **约定：论文最终引用的文献只能从本表进入**，未登记、未核验的不得写入论文。

---

## 一、RAG 框架与检索基础

**1. LEWIS P, PEREZ E, PIKTUS A, et al.** Retrieval-augmented generation for knowledge-intensive NLP tasks[C]//Advances in Neural Information Processing Systems 33 (NeurIPS). 2020: 9459-9474. DOI: 10.48550/arXiv.2005.11401（论文集无正式 DOI，此为 arXiv 号）
PDF：`Lewis 2020, RAG.pdf` ｜ 用途：两段式 RAG 架构奠基，Baseline 定义来源

**2. KARPUKHIN V, OĞUZ B, MIN S, et al.** Dense passage retrieval for open-domain question answering[C]//Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP). 2020: 6769-6781. DOI: 10.18653/v1/2020.emnlp-main.550
PDF：`Karpukhin 2020, DPR.pdf` ｜ 用途：双塔稠密检索 + FAISS 方案来源

**3. ROBERTSON S, ZARAGOZA H.** The probabilistic relevance framework: BM25 and beyond[J]. Foundations and Trends in Information Retrieval, 2009, 3(4): 333-389. DOI: 10.1561/1500000019
PDF：`Robertson 2009, BM25.pdf` ｜ 用途：对比实验的稀疏检索一侧

**4. KHATTAB O, ZAHARIA M.** ColBERT: efficient and effective passage search via contextualized late interaction over BERT[C]//Proceedings of the 43rd International ACM SIGIR Conference on Research and Development in Information Retrieval. 2020: 39-48. DOI: 10.1145/3397271.3401075
PDF：`Khattab 2020, ColBERT.pdf` ｜ 用途：晚交互检索，混合检索参照

**5. SANTHANAM K, KHATTAB O, SAAD-FALCON J, et al.** ColBERTv2: effective and efficient retrieval via lightweight late interaction[C]//Proceedings of the 2022 Conference of the North American Chapter of the Association for Computational Linguistics (NAACL). 2022: 3715-3734. DOI: 10.18653/v1/2022.naacl-main.272
PDF：`Santhanam 2022, ColBERTv2.pdf` ｜ 用途：与 4 二选一（存储更省）

**6. REIMERS N, GUREVYCH I.** Sentence-BERT: sentence embeddings using Siamese BERT-networks[C]//Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP). 2019: 3982-3992. DOI: 10.18653/v1/D19-1410
PDF：`Reimers 2019, Sentence-BERT.pdf` ｜ 用途：双塔嵌入原理，embedding 选型依据

## 二、切分粒度与嵌入模型

**7. CHEN T, WANG H, CHEN S, et al.** Dense X retrieval: what retrieval granularity should we use?[C]//Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing (EMNLP). 2024: 15159-15177. DOI: 10.18653/v1/2024.emnlp-main.845
PDF：`Chen 2024, Dense X Retrieval.pdf` ｜ 用途：★ chunk size 消融实验的直接理论依据

**8. CHEN J, XIAO S, ZHANG P, et al.** M3-Embedding: multi-linguality, multi-functionality, multi-granularity text embeddings through self-knowledge distillation[C]//Findings of the Association for Computational Linguistics: ACL 2024. 2024: 2318-2335. DOI: 10.18653/v1/2024.findings-acl.137
PDF：`Chen 2024, M3-Embedding.pdf` ｜ 用途：中英混合语料的 embedding 选型依据（正式标题无 "BGE" 前缀）

## 三、检索优化与评测方法

**9. NOGUEIRA R, JIANG Z, PRADEEP R, et al.** Document ranking with a pretrained sequence-to-sequence model[C]//Findings of the Association for Computational Linguistics: EMNLP 2020. 2020: 708-718. DOI: 10.18653/v1/2020.findings-emnlp.63
PDF：`Nogueira 2020, monoT5.pdf` ｜ 用途：拓展目标① Rerank 方法来源

**10. MA X, GONG Y, HE P, et al.** Query rewriting in retrieval-augmented large language models[C]//Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing (EMNLP). 2023: 5303-5315. DOI: 10.18653/v1/2023.emnlp-main.322
PDF：`Ma 2023, Query Rewriting.pdf` ｜ 用途：拓展目标② Query Rewrite 方法来源（标题是 in，非 for）

**11. JIANG Z, XU F F, GAO L, et al.** Active retrieval augmented generation[C]//Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing (EMNLP). 2023: 7969-7992. DOI: 10.18653/v1/2023.emnlp-main.495
PDF：`Jiang 2023, FLARE.pdf` ｜ 用途：主动检索，Agentic RAG 前身

**12. ASAI A, WU Z, WANG Y, et al.** Self-RAG: learning to retrieve, generate, and critique through self-reflection[C]//International Conference on Learning Representations (ICLR). 2024. arXiv: 2310.11511（ICLR 论文集无 DOI）
PDF：`Asai 2024, Self-RAG.pdf` ｜ 用途：拓展目标③ Agentic RAG 代表作

**13. ES S, JAMES J, ESPINOSA-ANKE L, et al.** RAGAs: automated evaluation of retrieval augmented generation[C]//Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics (EACL): System Demonstrations. 2024: 150-158. DOI: 10.18653/v1/2024.eacl-demo.16
PDF：`Es 2024, RAGAS.pdf` ｜ 用途：Faithfulness 等生成侧指标的定义与算法依据

---

## 未收录（备选，真实存在但相关性偏低）

| 文献 | 未收录原因 |
|---|---|
| Gao 等, 2023. Retrieval-augmented generation for large language models: a survey (arXiv:2312.10997) | 无正式出处，仅可作背景综述 |
| Izacard & Grave, 2021. FiD (EACL 2021) | 生成侧融合，偏离检索主线 |
| Izacard 等, 2022. Contriever (arXiv:2112.09118) | 仅被 7 当基线提及 |
| Nogueira & Cho, 2019. Passage re-ranking with BERT (arXiv:1901.04085) | 结论已被 9 覆盖 |
| Thakur 等, 2021. BEIR (arXiv:2104.08663) | 英文检索基准，仅可借鉴评测组织方法 |

## 引用注意

1. 以会议/期刊正式出处为准，arXiv 编号仅作查证通道，标注 `[EB/OL]` 的不得作主要论据。
2. 作者超 3 人列前 3 人加 `等 / et al.`。
3. 本目录 PDF 仅本机学习使用，不上传 GitHub（仓库 `.gitignore` 已排除 `*.pdf`）。
