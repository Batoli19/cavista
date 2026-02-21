from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

_KB_PATH = Path(__file__).resolve().parent.parent / "data" / "knowledge_notes.json"


def _load_notes() -> List[Dict[str, Any]]:
    if not _KB_PATH.exists():
        return []
    try:
        data = json.loads(_KB_PATH.read_text(encoding="utf-8") or "[]")
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def _save_notes(notes: List[Dict[str, Any]]) -> None:
    _KB_PATH.parent.mkdir(parents=True, exist_ok=True)
    _KB_PATH.write_text(json.dumps(notes, indent=2), encoding="utf-8")


def index_project(project: Dict[str, Any]) -> bool:
    """
    Placeholder knowledge indexing hook.
    Returns True so callers can safely treat indexing as successful.
    """
    return bool(project)


def search_knowledge(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Placeholder knowledge search hook.
    Returns an empty result set when no vector/RAG backend is configured.
    """
    query = (query or "").strip().lower()
    if not query:
        return []
    notes = _load_notes()
    ranked: List[Dict[str, Any]] = []
    for note in notes:
        haystack = " ".join(
            [
                str(note.get("source", "")),
                str(note.get("title", "")),
                str(note.get("summary", "")),
                str(note.get("insights", "")),
            ]
        ).lower()
        if query in haystack:
            ranked.append(note)
    return ranked[: max(1, int(limit))]


def add_learning_note(note: Dict[str, Any]) -> Dict[str, Any]:
    notes = _load_notes()
    notes.append(note)
    _save_notes(notes)
    return note
