from __future__ import annotations

import base64
import json
import mimetypes
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List


def _http_get_json(url: str, timeout: int = 15) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (ProjectForge Research Bot)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_get_bytes(url: str, timeout: int = 20, max_bytes: int = 2_500_000) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (ProjectForge Research Bot)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        content_type = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        body = resp.read(max_bytes)
    return body, content_type


def _clean_text(text: str, limit: int = 700) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()[:limit]


def _extract_domain(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.lower()
    except Exception:
        return ""


def _search_commons_image(title: str) -> str:
    # Disabled for proof policy: commons fallback introduces too many unrelated logos.
    return ""


def _resolve_image_url(page: Dict[str, Any]) -> str:
    image_url = page.get("thumbnail", {}).get("source", "")
    if image_url:
        return image_url
    try:
        title = page.get("title", "")
        if title:
            summary_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(title)
            summary_payload = _http_get_json(summary_url)
            image_url = (
                summary_payload.get("thumbnail", {}).get("source", "")
                or summary_payload.get("originalimage", {}).get("source", "")
            )
    except Exception:
        image_url = ""
    return image_url


def _is_relevant_visual(title: str, image_url: str, summary: str) -> bool:
    t = f"{title} {image_url} {summary}".lower()
    reject = ["logo", "icon", "wordmark", "seal", "symbol"]
    if any(r in t for r in reject):
        return False
    allow = [
        "chart",
        "graph",
        "trend",
        "rate",
        "statistics",
        "report",
        "clinical",
        "outcome",
        "comparison",
        "timeline",
        "breakdown",
    ]
    return any(a in t for a in allow)


def _image_to_evidence(title: str, image_url: str, source_url: str, summary: str) -> Dict[str, Any] | None:
    if not image_url:
        return None
    if not _is_relevant_visual(title, image_url, summary):
        return None
    try:
        body, content_type = _http_get_bytes(image_url)
        if not body:
            return None
        if not content_type:
            content_type = mimetypes.guess_type(image_url)[0] or "application/octet-stream"
        if not content_type.startswith("image/"):
            return None
        return {
            "type": "image",
            "title": title,
            "caption": f"Relevant research visual for {title}",
            "url": image_url,
            "path": None,
            "data": base64.b64encode(body).decode("ascii"),
            "source": source_url or None,
            "mime_type": content_type,
        }
    except Exception:
        return None


def research_topic_with_wikipedia(topic: str, limit: int = 4, request_evidence: bool = False) -> Dict[str, Any]:
    """
    Structured research output:
    {
      "summary": str,
      "sources": [{"title","url","domain","note"}],
      "evidence": [{"type":"image", ...}],
      "raw": [{"title","summary","source_url","image_url"}]
    }
    """
    topic = (topic or "").strip()
    if not topic:
        return {
            "summary": "",
            "sources": [],
            "evidence": [],
            "raw": [],
            "meta": {"reason": "empty_query", "needs_clarification": True, "no_reliable_visuals": bool(request_evidence)},
        }

    search_url = (
        "https://en.wikipedia.org/w/api.php?"
        + urllib.parse.urlencode(
            {
                "action": "query",
                "list": "search",
                "format": "json",
                "srlimit": max(1, min(limit, 8)),
                "srsearch": topic,
            }
        )
    )
    reason = ""
    try:
        search_payload = _http_get_json(search_url)
    except Exception:
        return {
            "summary": "",
            "sources": [],
            "evidence": [],
            "raw": [],
            "meta": {"reason": "provider_failure", "needs_clarification": True, "no_reliable_visuals": bool(request_evidence)},
        }

    hits = search_payload.get("query", {}).get("search", [])
    pageids = [str(item.get("pageid")) for item in hits if item.get("pageid")]
    if not pageids:
        return {
            "summary": "",
            "sources": [],
            "evidence": [],
            "raw": [],
            "meta": {"reason": "unclear_query", "needs_clarification": True, "no_reliable_visuals": bool(request_evidence)},
        }

    details_url = (
        "https://en.wikipedia.org/w/api.php?"
        + urllib.parse.urlencode(
            {
                "action": "query",
                "format": "json",
                "prop": "extracts|pageimages|info",
                "inprop": "url",
                "exintro": 1,
                "explaintext": 1,
                "pithumbsize": 900,
                "pageids": "|".join(pageids),
            }
        )
    )
    try:
        details_payload = _http_get_json(details_url)
    except Exception:
        return {
            "summary": "",
            "sources": [],
            "evidence": [],
            "raw": [],
            "meta": {"reason": "provider_failure", "needs_clarification": True, "no_reliable_visuals": bool(request_evidence)},
        }

    pages = details_payload.get("query", {}).get("pages", {})
    raw_rows: List[Dict[str, Any]] = []
    sources: List[Dict[str, Any]] = []
    visuals: List[Dict[str, Any]] = []

    for pageid in pageids:
        page = pages.get(pageid, {})
        if not page:
            continue
        title = page.get("title", "Unknown")
        source_url = page.get("fullurl", "")
        summary = _clean_text(page.get("extract", ""))
        image_url = _resolve_image_url(page)

        raw_rows.append(
            {
                "title": title,
                "summary": summary,
                "source_url": source_url,
                "image_url": image_url,
            }
        )

        sources.append(
            {
                "title": title,
                "url": source_url,
                "domain": _extract_domain(source_url) or "wikipedia.org",
                "note": "overview",
            }
        )

        if len(visuals) < 3:
            ev = _image_to_evidence(title, image_url, source_url, summary)
            if ev:
                visuals.append(ev)

    overall_summary = ""
    if raw_rows:
        snippets = [row["summary"] for row in raw_rows if row.get("summary")]
        overall_summary = _clean_text(" ".join(snippets), limit=500)

    if len(sources) < 3 and not reason:
        reason = "insufficient_sources"

    no_reliable_visuals = bool(request_evidence and len(visuals) == 0)
    if no_reliable_visuals and not reason:
        reason = "no_reliable_visuals"

    return {
        "summary": overall_summary,
        "sources": sources,
        "evidence": visuals,
        "raw": raw_rows,
        "meta": {
            "reason": reason or "ok",
            "needs_clarification": (len(sources) < 3),
            "no_reliable_visuals": no_reliable_visuals,
        },
    }
