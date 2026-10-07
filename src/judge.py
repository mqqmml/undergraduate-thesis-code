"""LLM 裁判指标（RAGAS 风格）—— 用于 Faithfulness、Answer Relevance 等需模型判断的指标。

本地裁判：qwen3:4b（通过 Ollama）。由于 4B 模型稳定性有限，必须配合人工抽检校准，
报告 Cohen's kappa 后方可采信。
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Sequence

from langchain_ollama import ChatOllama

from src.config import load_config, model_name


_LLM: ChatOllama | None = None


def _get_llm(cfg: Dict[str, Any]) -> ChatOllama:
    """单例裁判模型。"""
    global _LLM
    if _LLM is None:
        name = model_name("llm", cfg)
        temp = cfg.get("judge", {}).get("temperature", 0)
        _LLM = ChatOllama(model=name, temperature=temp)
        print(f"[judge] 裁判模型 = {name}, temperature = {temp}")
    return _LLM


_FAITHFULNESS_PROMPT = """你是严格的内容审核员。请把下面的回答拆分成若干独立、最小的论断，并逐一判断每个论断是否能从提供的资料中直接推出。

资料：
{context}

回答：
{answer}

输出要求：
1. 只输出 JSON 数组，不要解释、不要 Markdown 代码块；
2. 每个元素格式：{{"claim": "论断原文", "verdict": "支持/不支持/无法判断"}}；
3. "支持"表示资料明确包含该论断；"不支持"表示资料明确 contradict 或没有依据；"无法判断"表示资料不完整。
"""


def _extract_json_array(text: str) -> List[dict]:
    """从可能带 Markdown 的文本中提取 JSON 数组。"""
    text = text.strip()
    # 先去 Markdown 代码块
    if text.startswith("```"):
        text = re.sub(r"^```[\w]*\n?|\n?```$", "", text).strip()
    # 找第一个 [ 和最后一个 ]
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("未找到 JSON 数组")
    return json.loads(text[start : end + 1])


def faithfulness_claims(answer: str, contexts: Sequence[str], cfg: Dict[str, Any]) -> List[dict]:
    """返回回答中每个论断的裁判结果。

    返回列表，每项含 claim / verdict，verdict ∈ {"支持", "不支持", "无法判断"}。
    """
    context = "\n\n".join(f"[片段{i+1}] {c}" for i, c in enumerate(contexts))
    prompt = _FAITHFULNESS_PROMPT.format(context=context, answer=answer)
    llm = _get_llm(cfg)
    resp = llm.invoke(prompt)
    text = resp.content if isinstance(resp.content, str) else str(resp.content)
    return _extract_json_array(text)


def faithfulness(answer: str, contexts: Sequence[str], cfg: Dict[str, Any]) -> float:
    """Faithfulness = 支持论断数 / 总论断数（无法判断不计入支持）。"""
    try:
        claims = faithfulness_claims(answer, contexts, cfg)
    except Exception as e:
        print(f"[judge] Faithfulness 解析失败: {e}")
        return float("nan")

    if not claims:
        return float("nan")

    supported = sum(1 for c in claims if c.get("verdict") == "支持")
    return supported / len(claims)


def reset_llm() -> None:
    """切换模型时重置单例。"""
    global _LLM
    _LLM = None
