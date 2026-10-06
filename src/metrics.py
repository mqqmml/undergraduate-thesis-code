"""评测指标：纯 Python 实现，不依赖 LLM，便于单测和复现。

检索指标（判定依据：gold_evidence 原文片段是否出现在检索到的 chunk 中）
- HitRate@k : top-k 内是否命中任一证据
- Recall@k  : top-k 命中的证据数 / 全部证据数
- MRR       : 第一条命中证据所在排名的倒数（未命中记 0）

生成指标（无需 LLM 裁判，可离线算）
- KeyPointCoverage : 答案覆盖了多少个标准答案关键点
- CitationRate     : 答案中带 [片段x] 标注的比例（引用规范性）
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Sequence

# 归一化时去掉的字符：空白 + 常见中英文标点 + Markdown 标记
# （语料多为 Markdown，粗体 **、标题 #、表格 | 等符号不应影响证据匹配）
_PUNCT = re.compile(r"[\s，。、；：？！,.;:?!”\"'()（）\[\]【】《》\-—_/\\|*#`~+=<>]+")
_CITE = re.compile(r"\[片段\s*\d+\]")


def normalize(text: str) -> str:
    """去空白与标点，英文转小写 —— 用于宽松包含判定。"""
    return _PUNCT.sub("", (text or "").lower())


def _matched_evidences(text: str, evidences: Sequence[str], min_len: int = 8) -> set[int]:
    """返回 text 命中的证据下标集合。"""
    norm_text = normalize(text)
    matched: set[int] = set()
    for i, ev in enumerate(evidences):
        norm_ev = normalize(ev)
        if len(norm_ev) < min_len:
            continue
        if norm_ev and norm_ev in norm_text:
            matched.add(i)
    return matched


def hit_rate_at_k(hits: List[dict], evidences: Sequence[str], k: int, min_len: int = 8) -> float:
    """top-k 内命中任一证据记 1，否则 0。"""
    for h in hits[:k]:
        if _matched_evidences(h["text"], evidences, min_len):
            return 1.0
    return 0.0


def recall_at_k(hits: List[dict], evidences: Sequence[str], k: int, min_len: int = 8) -> float:
    """top-k 覆盖的证据比例（多证据题更有区分度）。"""
    valid = [e for e in evidences if len(normalize(e)) >= min_len]
    if not valid:
        return 0.0
    matched: set[int] = set()
    for h in hits[:k]:
        matched |= _matched_evidences(h["text"], evidences, min_len)
    return len(matched) / len(valid)


def mrr(hits: List[dict], evidences: Sequence[str], min_len: int = 8) -> float:
    """第一条命中证据的排名倒数。"""
    for h in hits:
        if _matched_evidences(h["text"], evidences, min_len):
            return 1.0 / h["rank"]
    return 0.0


def first_hit_rank(hits: List[dict], evidences: Sequence[str], min_len: int = 8) -> int | None:
    """第一条命中证据的排名，未命中返回 None（用于失败类型分析）。"""
    for h in hits:
        if _matched_evidences(h["text"], evidences, min_len):
            return h["rank"]
    return None


def keypoint_coverage(answer: str, key_points: Iterable[str]) -> float:
    """标准答案关键点覆盖比例。"""
    points = [p for p in key_points if p and p.strip()]
    if not points:
        return float("nan")
    norm_answer = normalize(answer)
    hit = sum(1 for p in points if normalize(p) in norm_answer)
    return hit / len(points)


def citation_rate(answer: str) -> float:
    """回答里是否带 [片段x] 引用标注（1 = 有，0 = 没有）。"""
    return 1.0 if _CITE.search(answer or "") else 0.0


def classify_failure(hits: List[dict], evidences: Sequence[str], answer: str,
                     key_points: Iterable[str], top_k: int, min_len: int = 8) -> str:
    """失败类型判定，用于 Baseline 问题分析报告。

    返回 one of: ok / retrieval_miss / rank_miss / generation_miss
    - retrieval_miss : top_k 内没有命中证据 -> 检索阶段就丢了
    - rank_miss      : 证据在 top_k 之外（这里用「检索范围外」统一表示排序偏后）
    - generation_miss: 证据命中但答案关键点覆盖不足 -> 生成阶段没用好上下文
    """
    rank = first_hit_rank(hits, evidences, min_len)
    if rank is None:
        return "retrieval_miss"
    if rank > top_k:
        return "rank_miss"
    cov = keypoint_coverage(answer, key_points)
    if cov == cov and cov < 0.6:  # 非 NaN 且覆盖不足
        return "generation_miss"
    return "ok"


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

    fails: Dict[str, int] = {}
    for r in rows:
        fails[r.get("failure_type", "unknown")] = fails.get(r.get("failure_type", "unknown"), 0) + 1
    summary["failure_distribution"] = {k: round(v / n, 4) for k, v in sorted(fails.items())}
    summary["failure_counts"] = fails
    return summary
