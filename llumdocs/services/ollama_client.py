from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List

import requests

from llumdocs.settings import get_ollama_base


@lru_cache(maxsize=1)
def _base() -> str:
    return get_ollama_base()


def health(timeout: float = 3.0) -> None:
    """Lightweight health probe against the Ollama server."""
    r = requests.get(f"{_base()}/api/tags", timeout=timeout)
    r.raise_for_status()


def chat(model: str, messages: List[Dict[str, Any]], **kwargs: Any) -> Dict[str, Any]:
    """
    Direct chat call to Ollama.

    Prefer using LiteLLM (`llumdocs.llm`) where possible; this is mainly for
    diagnostics or specialised flows that need raw Ollama access.
    """
    payload: Dict[str, Any] = {"model": model, "messages": messages, **kwargs}
    r = requests.post(
        f"{_base()}/api/chat",
        json=payload,
        timeout=float(kwargs.get("timeout", 60)),
    )
    r.raise_for_status()
    return r.json()


def generate(model: str, prompt: str, **kwargs: Any) -> Dict[str, Any]:
    """Direct generate call to Ollama."""
    payload: Dict[str, Any] = {"model": model, "prompt": prompt, **kwargs}
    r = requests.post(
        f"{_base()}/api/generate",
        json=payload,
        timeout=float(kwargs.get("timeout", 60)),
    )
    r.raise_for_status()
    return r.json()
