"""检索：Baseline 只用一种方案 —— 单一稠密向量相似度检索 + 固定 Top-k。

对应 agentic_rag/utils/基础检索.py 的 similarity_search，区别是带上 chunk_id 与相似度分数，
方便评测模块计算 HitRate@k / Recall@k / MRR。
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.config import load_config
from src.index import load_index

_vectorstore = None
_cfg: Dict[str, Any] | None = None


def _get_vectorstore(cfg: Dict[str, Any] | None = None):
    """单例加载向量库，避免每次检索都读盘。"""
    global _vectorstore, _cfg
    if _vectorstore is None:
        _cfg = cfg or load_config()
        _vectorstore = load_index(_cfg)
    return _vectorstore


def retrieve(query: str, k: int | None = None, cfg: Dict[str, Any] | None = None) -> List[dict]:
    """返回 top-k 命中列表：[{rank, chunk_id, doc_id, score, text}]，rank 从 1 开始。"""
    cfg = cfg or _cfg or load_config()
    k = k or cfg["retrieve"]["top_k"]
    vs = _get_vectorstore(cfg)

    # FAISS 默认返回 L2 距离，越小越相似
    pairs = vs.similarity_search_with_score(query, k=k)
    results: List[dict] = []
    for rank, (doc, score) in enumerate(pairs, start=1):
        results.append(
            {
                "rank": rank,
                "chunk_id": doc.metadata.get("chunk_id"),
                "doc_id": doc.metadata.get("doc_id"),
                "score": float(score),
                "text": doc.page_content,
            }
        )
    return results


def retrieve_context(query: str, k: int | None = None, cfg: Dict[str, Any] | None = None) -> str:
    """拼接 top-k 文本作为上下文（生成模块用）。"""
    hits = retrieve(query, k=k, cfg=cfg)
    return "\n\n".join(f"[片段{i}] {h['text']}" for i, h in enumerate(hits, start=1))


if __name__ == "__main__":
    query = "TCP 为什么要三次握手"
    for h in retrieve(query, k=5):
        print(f"[{h['rank']}] 距离={h['score']:.4f} | {h['chunk_id']} | {h['text'][:60]!r} ...")
