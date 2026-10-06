"""生成：朴素 RAG —— 把检索到的 top-k 片段拼进固定 prompt，交给本地 Ollama 生成。

对应 agentic_rag 的 llm/ollama_llm.py，区别是 temperature=0（可复现）且 prompt 写进配置。
"""

from __future__ import annotations

from typing import Any, Dict

from langchain_ollama import ChatOllama

from src.config import load_config, model_name
from src.retrieve import retrieve

_llm = None


def _get_llm(cfg: Dict[str, Any]):
    """单例 LLM，temperature 取配置（Baseline 固定为 0，保证可复现）。"""
    global _llm
    if _llm is None:
        name = model_name("llm", cfg)
        print(f"[generate] llm model = {name}, temperature = {cfg['generate'].get('temperature', 0)}")
        _llm = ChatOllama(model=name, temperature=cfg["generate"].get("temperature", 0))
    return _llm


def build_prompt(question: str, hits: list[dict], cfg: Dict[str, Any]) -> str:
    """按配置里的模板拼 prompt。"""
    max_chunks = cfg["generate"].get("max_context_chunks", len(hits))
    context = "\n\n".join(f"[片段{i}] {h['text']}" for i, h in enumerate(hits[:max_chunks], start=1))
    template = cfg["generate"]["prompt"]
    return template.format(context=context, question=question)


def answer(question: str, cfg: Dict[str, Any] | None = None) -> dict:
    """朴素 RAG 完整链路：检索 -> 拼 prompt -> 生成。返回答案与检索结果。"""
    cfg = cfg or load_config()
    hits = retrieve(question, k=cfg["retrieve"]["top_k"], cfg=cfg)
    prompt = build_prompt(question, hits, cfg)
    resp = _get_llm(cfg).invoke(prompt)
    text = resp.content if isinstance(resp.content, str) else str(resp.content)
    return {"question": question, "answer": text.strip(), "hits": hits, "prompt": prompt}


if __name__ == "__main__":
    cfg = load_config()
    out = answer("TCP 三次握手的作用是什么", cfg)
    print(out["answer"])
    print("\n引用片段：")
    for h in out["hits"]:
        print(f"  [{h['rank']}] {h['chunk_id']} 距离={h['score']:.4f}")
