"""交叉编码器重排（Rerank）：把召回候选池按 query-段落相关性重排。

为什么需要：Baseline 的失败类型里 rank_miss 占 39.1%——证据已在 top-50 内但排不进前 5。
Rerank 直接对 (query, passage) 成对打分，能把"语义相关但向量不接近"的段落顶上来。

实现说明：
- 默认 BAAI/bge-reranker-base（中英双语，CPU 可跑，约 1.1GB）
- 首次运行会从 HuggingFace 下载；国内建议先设 HF_ENDPOINT=https://hf-mirror.com
- 模型按名字缓存，进程内只加载一次
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

_MODELS: Dict[str, Any] = {}

_LOCAL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")


def _resolve(model_name: str) -> str:
    """优先用本地 models/<basename>，避免每次联网下载（国内 HF 常被代理拦截）。"""
    if os.path.isdir(model_name):
        return model_name
    cand = os.path.join(_LOCAL_DIR, model_name.split("/")[-1])
    if os.path.isfile(os.path.join(cand, "config.json")):
        return cand
    return model_name


def _load(model_name: str, device: str = "cpu"):
    if model_name in _MODELS:
        return _MODELS[model_name]
    try:
        from sentence_transformers import CrossEncoder
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "未安装 sentence-transformers，请先执行：\n"
            "  pip install torch --index-url https://download.pytorch.org/whl/cpu\n"
            "  pip install --no-deps transformers sentence-transformers"
        ) from e

    path = _resolve(model_name)
    print(f"[rerank] 加载交叉编码器 {path}（device={device}）...")
    model = CrossEncoder(path, max_length=512, device=device)
    _MODELS[model_name] = model
    return model


def rerank(
    query: str,
    candidates: List[dict],
    k: int,
    model_name: str = "BAAI/bge-reranker-base",
    device: str = "cpu",
    batch_size: int = 32,
) -> List[dict]:
    """对 candidates 打分并返回前 k 条（保留原始字段，score 换成重排分数）。"""
    if not candidates:
        return []
    model = _load(model_name, device)
    pairs = [(query, c["text"]) for c in candidates]
    scores = model.predict(pairs, batch_size=batch_size, show_progress_bar=False)

    order = sorted(range(len(candidates)), key=lambda i: float(scores[i]), reverse=True)[:k]
    out: List[dict] = []
    for i in order:
        item = dict(candidates[i])
        item["score"] = float(scores[i])
        item["retrieve_score"] = candidates[i].get("score")
        out.append(item)
    return out


if __name__ == "__main__":
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    q = "TCP 为什么要三次握手"
    cands = [
        {"chunk_id": "a", "text": "TCP 三次握手用于同步序号并确认双方收发能力。"},
        {"chunk_id": "b", "text": "DHCP 用于动态分配 IP 地址。"},
    ]
    for r in rerank(q, cands, k=2, model_name="BAAI/bge-reranker-base"):
        print(r["chunk_id"], round(r["score"], 4))
