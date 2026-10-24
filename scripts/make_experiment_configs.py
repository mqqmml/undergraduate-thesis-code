"""从 baseline_v2.yaml 派生 E1/E2 实验配置（改配置即实验，结果目录与 name 同名）。

用法：
    python scripts/make_experiment_configs.py

生成（已存在则覆盖）：
    configs/e1-dense.yaml / e1-bm25.yaml / e1-hybrid.yaml
    configs/e1-dense-rerank.yaml / e1-hybrid-rerank.yaml
    configs/e2-chunk256.yaml / e2-chunk1024.yaml
    configs/e2-topk3.yaml / e2-topk10.yaml
    configs/e2-embed-bge-m3.yaml

说明：
- 所有变体只改一个维度，其余与 baseline_v2 完全一致（受控变量）。
- chunk 变体使用独立索引目录，需先建索引；gold_chunks 需用 scripts/remap_gold.py 重映射。
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "configs" / "baseline_v2.yaml"


def sub_once(text: str, pattern: str, repl: str) -> str:
    new, n = re.subn(pattern, repl, text, count=1, flags=re.M)
    if n != 1:
        raise ValueError(f"配置替换失败：{pattern}")
    return new


def make(name: str, desc: str, edits: list[tuple[str, str]], base: Path | None = None) -> None:
    text = (base or BASE).read_text(encoding="utf-8")
    text = sub_once(text, r"^name: .*$", f"name: {name}")
    text = sub_once(text, r"^description: .*$", f"description: {desc}")
    for pattern, repl in edits:
        text = sub_once(text, pattern, repl)
    out = ROOT / "configs" / f"{name}.yaml"
    out.write_text(text, encoding="utf-8")
    print(f"  -> {out.name}")


TOPK_EDITS = lambda k: [  # noqa: E731
    (r"^  top_k: \d+.*$", f"  top_k: {k}"),
    (r"^  max_context_chunks: \d+.*$", f"  max_context_chunks: {k}"),
]

# chunk 变体必须带 gold_map，否则 gold_chunks 仍是 512 配置的 id，与目标索引错配
GOLD_MAP = lambda tag: [  # noqa: E731
    (
        r"^  kpc_threshold: .*$",
        "  kpc_threshold: 0.5               # KeyPointCoverage 放宽判定阈值（token 重叠 >= 0.5 视为覆盖）\n"
        f"  gold_map: data/eval/gold_chunks_{tag}.json   # chunk 变体：gold 按字符区间重映射",
    )
]


def main() -> None:
    print("[configs] 生成 E1 检索方案对比配置")
    make("e1-dense", "E1：稠密检索（Baseline 同款，作为对照）", [])

    make(
        "e1-bm25",
        "E1：BM25 稀疏检索（jieba 分词）",
        [(r"^  mode: .*$", "  mode: bm25")],
    )

    make(
        "e1-hybrid",
        "E1：稠密 + BM25 混合检索（RRF 融合，k=60）",
        [
            (r"^  mode: .*$", "  mode: hybrid"),
            (r"^  top_k: \d+.*$", "  top_k: 5\n  hybrid_depth: 50        # 每路各取 50 候选再做 RRF\n  rrf_k: 60               # RRF 平滑常数"),
        ],
    )

    make(
        "e1-dense-rerank",
        "E1：稠密召回 50 + 交叉编码器重排取 5",
        [
            (r"^  top_k: \d+.*$", "  top_k: 5\n  candidate_depth: 50     # 召回深度，重排池\n  rerank:\n    enabled: true\n    model: BAAI/bge-reranker-base\n    depth: 50"),
        ],
    )

    make(
        "e1-hybrid-rerank",
        "E1：混合检索（RRF）+ 交叉编码器重排取 5",
        [
            (r"^  mode: .*$", "  mode: hybrid"),
            (r"^  top_k: \d+.*$", "  top_k: 5\n  hybrid_depth: 50\n  rrf_k: 60\n  rerank:\n    enabled: true\n    model: BAAI/bge-reranker-base\n    depth: 50"),
        ],
    )

    print("[configs] 生成 E2 参数实验配置")
    make(
        "e2-chunk256",
        "E2：chunk_size=256（其余同 baseline）",
        [
            (r"^  size: \d+.*$", "  size: 256"),
            (r"^  persist_dir: .*$", "  persist_dir: index/baseline_c256"),
        ] + GOLD_MAP("c256"),
    )
    make(
        "e2-chunk1024",
        "E2：chunk_size=1024（其余同 baseline）",
        [
            (r"^  size: \d+.*$", "  size: 1024"),
            (r"^  persist_dir: .*$", "  persist_dir: index/baseline_c1024"),
        ] + GOLD_MAP("c1024"),
    )
    for k in (3, 10):
        make(f"e2-topk{k}", f"E2：top_k={k}（检索不变，只改生成上下文）", TOPK_EDITS(k))

    make(
        "e2-embed-bge-m3",
        "E2：embedding 换 bge-m3（需重建索引）",
        [
            (r"^  model: nomic-embed-text.*$", "  model: bge-m3"),
            (r"^  persist_dir: .*$", "  persist_dir: index/baseline_bgem3"),
        ],
    )
    print("[configs] 生成 E3 重排配置（在最强召回方案上叠加 CrossEncoder）")
    RERANK = "\n  rerank:\n    enabled: true\n    model: BAAI/bge-reranker-base\n    depth: 50"
    make(
        "e3-bm25-1024-rerank",
        "E3：BM25（chunk=1024）召回 50 + 交叉编码器重排取 5",
        [
            (r"^  mode: .*$", "  mode: bm25"),
            (r"^  top_k: \d+.*$", "  top_k: 5\n  candidate_depth: 50" + RERANK),
        ],
        base=ROOT / "configs" / "e2-chunk1024.yaml",
    )
    make(
        "e3-bgem3-dense-rerank",
        "E3：bge-m3 稠密召回 50 + 交叉编码器重排取 5",
        [
            (r"^  top_k: \d+.*$", "  top_k: 5\n  candidate_depth: 50" + RERANK),
        ],
        base=ROOT / "configs" / "e2-embed-bge-m3.yaml",
    )
    make(
        "e3-bgem3-hybrid-rerank",
        "E3：bge-m3 稠密 + BM25 混合（RRF）召回 50 + 交叉编码器重排取 5",
        [
            (r"^  mode: .*$", "  mode: hybrid"),
            (r"^  top_k: \d+.*$", "  top_k: 5\n  hybrid_depth: 50\n  rrf_k: 60\n  candidate_depth: 50" + RERANK),
        ],
        base=ROOT / "configs" / "e2-embed-bge-m3.yaml",
    )
    print("[configs] 完成")


if __name__ == "__main__":
    main()
