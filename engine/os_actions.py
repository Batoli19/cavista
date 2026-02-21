from __future__ import annotations

import webbrowser


def open_url(url: str) -> str:
    target = (url or "").strip()
    if not target:
        return "No URL provided."
    if not target.startswith("http"):
        target = "https://" + target
    webbrowser.open(target)
    return f"Opened {target}"
