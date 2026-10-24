"""把 eval-v2.0 的 gold_chunks 从 512 配置重映射到任意 chunk 配置。

原理：按字符区间重叠，而不是按文本相似度。
- 每个 chunk 都记录了 doc_id + char_start + length（切分时 add_start_index）；
- 旧 gold chunk 覆盖区间 [s, s+len)，新配置下与之重叠的 chunk 即为候选 gold；
- 判定规则：新 chunk 有 >= ratio 的比例落在 gold 区间内（默认 0.5），
  确保"新 chunk 主要是这段证据"，而不是顺带沾到一点边；
- 若没有任何 chunk 满足（极端情况：gold 太短、新 chunk 太大），取覆盖 gold 中点的那一块兜底。

用法：
    python scripts/remap_gold.py --target index/baseline_c256/chunks.jsonl \
        --out data/eval/gold_chunks_c256.json
    python scripts/remap_gold.py --target index/baseline_c1024/chunks.jsonl \
        --out data/eval/gold_chunks_c1024.json
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
BASE_CHUNKS = ROOT / "index" / "baseline" / "chunks.jsonl"
QUESTIONS = ROOT / "data" / "eval" / "questions_v2.0.jsonl"


def load_chunks(path: Path) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            c = json.loads(line)
            c["length"] = c.get("length") or len(c["text"])
            out[c["chunk_id"]] = c
    return out


def span(c: dict) -> Tuple[int, int]:
    s = c.get("char_start") or 0
    return s, s + (c.get("length") or len(c["text"]))


def build_doc_index(chunks: Dict[str, dict]) -> Dict[str, List[Tuple[int, int, str]]]:
    """doc_id -> [(start, end, chunk_id)]，按 start 排序，便于区间扫描。"""
    by_doc: Dict[str, List[Tuple[int, int, str]]] = defaultdict(list)
    for cid, c in chunks.items():
        s, e = span(c)
        by_doc[c["doc_id"]].append((s, e, cid))
    for v in by_doc.values():
        v.sort()
    return by_doc


def map_question(gold_ids: List[str], base: Dict[str, dict],
                 target_by_doc: Dict[str, List[Tuple[int, int, str]]],
                 ratio: float = 0.5) -> List[str]:
    picked: List[str] = []
    for gid in gold_ids:
        g = base.get(gid)
        if not g:
            continue
        gs, ge = span(g)
        cands = target_by_doc.get(g["doc_id"], [])
        hits = []
        for ts, te, tid in cands:
            if te <= gs or ts >= ge:  # 不相交
                continue
            overlap = min(te, ge) - max(ts, gs)
            if overlap <= 0:
                continue
            tlen = te - ts
            # 新 chunk 的主体落在 gold 区间内
            if overlap / max(tlen, 1) >= ratio:
                hits.append(tid)
        if not hits:
            # 兜底：覆盖 gold 中点的那一块
            mid = (gs + ge) // 2
            for ts, te, tid in cands:
                if ts <= mid < te:
                    hits.append(tid)
                    break
        for h in hits:
            if h not in picked:
                picked.append(h)
    return picked


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True, help="目标配置的 chunks.jsonl")
    ap.add_argument("--out", required=True, help="输出 gold 映射 json")
    ap.add_argument("--ratio", type=float, default=0.5, help="新 chunk 落在 gold 区间内的最小比例")
    args = ap.parse_args()

    base = load_chunks(BASE_CHUNKS)
    target_path = ROOT / args.target if not Path(args.target).is_absolute() else Path(args.target)
    target = load_chunks(target_path)
    if not target:
        raise SystemExit(f"目标 chunk 为空：{target_path}")

    target_by_doc = build_doc_index(target)
    target_ids = set(target)

    questions = [json.loads(l) for l in open(QUESTIONS, encoding="utf-8") if l.strip()]
    mapping: Dict[str, List[str]] = {}
    empty, missing = 0, 0
    for q in questions:
        gold = q.get("gold_chunks") or []
        new_ids = map_question(gold, base, target_by_doc, args.ratio)
        # 过滤掉目标索引里不存在的 id
        new_ids = [c for c in new_ids if c in target_ids]
        if not new_ids:
            empty += 1
        mapping[q["id"]] = new_ids

    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(
            {
                "target_chunks": str(target_path.relative_to(ROOT) if target_path.is_relative_to(ROOT) else target_path),
                "ratio": args.ratio,
                "n_questions": len(questions),
                "n_target_chunks": len(target),
                "n_empty": empty,
                "mapping": mapping,
            },
            f,
            ensure_ascii=False,
            indent=1,
        )

    sizes = [len(v) for v in mapping.values()]
    print(f"[remap] 目标 {len(target)} 个 chunk，源 {len(base)} 个 chunk")
    print(f"[remap] {len(questions)} 题：映射后平均 {sum(sizes)/len(sizes):.2f} 个 gold chunk，"
          f"空映射 {empty} 题（{empty/len(questions):.1%}）")
    print(f"[remap] 已写入 {out}")


if __name__ == "__main__":
    main()
