"""汇总所有实验结果，生成论文用的主结果表 + 分题型表。

用法：
    python scripts/collect_results.py                 # 汇总 results/*/summary.json
    python scripts/collect_results.py --n 238         # 只收 238 题的实验（默认）

输出：
    results/main_table.md      主结果表（Markdown，直接贴论文）
    results/main_table.csv     同上，CSV
    results/by_type_table.md   分题型分解（每个实验一张小节）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

K_COLS = [1, 3, 5, 10, 20, 50]
METRIC_COLS = ["HitRate@5", "HitRate@20", "HitRate@50", "Recall@5", "Recall@50", "MRR",
               "KeyPointCoverage", "Faithfulness", "CitationRate"]


def load_runs(n: int | None) -> List[Dict[str, Any]]:
    runs = []
    for p in sorted(RESULTS.glob("*/summary.json")):
        try:
            s = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if n and s.get("n_questions") != n:
            continue
        s["_dir"] = p.parent.name
        runs.append(s)
    return runs


def fmt(v: Any) -> str:
    if isinstance(v, float):
        return "-" if v != v else f"{v:.3f}"
    return "-" if v is None else str(v)


def main_table(runs: List[Dict[str, Any]]) -> str:
    head = ["实验", "检索", "rerank", "chunk", "top_k", "embedding"] + \
           [f"HR@{k}" for k in K_COLS] + ["R@5", "R@50", "MRR", "KPC", "Faith", "Cite", "耗时"]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for s in runs:
        row = [
            s.get("experiment", s["_dir"]),
            s.get("retrieve_mode", "-"),
            "✓" if "rerank" in s.get("_dir", "") else "-",
            str(s.get("chunk_size", "-")),
            str(s.get("top_k", "-")),
            str(s.get("embedding_model", "-")).split(":")[0],
        ]
        row += [f"{s.get(f'HitRate@{k}', float('nan')):.3f}" if f"HitRate@{k}" in s else "-" for k in K_COLS]
        row += [fmt(s.get("Recall@5")), fmt(s.get("Recall@50")), fmt(s.get("MRR")),
                fmt(s.get("KeyPointCoverage")), fmt(s.get("Faithfulness")), fmt(s.get("CitationRate"))]
        row.append(f"{s.get('elapsed_sec', 0)/60:.0f}m")
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def by_type_tables(runs: List[Dict[str, Any]]) -> str:
    out: List[str] = []
    for s in runs:
        bt = s.get("by_type")
        if not bt:
            continue
        out.append(f"\n### {s.get('experiment', s['_dir'])}（n={s.get('n_questions')}）\n")
        head = ["题型", "n", "HR@5", "HR@50", "Recall@5", "MRR", "KPC", "Faith", "rank_miss", "retrieval_miss"]
        out.append("| " + " | ".join(head) + " |")
        out.append("|" + "---|" * len(head))
        for t, b in bt.items():
            fd = b.get("failure_distribution", {})
            out.append("| " + " | ".join([
                t, str(b.get("n_questions")),
                fmt(b.get("HitRate@5")), fmt(b.get("HitRate@50")), fmt(b.get("Recall@5")),
                fmt(b.get("MRR")), fmt(b.get("KeyPointCoverage")), fmt(b.get("Faithfulness")),
                fmt(fd.get("rank_miss")), fmt(fd.get("retrieval_miss")),
            ]) + " |")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=238, help="只汇总该题量的实验（0 表示不过滤）")
    args = ap.parse_args()

    runs = load_runs(args.n or None)
    if not runs:
        raise SystemExit("没有可汇总的结果")
    # 只保留有检索指标的（排除早期 v1.0 实验）
    runs = [s for s in runs if "HitRate@5" in s]
    runs.sort(key=lambda s: (s.get("elapsed_sec", 0) > 3600, -s.get("HitRate@5", 0)))

    md = "# 主结果表\n\n" + main_table(runs) + "\n"
    (RESULTS / "main_table.md").write_text(md, encoding="utf-8")
    print(md)

    # CSV
    import csv
    keys = ["experiment", "retrieve_mode", "chunk_size", "top_k", "embedding_model"] + METRIC_COLS
    with open(RESULTS / "main_table.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for s in runs:
            w.writerow({k: s.get(k, "") for k in keys})

    bt = by_type_tables(runs)
    if bt:
        (RESULTS / "by_type_table.md").write_text("# 分题型结果\n" + bt, encoding="utf-8")
        print(f"\n分题型表已写入 results/by_type_table.md（{len([s for s in runs if s.get('by_type')])} 个实验有生成指标）")
    print(f"\n已写入 results/main_table.md / main_table.csv（{len(runs)} 个实验）")


if __name__ == "__main__":
    main()
