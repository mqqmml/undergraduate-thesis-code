"""向量索引：把 chunk 用 Ollama 嵌入模型编码，构建 FAISS 索引并持久化。

对应 agentic_rag 的 utils/rag_index.py，差异：
- 路径全部来自配置，不写死开发机绝对路径；
- 额外导出一份 chunks.jsonl（chunk_id -> 文本），供检索评测做命中判定。
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from src.config import model_name, resolve


def get_embedding(cfg: Dict[str, Any]) -> OllamaEmbeddings:
    """嵌入模型：nomic-embed-text（与配置一致，换模型必须重建索引）。"""
    name = model_name("embedding", cfg)
    print(f"[index] embedding model = {name}")
    return OllamaEmbeddings(model=name)


def build_index(chunks: List[Document], cfg: Dict[str, Any]) -> Path:
    """构建并保存 FAISS 索引，返回索引目录。"""
    persist_dir = resolve(cfg["index"]["persist_dir"])
    if persist_dir.exists():
        shutil.rmtree(persist_dir)
        print(f"[index] 已清除旧索引 {persist_dir}")

    vectorstore = FAISS.from_documents(chunks, get_embedding(cfg))
    persist_dir.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(persist_dir))
    print(f"[index] FAISS 索引已保存：{persist_dir}（{len(chunks)} 个向量）")

    # 落一份 chunk 映射，评测时用来判定命中（避免每次重新切分）
    mapping_path = persist_dir / "chunks.jsonl"
    with open(mapping_path, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(
                json.dumps(
                    {
                        "chunk_id": c.metadata.get("chunk_id"),
                        "doc_id": c.metadata.get("doc_id"),
                        "char_start": c.metadata.get("start_index"),
                        "text": c.page_content,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    print(f"[index] chunk 映射已保存：{mapping_path}")
    return persist_dir


def load_index(cfg: Dict[str, Any]) -> FAISS:
    """加载已持久化的 FAISS 索引（单例由 retrieve 模块维护）。"""
    persist_dir = resolve(cfg["index"]["persist_dir"])
    if not persist_dir.exists():
        raise FileNotFoundError(f"索引不存在：{persist_dir}，请先运行 python -m src.index")
    return FAISS.load_local(
        str(persist_dir),
        get_embedding(cfg),
        allow_dangerous_deserialization=True,  # 本地自建索引，可安全反序列化
    )


def load_chunk_map(cfg: Dict[str, Any]) -> Dict[str, dict]:
    """读取 chunk_id -> {text, doc_id} 映射。"""
    path = resolve(cfg["index"]["persist_dir"]) / "chunks.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"chunk 映射不存在：{path}，请先运行 python -m src.index")
    mapping: Dict[str, dict] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                item = json.loads(line)
                mapping[item["chunk_id"]] = item
    return mapping


if __name__ == "__main__":
    """python -m src.index —— 全量重建 Baseline 索引"""
    import sys

    from src.chunk import dump_chunks, split_documents
    from src.config import load_config
    from src.ingest import load_documents

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    cfg = load_config()
    docs = load_documents(cfg["corpus"]["raw_dir"], cfg["corpus"].get("patterns"))
    chunks = split_documents(
        docs,
        size=cfg["chunk"]["size"],
        overlap=cfg["chunk"]["overlap"],
        splitter=cfg["chunk"].get("splitter", "recursive"),
    )
    dump_chunks(chunks)
    build_index(chunks, cfg)
