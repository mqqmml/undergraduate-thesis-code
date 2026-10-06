"""语料加载：把 data/raw 下的 .md / .txt / .pdf 读成 LangChain Document。

参考了 agentic_rag/utils/rag_index.py 的写法，区别是：
- 支持整个目录批量加载，而不是写死单个文件路径；
- 每个文档补上 doc_id / source 元信息，方便后续溯源与评测比对。
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader
from langchain_core.documents import Document

from src.config import PROJECT_ROOT


def _load_one(path: Path) -> List[Document]:
    """按后缀选择加载器。"""
    suffix = path.suffix.lower()
    if suffix == ".md":
        loader = UnstructuredMarkdownLoader(str(path))
    elif suffix == ".pdf":
        loader = PyPDFLoader(str(path))
    else:
        loader = TextLoader(str(path), encoding="utf-8")
    return loader.load()


def load_documents(raw_dir: str | Path, patterns: List[str] | None = None) -> List[Document]:
    """递归加载语料目录下的所有文档，返回 Document 列表。"""
    root = Path(raw_dir)
    if not root.is_absolute():
        root = PROJECT_ROOT / root
    if not root.exists():
        raise FileNotFoundError(f"语料目录不存在：{root}")

    patterns = patterns or ["*.md", "*.txt", "*.pdf"]
    files: List[Path] = []
    for pat in patterns:
        files.extend(sorted(root.rglob(pat)))

    if not files:
        raise FileNotFoundError(
            f"{root} 下没有找到任何语料（{patterns}）。请把教材/笔记放进该目录。"
        )

    docs: List[Document] = []
    for f in files:
        for d in _load_one(f):
            # doc_id 用相对路径，跨机器稳定
            rel = f.relative_to(root).as_posix()
            d.metadata["doc_id"] = rel
            d.metadata["source"] = rel
            d.metadata["file_name"] = f.name
            docs.append(d)

    print(f"[ingest] 加载 {len(files)} 个文件，得到 {len(docs)} 个文档对象")
    for f in files:
        print(f"         - {f.relative_to(root).as_posix()}")
    return docs
