"""评测脚本 v2.0：逐题跑 Baseline，输出逐题明细 + 汇总指标 + 失败类型分布。

用法：
    python -m src.evaluate              # 检索 + 生成 + 指标（完整）
    python -m src.evaluate --no-gen     # 只评检索指标（不调 LLM，秒级）
    python -m src.evaluate --limit 20   # 先拿 20 题试跑

输出：
    results/<实验名>/per_question.csv   逐题：检索命中、各指标、生成答案、失败类型
    results/<实验名>/summary.json       汇总指标 + 失败类型分布（论文表格直接抄这个）
    results/<实验名>/retrieval_log.jsonl 完整检索结果（含每个 chunk 的距离与排名）
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, List

from tqdm import tqdm

from src.config import load_config, out_dir, resolve
from src.metrics import (
    aggregate,
    citation_rate,
    classify_failure,
    hit_rate_at_k,
    keypoint_coverage,
    mrr,
    recall_at_k,
)
from src.retrieve import retrieve


def load_questions(path: str | Path) -> List[dict]:
    """读取评测集（jsonl，一行一题）。"""
    p = resolve(path)
    if not p.exists():
        raise FileNotFoundError(f"评测集不存在：{p}")
    rows: List[dict] = []
    with open(p, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            item = json.loads(line)
            item.setdefault("id", f"q{i:03d}")
            item.setdefault("gold_evidence", [])
            item.setdefault("gold_chunks", [])
            item.setdefault("key_points", [])
            item.setdefault("type", "未标注")
            rows.append(item)
    print(f"[evaluate] 载入评测题 {len(rows)} 道：{p}")
    return rows


def _build_gold(question: dict) -> dict:
    """组装 gold 对象：优先 chunk_id，其次 evidence 字符串。"""
    return {
        "chunks": question.get("gold_chunks") or [],
        "evidences": question.get("gold_evidence") or [],
    }


def evaluate(cfg: Dict[str, Any], with_gen: bool = True, limit: int | None = None) -> Dict[str, Any]:
    questions = load_questions(cfg["eval"]["questions"])
    if limit:
        questions = questions[:limit]

    k_values = sorted(set(cfg["eval"].get("k_values", [])) | {cfg["retrieve"]["top_k"]})
    max_k = max(k_values)
    min_len = cfg["eval"].get("min_evidence_len", 8)
    kpc_threshold = cfg["eval"].get("kpc_threshold", 0.5)
    use_faithfulness = cfg["eval"].get("faithfulness", False) and with_gen
    result_dir = out_dir(cfg)
    retrieval_log_path = result_dir / "retrieval_log.jsonl"

    if use_faithfulness:
        print("[evaluate] 启用 Faithfulness（LLM 裁判），每题会额外调一次裁判模型")

    rows: List[Dict[str, Any]] = []
    t0 = time.time()

    with open(retrieval_log_path, "w", encoding="utf-8") as log_f:
        for q in tqdm(questions, desc="评测中", ncols=80):
            # 一次取到 max_k，够算所有 @k 指标
            hits = retrieve(q["question"], k=max_k, cfg=cfg)
            gold = _build_gold(q)
            log_f.write(
                json.dumps(
                    {
                        "id": q["id"],
                        "question": q["question"],
                        "gold_chunks": gold["chunks"],
                        "hits": [
                            {k: h[k] for k in ("rank", "chunk_id", "doc_id", "score")}
                            for h in hits
                        ],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

            row: Dict[str, Any] = {
                "id": q["id"],
                "type": q["type"],
                "question": q["question"],
                "gold_answer": q.get("gold_answer", ""),
                "gold_chunks": " || ".join(gold["chunks"]),
                "gold_evidence": " || ".join(gold["evidences"]),
                "top1_chunk": hits[0]["chunk_id"] if hits else "",
                "top1_score": round(hits[0]["score"], 4) if hits else "",
            }
            for k in k_values:
                row[f"hit@{k}"] = hit_rate_at_k(hits, gold, k, min_len)
                row[f"recall@{k}"] = recall_at_k(hits, gold, k, min_len)
            row["mrr"] = mrr(hits, gold, min_len)

            if with_gen:
                # 延迟导入：--no-gen 模式不需要 langchain_ollama
                from src.generate import answer as gen_answer
                from src.judge import faithfulness

                out = gen_answer(q["question"], cfg)
                row["answer"] = out["answer"]
                row["keypoint_coverage"] = round(
                    keypoint_coverage(out["answer"], q["key_points"], kpc_threshold), 4
                )
                row["citation_rate"] = citation_rate(out["answer"])
                row["failure_type"] = classify_failure(
                    hits, gold, out["answer"], q["key_points"],
                    cfg["retrieve"]["top_k"], min_len, kpc_threshold,
                )
                if use_faithfulness:
                    contexts = [h["text"] for h in out["hits"][: cfg["retrieve"]["top_k"]]]
                    row["faithfulness"] = round(faithfulness(out["answer"], contexts, cfg), 4)
            else:
                hr = hit_rate_at_k(hits, gold, cfg["retrieve"]["top_k"], min_len)
                row["answer"] = ""
                row["keypoint_coverage"] = float("nan")
                row["citation_rate"] = float("nan")
                row["faithfulness"] = float("nan")
                # 不做生成时只能判断检索阶段是否命中
                row["failure_type"] = "ok" if hr else "retrieval_miss"

            rows.append(row)

    elapsed = time.time() - t0

    # ---- 落盘 ----
    csv_path = result_dir / "per_question.csv"
    fieldnames = list(rows[0].keys()) if rows else []
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    summary = aggregate(rows, k_values)
    summary.update(
        {
            "experiment": cfg["_config_name"],
            "config": cfg.get("_config_path"),
            "chunk_size": cfg["chunk"]["size"],
            "chunk_overlap": cfg["chunk"]["overlap"],
            "retrieve_mode": cfg["retrieve"]["mode"],
            "top_k": cfg["retrieve"]["top_k"],
            "embedding_model": cfg["embedding"]["model"],
            "llm_model": cfg["generate"]["model"] if with_gen else None,
            "with_generation": with_gen,
            "with_faithfulness": use_faithfulness,
            "elapsed_sec": round(elapsed, 1),
        }
    )

    # 简单数据集指纹
    questions_path = resolve(cfg["eval"]["questions"])
    summary["questions_path"] = str(questions_path)
    summary["questions_sha256"] = hashlib.sha256(questions_path.read_bytes()).hexdigest()[:16]

    with open(result_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n================ Baseline 评测结果 ================")
    for k, v in summary.items():
        if k.startswith(("HitRate", "Recall")) or k in ("MRR", "KeyPointCoverage", "Faithfulness", "CitationRate", "n_questions"):
            print(f"  {k:<20} {v}")
    print(f"  失败类型分布          {summary.get('failure_distribution')}")
    print(f"  耗时                  {summary['elapsed_sec']}s")
    print(f"  明细                  {csv_path}")
    print(f"  汇总                  {result_dir / 'summary.json'}")
    print("==================================================\n")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="朴素 RAG Baseline 评测 v2.0")
    parser.add_argument("--config", default=None, help="配置文件路径，默认 configs/baseline.yaml")
    parser.add_argument("--no-gen", action="store_true", help="只评检索指标，不调用 LLM")
    parser.add_argument("--limit", type=int, default=None, help="只评前 N 题（调试用）")
    args = parser.parse_args()

    cfg = load_config(args.config)
    evaluate(cfg, with_gen=not args.no_gen, limit=args.limit)


if __name__ == "__main__":
    main()
