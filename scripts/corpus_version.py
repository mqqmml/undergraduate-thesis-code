# -*- coding: utf-8 -*-
"""生成知识库版本指纹：语料 sha256、各切分配置块数、索引与模型信息。

产物：data/metadata/corpus_version.json + 追加到 corpus_manifest.md 的「版本信息」小节。
可见性：语料本身不入库（.gitignore），但指纹入库，保证可追溯与可复现。
"""
from __future__ import annotations

import hashlib
import json
import platform
from datetime import date
from pathlib import Path

from src.chunk import split_documents
from src.config import PROJECT_ROOT
from src.ingest import load_documents

RAW = PROJECT_ROOT / "data/raw"
OUT_JSON = PROJECT_ROOT / "data/metadata/corpus_version.json"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for buf in iter(lambda: f.read(1 << 20), b""):
            h.update(buf)
    return h.hexdigest()


def main() -> None:
    files = sorted(RAW.glob("*.md"))
    if not files:
        raise SystemExit("data/raw 下没有语料文件")

    per_file = []
    total_chars = 0
    for p in files:
        text = p.read_text(encoding="utf-8")
        total_chars += len(text)
        per_file.append({"file": p.name, "chars": len(text), "sha256": sha256_file(p)})

    # 语料集合级指纹：按文件名排序后串联各文件 sha256 再取哈希
    combo = hashlib.sha256()
    for item in per_file:
        combo.update(f"{item['file']}:{item['sha256']}\n".encode())
    corpus_sha = combo.hexdigest()

    # 各切分配置的块数（只切分，不建索引，秒级完成）
    docs = load_documents(RAW)
    chunk_stats = {}
    for size in (256, 512, 1024):
        chunks = split_documents(docs, size=size, overlap=50)
        lens = [len(c.page_content) for c in chunks]
        chunk_stats[str(size)] = {
            "n_chunks": len(chunks),
            "avg_len": round(sum(lens) / len(lens), 1),
            "min_len": min(lens),
            "max_len": max(lens),
        }

    info = {
        "kb_version": "v1.0",
        "frozen_date": "2026-10-03",
        "generated_at": str(date.today()),
        "corpus_sha256": corpus_sha,
        "n_files": len(per_file),
        "total_chars": total_chars,
        "files": per_file,
        "chunk_stats": chunk_stats,
        "embedding": {"baseline": "nomic-embed-text (768d)", "alternative": "bge-m3 (1024d)"},
        "index": {"type": "faiss IndexFlatIP", "persist_dir": "index/<config-name>"},
        "env": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "cpu_only": True,
        },
        "notes": "语料不入库；指纹入库，可用 scripts/corpus_version.py 复算校验。",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[version] KB {info['kb_version']} 文件 {len(per_file)} 个，{total_chars} 字符")
    print(f"[version] corpus_sha256 = {corpus_sha}")
    for size, st in chunk_stats.items():
        print(f"[version] chunk={size}: {st['n_chunks']} 块，均长 {st['avg_len']}")
    print(f"[version] 已写入 {OUT_JSON}")


if __name__ == "__main__":
    main()
