"""
AI Router: resilient routing across model providers.
"""

from __future__ import annotations

import time
from typing import Dict

from engine.ai_chat import chat_with_ai, _chat_with_gemini_text, _chat_with_groq

CACHE_TTL_SECONDS = 300
_ROUTER_CACHE: Dict[str, tuple[float, str]] = {}


def _cache_get(key: str) -> str | None:
    item = _ROUTER_CACHE.get(key)
    if not item:
        return None
    expires_at, value = item
    if expires_at < time.time():
        _ROUTER_CACHE.pop(key, None)
        return None
    return value


def _cache_set(key: str, value: str) -> None:
    _ROUTER_CACHE[key] = (time.time() + CACHE_TTL_SECONDS, value)


def _local_fallback(prompt: str) -> str:
    short = (prompt or "").strip()
    if len(short) > 120:
        short = short[:120] + "..."
    return (
        "I could not reach the main models right now.\n"
        f"- Request captured: {short or 'No text provided'}\n"
        "- Please try again shortly."
    )


def route_request(
    prompt: str,
    context: str = None,
    task_type: str = "fast",
    files: list = None,
) -> str:
    """
    Routing policy:
    - vision/files => chat_with_ai (vision pipeline)
    - planning/reasoning => Gemini text then Groq
    - fast/default => Groq then Gemini text
    - final fallback => local short response
    """
    files = files or []
    full_prompt = f"{context}\n\nUser Question: {prompt}" if context else prompt
    cache_key = f"{task_type}|{bool(files)}|{full_prompt}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    try:
        if task_type == "vision" or files:
            result = chat_with_ai(full_prompt, files)
            _cache_set(cache_key, result)
            return result

        if task_type in ("planning", "reasoning"):
            try:
                result = _chat_with_gemini_text(full_prompt)
                _cache_set(cache_key, result)
                return result
            except Exception:
                result = _chat_with_groq(full_prompt)
                _cache_set(cache_key, result)
                return result

        try:
            result = _chat_with_groq(full_prompt)
            _cache_set(cache_key, result)
            return result
        except Exception:
            result = _chat_with_gemini_text(full_prompt)
            _cache_set(cache_key, result)
            return result
    except Exception:
        result = _local_fallback(full_prompt)
        _cache_set(cache_key, result)
        return result


def ask_fast(prompt: str, context: str = None) -> str:
    return route_request(prompt, context=context, task_type="fast")


def ask_vision(prompt: str, files: list) -> str:
    return route_request(prompt, task_type="vision", files=files)


def ask_planner(prompt: str) -> str:
    return route_request(prompt, task_type="planning")
