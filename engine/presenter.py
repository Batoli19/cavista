from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

DEFAULT_VERBOSITY = "quick"
ALLOWED_VERBOSITY = {"quick", "standard", "detailed"}

_BANNED_TONE = [
    r"\bhuman\b",
    r"\bas jarvis\b",
    r"\bdoctor diagnosis\b",
    r"\bexcellent task\b",
]


@dataclass
class ResponseContract:
    say_text: str
    show_text: str
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    files: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, str]] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def get_verbosity() -> str:
    configured = (os.getenv("ASSISTANT_VERBOSITY", DEFAULT_VERBOSITY) or "").strip().lower()
    if configured in ALLOWED_VERBOSITY:
        return configured
    return DEFAULT_VERBOSITY


def _clean_tone(text: str) -> str:
    clean = (text or "").strip()
    for pattern in _BANNED_TONE:
        clean = re.sub(pattern, "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def _sentence_limit_for_verbosity(level: str) -> int:
    if level == "detailed":
        return 8
    if level == "standard":
        return 5
    return 3


def _limit_sentences(text: str, max_sentences: int) -> str:
    clean = re.sub(r"\s+", " ", (text or "")).strip()
    if not clean:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", clean)
    return " ".join(parts[:max_sentences]).strip()


def sanitize_for_tts(text: str, source_count: int = 0) -> str:
    clean = (text or "").strip()
    clean = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1", clean)  # markdown links
    clean = re.sub(r"https?://\S+", "", clean)
    clean = re.sub(r"\b[a-f0-9]{8,}\b", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"[{}[\]]", "", clean)
    clean = re.sub(r"\s+", " ", clean).strip(" ,.-")
    clean = _limit_sentences(clean, 2)
    if source_count > 0 and "source" not in clean.lower():
        clean = f"{clean}. I attached {source_count} sources."
    return clean or "Done."


def _render_sources(sources: List[Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    for source in sources:
        title = source.get("title", "Source")
        domain = source.get("domain", "")
        note = source.get("note", "reference")
        lines.append(f"- {title} — {domain} (used for: {note})")
    return lines


def make_response(
    summary: str,
    *,
    bullets: List[str] | None = None,
    sections: List[Dict[str, Any]] | None = None,
    sources: List[Dict[str, Any]] | None = None,
    evidence: List[Dict[str, Any]] | None = None,
    files: List[Dict[str, Any]] | None = None,
    actions: List[Dict[str, str]] | None = None,
    intent: str = "general",
    verbosity: str | None = None,
    say_text: str | None = None,
    question: str | None = None,
    debug: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    v = verbosity if verbosity in ALLOWED_VERBOSITY else get_verbosity()
    sentence_limit = _sentence_limit_for_verbosity(v)

    top_line = _clean_tone(_limit_sentences(summary, sentence_limit))
    body: List[str] = [top_line] if top_line else []

    bullet_lines = [_clean_tone(b) for b in (bullets or []) if b and b.strip()]
    bullet_cap = 2 if v == "quick" else 4 if v == "standard" else 5
    if bullet_lines:
        body.extend([f"- {b}" for b in bullet_lines[:bullet_cap]])

    for section in (sections or []):
        title = (section.get("title") or "").strip()
        items = [str(i).strip() for i in section.get("items", []) if str(i).strip()]
        if not title or not items:
            continue
        body.append("")
        body.append(f"**{title}**")
        max_items = 2 if v == "quick" else 3 if v == "standard" else 5
        body.extend([f"- {item}" for item in items[:max_items]])

    rendered_sources = _render_sources(sources or [])
    if rendered_sources:
        body.append("")
        body.append("**What I found**")
        body.extend(rendered_sources[: (3 if v == "quick" else 5)])
        body.append("- Source links are attached below.")

    if question:
        q = question.strip()
        if q and not q.endswith("?"):
            q += "?"
        body.append("")
        body.append(q)

    show_text = "\n".join([line for line in body if line is not None]).strip()
    spoken = sanitize_for_tts(say_text or summary or show_text, source_count=len(sources or []))

    evidence_items = list(evidence or [])
    for src in (sources or []):
        if src.get("url"):
            evidence_items.append(
                {
                    "type": "link",
                    "title": src.get("title", "Source"),
                    "caption": src.get("note", ""),
                    "url": src.get("url"),
                    "path": None,
                    "data": None,
                    "source": src.get("domain"),
                }
            )

    resp = ResponseContract(
        say_text=spoken,
        show_text=show_text,
        evidence=evidence_items,
        files=files or [],
        actions=actions or [],
        meta={
            "intent": intent,
            "verbosity": v,
            "sources": sources or [],
            "debug": debug or {},
        },
    )
    return resp.to_dict()


def wrap_response(result: Any, *, intent: str = "general") -> Dict[str, Any]:
    """
    Backward compatibility wrapper:
    - String => ResponseContract
    - Existing contract-like dict => normalized contract keys
    - Legacy dict(reply/attachments) => converted
    """
    if isinstance(result, dict) and {"say_text", "show_text", "evidence", "files", "actions", "meta"}.issubset(
        result.keys()
    ):
        return result

    if isinstance(result, dict):
        if {"say_text", "show_text", "evidence"}.issubset(result.keys()):
            return {
                "say_text": result.get("say_text", ""),
                "show_text": result.get("show_text", ""),
                "evidence": result.get("evidence", []),
                "files": result.get("files", []),
                "actions": result.get("actions", []),
                "meta": result.get("meta", {"intent": intent, "verbosity": get_verbosity(), "sources": [], "debug": {}}),
            }
        legacy_reply = str(result.get("reply", ""))
        legacy_attachments = result.get("attachments", [])
        evidence = []
        for att in legacy_attachments:
            if isinstance(att, dict):
                evidence.append(
                    {
                        "type": "image",
                        "title": att.get("name", "Attachment"),
                        "caption": "",
                        "url": None,
                        "path": None,
                        "data": att.get("content"),
                        "source": None,
                    }
                )
        return make_response(summary=legacy_reply or "Done.", evidence=evidence, intent=intent)

    return make_response(summary=str(result), intent=intent)
