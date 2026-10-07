# -*- coding: utf-8 -*-
"""把 questions.jsonl 中的 gold_evidence 原文片段映射为 chunk_id（gold_chunks）。

用法：
    python scripts/map_gold_chunks.py

输入：
    data/eval/questions.jsonl
    data/processed/chunks.jsonl

输出：
    data/eval/questions_v1.1.jsonl（原字段保留，新增 gold_chunks）
    data/eval/mapping_log.json（每题映射详情，便于人工复核）

映射规则（按优先级）：
1. 证据归一化后能在某个 chunk 归一化文本中找到 → 命中该 chunk；
2. 若不能，取证据前 20 字继续找；
3. 若仍不能，按 token 重叠率选最佳 chunk（>=0.3），并打印警告；
4. 若完全无法匹配，gold_chunks 为空，需人工补标。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Set

import jieba

ROOT = Path(__file__).resolve().parent.parent

_PUNCT = re.compile(r"[\s，。、；：？！,.;:?!”\"'()（）\[\]【】《》\-—_/\\|*#`~+=<>]+")


def normalize(text: str) -> str:
    return _PUNCT.sub("", (text or "").lower())


def tokens(text: str) -> List[str]:
    return [t for t in jieba.lcut_for_search(normalize(text)) if t and t.strip()]


def load_chunks(path: Path) -> Dict[str, dict]:
    chunks: Dict[str, dict] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            item["_norm"] = normalize(item["text"])
            item["_tokens"] = set(tokens(item["text"]))
            chunks[item["chunk_id"]] = item
    return chunks


def find_chunk_for_evidence(evidence: str, chunks: Dict[str, dict]) -> tuple[str | None, str]:
    """返回最佳 chunk_id 与匹配方式。"""
    norm_ev = normalize(evidence)
    if not norm_ev:
        return None, "empty"

    # 1. 完全子串
    for cid, c in chunks.items():
        if norm_ev in c["_norm"]:
            return cid, "substring"

    # 2. 前缀子串
    prefix = norm_ev[:20] if len(norm_ev) > 20 else norm_ev
    if prefix:
        for cid, c in chunks.items():
            if prefix in c["_norm"]:
                return cid, "prefix"

    # 3. token 重叠率
    ev_tokens = set(tokens(evidence))
    if not ev_tokens:
        return None, "fail"
    best_cid = None
    best_score = 0.0
    for cid, c in chunks.items():
        inter = ev_tokens & c["_tokens"]
        score = len(inter) / len(ev_tokens)
        if score > best_score:
            best_score = score
            best_cid = cid
    if best_cid and best_score >= 0.3:
        return best_cid, f"token_overlap_{best_score:.2f}"

    return None, "fail"


def main() -> None:
    questions_path = ROOT / "data" / "eval" / "questions.jsonl"
    chunks_path = ROOT / "data" / "processed" / "chunks.jsonl"

    with open(questions_path, "r", encoding="utf-8") as f:
        questions = [json.loads(line) for line in f if line.strip() and not line.strip().startswith("//")]

    chunks = load_chunks(chunks_path)
    print(f"[map] 载入 {len(questions)} 题，{len(chunks)} 个 chunk")

    log: List[Dict[str, Any]] = []
    warnings = 0

    for q in questions:
        q["gold_chunks"] = []
        detail = {"id": q["id"], "matches": []}
        seen_chunks: Set[str] = set()

        for ev in q.get("gold_evidence", []):
            cid, method = find_chunk_for_evidence(ev, chunks)
            detail["matches"].append({"evidence": ev, "chunk_id": cid, "method": method})
            if cid:
                if cid not in seen_chunks:
                    seen_chunks.add(cid)
                    q["gold_chunks"].append(cid)
            else:
                warnings += 1
                print(f"[warn] {q['id']} 无法映射证据: {ev[:40]!r}")

        log.append(detail)

    # 输出
    out_path = ROOT / "data" / "eval" / "questions_v1.1.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for q in questions:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    log_path = ROOT / "data" / "eval" / "mapping_log.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({"n_questions": len(questions), "warnings": warnings, "details": log}, f, ensure_ascii=False, indent=2)

    print(f"[map] 完成：新增 gold_chunks，输出 {out_path}")
    print(f"[map] 无法自动映射的题目数：{warnings} 条证据")
    print(f"[map] 日志见 {log_path}")


if __name__ == "__main__":
    main()
