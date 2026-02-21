from __future__ import annotations

import html
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from .ai_chat import chat_with_ai
from .knowledge_base import add_learning_note

_YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_URL_RE = re.compile(r"https?://[^\s]+")


def extract_youtube_video_id(text_or_url: str) -> Optional[str]:
    raw = (text_or_url or "").strip()
    if not raw:
        return None

    if _YOUTUBE_ID_RE.fullmatch(raw):
        return raw

    match = _URL_RE.search(raw)
    url = match.group(0) if match else raw
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower()

    if "youtu.be" in host:
        vid = parsed.path.strip("/").split("/")[0]
        return vid if _YOUTUBE_ID_RE.fullmatch(vid) else None

    if "youtube.com" in host:
        if parsed.path == "/watch":
            qs = urllib.parse.parse_qs(parsed.query)
            vid = (qs.get("v") or [None])[0]
            return vid if vid and _YOUTUBE_ID_RE.fullmatch(vid) else None
        if parsed.path.startswith("/shorts/") or parsed.path.startswith("/embed/"):
            vid = parsed.path.strip("/").split("/")[1]
            return vid if _YOUTUBE_ID_RE.fullmatch(vid) else None

    return None


def _safe_get_json(url: str, timeout: int = 10) -> Dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_video_title(video_url: str) -> str:
    try:
        endpoint = (
            "https://www.youtube.com/oembed?"
            + urllib.parse.urlencode({"url": video_url, "format": "json"})
        )
        data = _safe_get_json(endpoint)
        return str(data.get("title") or "YouTube video")
    except Exception:
        return "YouTube video"


def _fetch_caption_xml(video_id: str) -> Tuple[Optional[str], Optional[str]]:
    caption_variants = [
        {"lang": "en"},
        {"lang": "en", "kind": "asr"},
        {"lang": "en-US"},
        {"lang": "en-US", "kind": "asr"},
    ]
    for params in caption_variants:
        query = {"v": video_id, **params}
        url = "https://www.youtube.com/api/timedtext?" + urllib.parse.urlencode(query)
        try:
            with urllib.request.urlopen(url, timeout=12) as resp:
                xml_text = resp.read().decode("utf-8", errors="ignore")
                if "<text" in xml_text:
                    return xml_text, params.get("lang")
        except Exception:
            continue
    return None, None


def extract_transcript(video_id: str) -> str:
    xml_text, _lang = _fetch_caption_xml(video_id)
    if not xml_text:
        return ""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return ""

    parts = []
    for node in root.findall("text"):
        text = node.text or ""
        text = html.unescape(text).replace("\n", " ").strip()
        if text:
            parts.append(text)
    return " ".join(parts).strip()


def learn_from_youtube(video_url_or_text: str) -> Dict[str, Any]:
    video_id = extract_youtube_video_id(video_url_or_text)
    if not video_id:
        return {
            "ok": False,
            "message": "I couldn't find a valid YouTube URL/video ID. Try: learn from youtube https://www.youtube.com/watch?v=...",
        }

    canonical_url = f"https://www.youtube.com/watch?v={video_id}"
    title = get_video_title(canonical_url)
    transcript = extract_transcript(video_id)
    if not transcript:
        return {
            "ok": False,
            "message": "I couldn't extract captions from this video. It may have no public transcript.",
            "video_url": canonical_url,
        }

    clipped_transcript = transcript[:12000]
    prompt = (
        "You are extracting practical learning notes from a YouTube transcript.\n"
        "Return concise plain text with exactly these sections:\n"
        "1) Core Idea (2 lines)\n"
        "2) Key Lessons (3-6 bullets)\n"
        "3) Action Steps (3-5 bullets)\n"
        "4) One-Paragraph Summary\n\n"
        f"Video title: {title}\n"
        f"Transcript:\n{clipped_transcript}"
    )
    insights = chat_with_ai(prompt, files=[])

    note = {
        "source": "youtube",
        "video_id": video_id,
        "video_url": canonical_url,
        "title": title,
        "summary": insights[:1000],
        "insights": insights,
        "transcript_chars": len(transcript),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    add_learning_note(note)

    return {
        "ok": True,
        "video_url": canonical_url,
        "title": title,
        "transcript_chars": len(transcript),
        "insights": insights,
    }
