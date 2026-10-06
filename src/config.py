"""配置加载：统一从 configs/*.yaml 读超参，从 .env 读模型名，代码里不写死路径。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# 项目根目录 = 本文件的上一级
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 加载 .env（不覆盖已存在的系统环境变量）
load_dotenv(PROJECT_ROOT / ".env")

DEFAULT_CONFIG = PROJECT_ROOT / "configs" / "baseline.yaml"


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """读取实验配置 yaml，返回 dict。"""
    cfg_path = Path(path) if path else DEFAULT_CONFIG
    if not cfg_path.is_absolute():
        cfg_path = PROJECT_ROOT / cfg_path
    if not cfg_path.exists():
        raise FileNotFoundError(f"配置文件不存在：{cfg_path}")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    cfg["_config_path"] = str(cfg_path)
    cfg["_config_name"] = cfg.get("name") or cfg_path.stem
    return cfg


def resolve(path: str | Path) -> Path:
    """把配置里的相对路径解析为项目内的绝对路径。"""
    p = Path(path)
    return p if p.is_absolute() else (PROJECT_ROOT / p)


def out_dir(cfg: dict[str, Any], sub: str | None = None) -> Path:
    """结果输出目录：results/<实验名>/[sub]，不存在则创建。"""
    base = resolve(cfg.get("output", {}).get("dir", "results")) / cfg["_config_name"]
    if sub:
        base = base / sub
    base.mkdir(parents=True, exist_ok=True)
    return base


def env(key: str, default: str | None = None) -> str | None:
    return os.getenv(key, default)


def model_name(kind: str, cfg: dict[str, Any] | None = None) -> str:
    """模型名优先取 .env，其次取配置 yaml。kind: llm | embedding"""
    if kind in ("llm", "generate"):
        fallback = (cfg or {}).get("generate", {}).get("model", "qwen3:4b")
        return env("OLLAMA_LLM", fallback) or fallback
    fallback = (cfg or {}).get("embedding", {}).get("model", "nomic-embed-text")
    return env("OLLAMA_EMBEDDING", fallback) or fallback
