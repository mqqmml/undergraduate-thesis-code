"""检索：支持 dense / bm25 / hybrid 三种方案，可选叠加 rerank。

设计要点
- dense : FAISS 向量检索（Baseline 方案），距离越小越相似
- bm25  : rank_bm25 + jieba 分词；中文必须先分词，否则退化成字符匹配
- hybrid: dense 与 bm25 各取候选，再用 RRF（Reciprocal Rank Fusion）融合
- rerank: 对融合后的候选池做交叉编码器重排（默认关闭，cfg.retrieve.rerank.enabled）

对外接口保持兼容：retrieve(query, k, cfg) -> [{rank, chunk_id, doc_id, score, text}]
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

import jieba

from src.config import load_config, resolve
from src.index import load_index

_vectorstore = None
_cfg: Dict[str, Any] | None = None
_bm25: Any = None
_bm25_corpus: List[dict] | None = None


# ---------------------------------------------------------------- 稠密检索
def _get_vectorstore(cfg: Dict[str, Any] | None = None):
    """单例加载向量库，避免每次检索都读盘。"""
    global _vectorstore, _cfg
    if _vectorstore is None:
        _cfg = cfg or load_config()
        _vectorstore = load_index(_cfg)
    return _vectorstore


def _dense_search(query: str, k: int, cfg: Dict[str, Any]) -> List[dict]:
    vs = _get_vectorstore(cfg)
    # FAISS 默认返回 L2 距离，越小越相似
    pairs = vs.similarity_search_with_score(query, k=k)
    return [
        {
            "chunk_id": doc.metadata.get("chunk_id"),
            "doc_id": doc.metadata.get("doc_id"),
            "score": float(score),
            "text": doc.page_content,
        }
        for doc, score in pairs
    ]


# ---------------------------------------------------------------- BM25
def _tokenize_zh(text: str) -> List[str]:
    """jieba 搜索模式分词，过滤空白。"""
    return [t for t in jieba.lcut_for_search(text) if t.strip()]


def _load_bm25(cfg: Dict[str, Any]) -> Tuple[Any, List[dict]]:
    """从索引目录的 chunks.jsonl 构建 BM25（单例缓存）。"""
    global _bm25, _bm25_corpus
    if _bm25 is not None:
        return _bm25, _bm25_corpus or []

    from rank_bm25 import BM25Okapi

    path = resolve(cfg["index"]["persist_dir"]) / "chunks.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"chunk 映射不存在：{path}，请先运行 python -m src.index")

    corpus: List[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                corpus.append(json.loads(line))

    tokenized = [_tokenize_zh(c["text"]) for c in corpus]
    _bm25 = BM25Okapi(tokenized)
    _bm25_corpus = corpus
    print(f"[retrieve] BM25 索引就绪：{len(corpus)} 个 chunk")
    return _bm25, corpus


def _bm25_search(query: str, k: int, cfg: Dict[str, Any]) -> List[dict]:
    bm25, corpus = _load_bm25(cfg)
    scores = bm25.get_scores(_tokenize_zh(query))
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
    return [
        {
            "chunk_id": corpus[i]["chunk_id"],
            "doc_id": corpus[i].get("doc_id"),
            "score": float(scores[i]),
            "text": corpus[i]["text"],
        }
        for i in order
        if scores[i] > 0  # 全 0 说明无词命中，不返回噪声
    ]


# ---------------------------------------------------------------- 融合
def rrf_fuse(runs: List[List[dict]], k: int, rrf_k: int = 60) -> List[dict]:
    """Reciprocal Rank Fusion：score = Σ 1/(rrf_k + rank)，rank 从 1 开始。

    同一 chunk 在多路出现则分数累加；文本/元信息取首次出现的那份。
    """
    scores: Dict[str, float] = {}
    store: Dict[str, dict] = {}
    for run in runs:
        for rank, hit in enumerate(run, start=1):
            cid = hit["chunk_id"]
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
            store.setdefault(cid, hit)

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
    return [
        {
            "chunk_id": cid,
            "doc_id": store[cid].get("doc_id"),
            "score": round(score, 6),
            "text": store[cid]["text"],
        }
        for cid, score in ranked
    ]


# ---------------------------------------------------------------- 重排
def _rerank(query: str, candidates: List[dict], k: int, cfg: Dict[str, Any]) -> List[dict]:
    from src.rerank import rerank as do_rerank

    rc = cfg["retrieve"].get("rerank", {})
    model = rc.get("model", "BAAI/bge-reranker-base")
    depth = min(rc.get("depth", len(candidates)), len(candidates))
    return do_rerank(query, candidates[:depth], k=k, model_name=model)


# ---------------------------------------------------------------- 对外入口
def retrieve(query: str, k: int | None = None, cfg: Dict[str, Any] | None = None) -> List[dict]:
    """返回 top-k 命中列表：[{rank, chunk_id, doc_id, score, text}]，rank 从 1 开始。"""
    cfg = cfg or _cfg or load_config()
    k = k or cfg["retrieve"]["top_k"]
    rc = cfg["retrieve"]
    mode = rc.get("mode", "dense")
    use_rerank = bool(rc.get("rerank", {}).get("enabled", False))
    depth = rc.get("hybrid_depth", rc.get("candidate_depth", 50))

    # 一次取够候选：rerank 时池子要更宽
    pool_k = max(k, depth) if use_rerank or mode == "hybrid" else k

    if mode == "dense":
        hits = _dense_search(query, pool_k, cfg)
    elif mode == "bm25":
        hits = _bm25_search(query, pool_k, cfg)
    elif mode == "hybrid":
        dense_hits = _dense_search(query, pool_k, cfg)
        bm25_hits = _bm25_search(query, pool_k, cfg)
        hits = rrf_fuse([dense_hits, bm25_hits], k=pool_k, rrf_k=rc.get("rrf_k", 60))
    else:
        raise ValueError(f"未知 retrieve.mode：{mode}（可选 dense / bm25 / hybrid）")

    if use_rerank:
        hits = _rerank(query, hits, k, cfg)
    else:
        hits = hits[:k]

    for rank, h in enumerate(hits, start=1):
        h["rank"] = rank
    return hits


def retrieve_context(query: str, k: int | None = None, cfg: Dict[str, Any] | None = None) -> str:
    """拼接 top-k 文本作为上下文（生成模块用）。"""
    hits = retrieve(query, k=k, cfg=cfg)
    return "\n\n".join(f"[片段{i}] {h['text']}" for i, h in enumerate(hits, start=1))


if __name__ == "__main__":
    query = "TCP 为什么要三次握手"
    for h in retrieve(query, k=5):
        print(f"[{h['rank']}] score={h['score']:.4f} | {h['chunk_id']} | {h['text'][:60]!r} ...")
