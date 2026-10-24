"""评测偏差对照：人工标注题（30）vs 自动生成题（208）。

为什么必须做：208 道新题的 gold_chunks 由 idf 词重叠自动映射产生，
天然偏向词法匹配，可能抬高 BM25 一类的稀疏检索成绩。
用人工标注子集交叉验证，可以判断"BM25 领先"是真实优势还是评测集构造的伪影。

用法：
    python scripts/bias_check.py

输出：
    results/bias_check.md
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

# 目录名 -> 展示名（只列 238 题、检索侧已完成的实验）
RUNS = {
    "e1-dense": "Dense (nomic-embed-text)",
    "e1-bm25": "BM25 (chunk 512)",
    "e1-hybrid": "Hybrid RRF (nomic + BM25)",
    "e2-embed-bge-m3-dense": "Dense (bge-m3)",
    "e2-embed-bge-m3-hybrid": "Hybrid RRF (bge-m3 + BM25)",
    "e2-chunk256": "Dense (chunk 256)",
    "e2-chunk256-bm25": "BM25 (chunk 256)",
    "e2-chunk1024": "Dense (chunk 1024)",
    "e2-chunk1024-bm25": "BM25 (chunk 1024)",
    "e3-bm25-1024-rerank": "BM25 (chunk 1024) + Rerank",
    "e3-bgem3-dense-rerank": "Dense (bge-m3) + Rerank",
    "e3-bgem3-hybrid-rerank": "Hybrid RRF (bge-m3) + Rerank",
}

HUMAN_SOURCE = "v1.0人工"


def load_per_question(tag: str) -> Dict[str, dict]:
    p = RESULTS / tag / "per_question.csv"
    if not p.exists():
        return {}
    with open(p, encoding="utf-8-sig") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


def human_ids() -> set[str]:
    import json

    ids = set()
    with open(ROOT / "data" / "eval" / "questions_v2.0.jsonl", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                q = json.loads(line)
                if q.get("source") == HUMAN_SOURCE:
                    ids.add(q["id"])
    return ids


def mean(rows: List[dict], key: str) -> float:
    vals = [float(r[key]) for r in rows if r.get(key) not in (None, "", "nan")]
    return sum(vals) / len(vals) if vals else float("nan")


def main() -> None:
    hids = human_ids()
    lines = [
        "# 评测偏差对照：人工题 vs 自动题",
        "",
        f"人工标注题 {len(hids)} 道（gold 来自人工证据）；其余为自动映射题。",
        "自动题的 gold_chunks 由 idf 词重叠映射产生，偏向词法匹配，可能抬高 BM25 成绩。",
        "",
        "| 方案 | 全 238 题 HR@5 | 全 238 题 HR@50 | 全 238 题 MRR | 人工 30 题 HR@5 | 人工 30 题 HR@50 | 人工 30 题 MRR |",
        "|---|---|---|---|---|---|---|",
    ]
    for tag, name in RUNS.items():
        rows = load_per_question(tag)
        if len(rows) < 200:  # 跳过 --limit 试跑留下的残片
            continue
        all_rows = list(rows.values())
        h_rows = [rows[i] for i in hids if i in rows]
        a5, a50, am = mean(all_rows, "hit@5"), mean(all_rows, "hit@50"), mean(all_rows, "mrr")
        h5, h50, hm = mean(h_rows, "hit@5"), mean(h_rows, "hit@50"), mean(h_rows, "mrr")
        lines.append(
            f"| {name} | {a5:.3f} | {a50:.3f} | {am:.3f} | {h5:.3f} | {h50:.3f} | {hm:.3f} |"
        )

    lines += [
        "",
        "> 读法：两种口径的**排序**若不一致，说明结论受评测集构造影响，",
        "> 论文中必须同时报告，并以人工子集为准说明方法优劣。",
    ]
    out = RESULTS / "bias_check.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\n已写入 {out}")


if __name__ == "__main__":
    main()
