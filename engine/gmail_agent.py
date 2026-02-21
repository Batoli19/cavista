from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Dict

from engine.ai_chat import chat_with_ai


class GmailSetupRequired(Exception):
    pass


SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
ROOT = Path(__file__).resolve().parent.parent
CREDENTIALS_PATH = ROOT / "credentials.json"
TOKEN_PATH = ROOT / "token.json"


def _build_service():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except Exception as e:
        raise GmailSetupRequired("Google Gmail dependencies are missing.") from e

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise GmailSetupRequired("credentials.json is missing.")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    return build("gmail", "v1", credentials=creds)


def _extract_body(payload: Dict[str, Any]) -> str:
    if not payload:
        return ""
    parts = payload.get("parts") or []
    for part in parts:
        mime = (part.get("mimeType") or "").lower()
        body = part.get("body", {})
        data = body.get("data")
        if mime == "text/plain" and data:
            try:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            except Exception:
                continue
    body = payload.get("body", {})
    data = body.get("data")
    if data:
        try:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        except Exception:
            return ""
    return ""


def get_last_email() -> Dict[str, str]:
    service = _build_service()
    res = service.users().messages().list(userId="me", maxResults=1, labelIds=["INBOX"]).execute()
    msgs = res.get("messages", [])
    if not msgs:
        return {"id": "", "from": "", "subject": "No email found", "snippet": "", "body": ""}
    message_id = msgs[0].get("id")
    full = service.users().messages().get(userId="me", id=message_id, format="full").execute()
    headers = full.get("payload", {}).get("headers", []) or []
    header_map = {h.get("name", "").lower(): h.get("value", "") for h in headers}
    return {
        "id": message_id or "",
        "from": header_map.get("from", ""),
        "subject": header_map.get("subject", ""),
        "snippet": full.get("snippet", ""),
        "body": _extract_body(full.get("payload", {})),
    }


def summarize_email(email: Dict[str, str]) -> str:
    body = (email.get("body") or email.get("snippet") or "").strip()
    prompt = (
        "Summarize this email in 3 short bullets and one action line.\n"
        f"From: {email.get('from','')}\n"
        f"Subject: {email.get('subject','')}\n"
        f"Body:\n{body[:5000]}"
    )
    return chat_with_ai(prompt)


def draft_reply(email: Dict[str, str], instructions: str) -> str:
    prompt = (
        "Draft a concise, professional email reply.\n"
        f"Original subject: {email.get('subject','')}\n"
        f"Original body:\n{(email.get('body') or email.get('snippet') or '')[:5000]}\n\n"
        f"Instructions: {instructions}"
    )
    return chat_with_ai(prompt)
