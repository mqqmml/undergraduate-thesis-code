"""文档切分：Baseline 使用固定参数切分（chunk_size / chunk_overlap 写死在配置里）。

产物：
- 切分后的 Document 列表（含 chunk_id / doc_id / source / char_start 元信息）
- 可选落盘 data/processed/chunks.jsonl，方便人工检查切分质量
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import PROJECT_ROOT


def split_documents(
    docs: List[Document],
    size: int = 512,
    overlap: int = 50,
    splitter: str = "recursive",
) -> List[Document]:
    """固定参数切分。chunk_id 形如 01-网络体系结构.md#c0003。"""
    if splitter != "recursive":
        raise ValueError(f"Baseline 只实现 recursive 切分，收到：{splitter}")

    sp = RecursiveCharacterTextSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", "。", "；", " ", ""],
        add_start_index=True,  # 记录每块在原文档中的起始位置，便于溯源
    )

    chunks: List[Document] = []
    for doc in docs:
        doc_id = doc.metadata.get("doc_id", "unknown")
        for i, c in enumerate(sp.split_documents([doc])):
            c.metadata["chunk_id"] = f"{doc_id}#c{i:04d}"
            c.metadata["chunk_index"] = i
            chunks.append(c)

    print(f"[chunk] chunk_size={size} overlap={overlap} -> 共 {len(chunks)} 个 chunk")
    return chunks


def dump_chunks(chunks: List[Document], path: str | Path = "data/processed/chunks.jsonl") -> Path:
    """把切分结果落盘，便于检查/复现。"""
    out = PROJECT_ROOT / path
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(
                json.dumps(
                    {
                        "chunk_id": c.metadata.get("chunk_id"),
                        "doc_id": c.metadata.get("doc_id"),
                        "char_start": c.metadata.get("start_index"),
                        "length": len(c.page_content),
                        "text": c.page_content,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    print(f"[chunk] 切分明细已写入 {out}")
    return out
