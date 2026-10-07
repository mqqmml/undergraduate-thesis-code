"""评测指标 v2.0：支持 chunk 级 gold + 规则放宽的 KPC + RAGAS Faithfulness。

检索指标（命中判定可二选一，优先 chunk_id）
- HitRate@k : top-k 内是否命中任一 gold chunk
- Recall@k  : top-k 命中的 gold chunk 数 / 全部 gold chunk 数
- MRR       : 第一条命中 chunk 所在排名的倒数（未命中记 0）

生成指标
- KeyPointCoverage : 答案对标准答案关键点的覆盖比例（jieba 分词后 token 重叠）
- CitationRate     : 答案中带 [片段x] 标注的比例
- Faithfulness     : 答案论断可被上下文支撑的比例（需 LLM 裁判，可选）
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, List, Sequence, Set

import jieba

# 归一化：去掉空白 + 常见中英文标点 + Markdown 标记
_PUNCT = re.compile(r"[\s，。、；：？！,.;:?!”\"'()（）\[\]【】《》\-—_/\\|*#`~+=<>]+")
_CITE = re.compile(r"\[片段\s*\d+\]")


def normalize(text: str) -> str:
    """去空白与标点，英文转小写 —— 用于宽松包含判定。"""
    return _PUNCT.sub("", (text or "").lower())


def _tokens(text: str) -> List[str]:
    """对文本做归一化 + jieba 分词，返回非空 token 列表。"""
    norm = normalize(text)
    toks = [t for t in jieba.lcut_for_search(norm) if t and t.strip()]
    # 去重但保留顺序（用于覆盖判定）
    seen: Set[str] = set()
    out: List[str] = []
    for t in toks:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


# ---------- chunk 级命中判定 ----------

def _gold_chunk_ids(gold: dict | Sequence[str]) -> List[str] | None:
    """从 gold 对象中提取 chunk_id 列表；没有则返回 None。"""
    if isinstance(gold, dict):
        chunks = gold.get("chunks")
        if chunks:
            return [str(c) for c in chunks]
    return None


def _gold_evidences(gold: dict | Sequence[str]) -> Sequence[str]:
    """从 gold 对象中提取 evidence 字符串列表。"""
    if isinstance(gold, dict):
        return gold.get("evidences") or []
    return gold


def _matched_evidences(text: str, evidences: Sequence[str], min_len: int = 8) -> set[int]:
    """返回 text 命中的 evidence 下标集合（字符串包含）。"""
    norm_text = normalize(text)
    matched: set[int] = set()
    for i, ev in enumerate(evidences):
        norm_ev = normalize(ev)
        if len(norm_ev) < min_len:
            continue
        if norm_ev and norm_ev in norm_text:
            matched.add(i)
    return matched


def hit_rate_at_k(hits: List[dict], gold: dict | Sequence[str], k: int, min_len: int = 8) -> float:
    """top-k 内命中任一 gold 记 1，否则 0。优先 chunk_id，其次 evidence 字符串。"""
    chunks = _gold_chunk_ids(gold)
    if chunks:
        top_chunks = {h["chunk_id"] for h in hits[:k]}
        return 1.0 if any(c in top_chunks for c in chunks) else 0.0

    evidences = _gold_evidences(gold)
    for h in hits[:k]:
        if _matched_evidences(h["text"], evidences, min_len):
            return 1.0
    return 0.0


def recall_at_k(hits: List[dict], gold: dict | Sequence[str], k: int, min_len: int = 8) -> float:
    """top-k 命中的 gold 比例。"""
    chunks = _gold_chunk_ids(gold)
    if chunks:
        if not chunks:
            return 0.0
        top_chunks = {h["chunk_id"] for h in hits[:k]}
        matched = [c for c in chunks if c in top_chunks]
        return len(matched) / len(chunks)

    evidences = _gold_evidences(gold)
    valid = [e for e in evidences if len(normalize(e)) >= min_len]
    if not valid:
        return 0.0
    matched: set[int] = set()
    for h in hits[:k]:
        matched |= _matched_evidences(h["text"], evidences, min_len)
    return len(matched) / len(valid)


def mrr(hits: List[dict], gold: dict | Sequence[str], min_len: int = 8) -> float:
    """第一条命中 chunk 的排名倒数。"""
    chunks = _gold_chunk_ids(gold)
    if chunks:
        chunk_set = set(chunks)
        for h in hits:
            if h["chunk_id"] in chunk_set:
                return 1.0 / h["rank"]
        return 0.0

    evidences = _gold_evidences(gold)
    for h in hits:
        if _matched_evidences(h["text"], evidences, min_len):
            return 1.0 / h["rank"]
    return 0.0


def first_hit_rank(hits: List[dict], gold: dict | Sequence[str], min_len: int = 8) -> int | None:
    """第一条命中 chunk 的排名，未命中返回 None（失败类型分析）。"""
    chunks = _gold_chunk_ids(gold)
    if chunks:
        chunk_set = set(chunks)
        for h in hits:
            if h["chunk_id"] in chunk_set:
                return h["rank"]
        return None

    evidences = _gold_evidences(gold)
    for h in hits:
        if _matched_evidences(h["text"], evidences, min_len):
            return h["rank"]
    return None


# ---------- 生成指标 ----------

def keypoint_coverage(answer: str, key_points: Iterable[str], threshold: float = 0.5) -> float:
    """标准答案关键点覆盖比例（规则放宽版）。

    对每个 key_point：
      1. jieba 分词得到 tokens；
      2. 统计这些 token 在 answer 归一化文本中的命中比例；
      3. 比例 >= threshold 视为该要点被覆盖。

    相比 v1.0 的逐字包含，能容忍改写、缩写、语序变化。
    """
    points = [p for p in key_points if p and p.strip()]
    if not points:
        return float("nan")

    answer_norm = normalize(answer)
    answer_tokens = set(_tokens(answer))

    hit = 0
    for p in points:
        ptokens = _tokens(p)
        if not ptokens:
            continue
        # token 在答案中出现即算命中（兼顾同词与包含关系）
        matched = sum(1 for t in ptokens if t in answer_norm or t in answer_tokens)
        if matched / len(ptokens) >= threshold:
            hit += 1
    return hit / len(points)


def citation_rate(answer: str) -> float:
    """回答里是否带 [片段x] 引用标注（1 = 有，0 = 没有）。"""
    return 1.0 if _CITE.search(answer or "") else 0.0


# ---------- 失败分类 ----------

def classify_failure(hits: List[dict], gold: dict | Sequence[str], answer: str,
                     key_points: Iterable[str], top_k: int, min_len: int = 8,
                     kpc_threshold: float = 0.5) -> str:
    """失败类型判定，用于问题分析报告。

    返回 one of: ok / retrieval_miss / rank_miss / generation_miss
    - retrieval_miss : top_k 内没有命中证据 -> 检索阶段就丢了
    - rank_miss      : 证据在 top_k 之外（用 max_k 判断）
    - generation_miss: 证据命中但答案关键点覆盖不足 -> 生成阶段没用好上下文
    """
    rank = first_hit_rank(hits, gold, min_len)
    if rank is None:
        return "retrieval_miss"
    if rank > top_k:
        return "rank_miss"
    cov = keypoint_coverage(answer, key_points, kpc_threshold)
    if cov == cov and cov < kpc_threshold:
        return "generation_miss"
    return "ok"


# ---------- 聚合 ----------

def aggregate(rows: List[Dict[str, Any]], k_values: Sequence[int]) -> Dict[str, Any]:
    """把逐题结果聚合成 summary。"""
    n = len(rows)
    if n == 0:
        return {"n_questions": 0}

    def mean(key: str) -> float:
        vals = [r[key] for r in rows if isinstance(r.get(key), (int, float)) and r[key] == r[key]]
        return round(sum(vals) / len(vals), 4) if vals else float("nan")

    summary: Dict[str, Any] = {"n_questions": n}
    for k in k_values:
        summary[f"HitRate@{k}"] = mean(f"hit@{k}")
        summary[f"Recall@{k}"] = mean(f"recall@{k}")
    summary["MRR"] = mean("mrr")
    summary["KeyPointCoverage"] = mean("keypoint_coverage")
    summary["CitationRate"] = mean("citation_rate")
    if "faithfulness" in rows[0]:
        summary["Faithfulness"] = mean("faithfulness")

    fails: Dict[str, int] = {}
    for r in rows:
        fails[r.get("failure_type", "unknown")] = fails.get(r.get("failure_type", "unknown"), 0) + 1
    summary["failure_distribution"] = {k: round(v / n, 4) for k, v in sorted(fails.items())}
    summary["failure_counts"] = fails
    return summary
