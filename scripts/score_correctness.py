"""事后补齐 AnswerCorrectness：对已有生成结果的 per_question.csv 逐题判分。

不重跑生成，只调裁判模型，节省时间。

用法：
    python scripts/score_correctness.py results/baseline_v2
    python scripts/score_correctness.py results/e2-chunk1024-bm25 --limit 30

输出：
    results/<exp>/correctness.csv    逐题：answer_correctness + 理由
    results/<exp>/summary.json       追加 AnswerCorrectness / by_type.AnswerCorrectness（原地更新）
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tqdm import tqdm

from src.config import load_config
from src.judge import answer_correctness, reset_llm


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", help="结果目录，如 results/baseline_v2")
    ap.add_argument("--config", default="configs/baseline_v2.yaml", help="仅用于取裁判模型配置")
    ap.add_argument("--limit", type=int, default=None, help="只评前 N 题")
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    pq = run_dir / "per_question.csv"
    if not pq.exists():
        raise SystemExit(f"找不到 {pq}")

    cfg = load_config(args.config)
    reset_llm()

    with open(pq, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if args.limit:
        rows = rows[: args.limit]

    out_rows = []
    for r in tqdm(rows, desc=f"判分 {run_dir.name}", ncols=80):
        score = answer_correctness(
            r.get("question", ""), r.get("gold_answer", ""), r.get("answer", ""), cfg
        )
        out_rows.append(
            {
                "id": r.get("id", ""),
                "type": r.get("type", ""),
                "answer_correctness": score,
            }
        )

    out_csv = run_dir / "correctness.csv"
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "type", "answer_correctness"])
        w.writeheader()
        w.writerows(out_rows)

    def mean(xs):
        xs = [x for x in xs if x == x]  # 过滤 nan
        return sum(xs) / len(xs) if xs else float("nan")

    overall = mean([r["answer_correctness"] for r in out_rows])
    by_type: dict[str, list[float]] = {}
    for r in out_rows:
        by_type.setdefault(r["type"], []).append(r["answer_correctness"])

    summary_path = run_dir / "summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["AnswerCorrectness"] = round(overall, 4)
        for t, xs in summary.get("by_type", {}).items():
            if t in by_type:
                xs["AnswerCorrectness"] = round(mean(by_type[t]), 4)
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[score] summary.json 已更新：AnswerCorrectness={overall:.4f}")

    print(f"[score] 逐题明细 -> {out_csv}")
    print(f"[score] AnswerCorrectness = {overall:.4f}（n={len(out_rows)}）")
    for t, xs in by_type.items():
        print(f"  {t}: {mean(xs):.4f} (n={len(xs)})")


if __name__ == "__main__":
    main()
