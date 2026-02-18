import json
import os
import urllib.request
import urllib.error
import time
import random
from typing import List, Dict, Any

import base64
import io
import zipfile
import xml.etree.ElementTree as ET

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION — Groq first, Gemini only for vision
# ══════════════════════════════════════════════════════════════════════════════

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Models
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-exp")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER: Check if files contain images
# ══════════════════════════════════════════════════════════════════════════════

def _has_images(files: List[Dict[str, Any]]) -> bool:
    """Check if any file is an image."""
    if not files:
        return False
    for file in files:
        mime = file.get("type", "").lower()
        name = file.get("name", "").lower()
        if mime.startswith("image/") or name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')):
            return True
    return False


def _extract_text_from_file(base64_data: str, mime_type: str, filename: str) -> str:
    """
    Extracts text from base64 encoded file data.
    Supports: .txt, .docx, code files.
    """
    try:
        file_bytes = base64.b64decode(base64_data)
        
        # 1. DOCX Handling
        if "wordprocessingml.document" in mime_type or filename.endswith(".docx"):
            try:
                with io.BytesIO(file_bytes) as f:
                    with zipfile.ZipFile(f) as z:
                        xml_content = z.read("word/document.xml")
                        tree = ET.fromstring(xml_content)
                        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                        text_parts = []
                        for node in tree.iter():
                            if node.tag == f"{{{ns['w']}}}t":
                                if node.text:
                                    text_parts.append(node.text)
                            elif node.tag == f"{{{ns['w']}}}p":
                                text_parts.append("\n")
                        return "".join(text_parts).strip()
            except Exception as e:
                print(f"[Text Extraction] Failed to parse DOCX: {e}")
                return None

        # 2. Plain Text / Code
        try:
            return file_bytes.decode('utf-8')
        except UnicodeDecodeError:
            print(f"[Text Extraction] Could not decode file as UTF-8: {mime_type}")
            return None

    except Exception as e:
        print(f"[Text Extraction] Error: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT — Smart routing
# ══════════════════════════════════════════════════════════════════════════════

def chat_with_ai(message: str, files: List[Dict[str, Any]] = None) -> str:
    """
    Smart AI router:
    - Has images? → Gemini vision (ONLY path that uses Gemini)
    - Text only? → Groq (FAST, unlimited, DEFAULT)
    
    This is the NEW optimized version — Groq first, not Gemini.
    """
    if not message and not files:
        return "I'm listening..."

    files = files or []

    # ── VISION PATH: Images detected → use Gemini ────────────────────────
    if _has_images(files):
        print("[AI Chat] 🖼️  Images detected → routing to Gemini vision")
        return _chat_with_gemini_vision(message, files)

    # ── TEXT PATH: Default to Groq (FAST) ────────────────────────────────
    print("[AI Chat] 💬 Text only → routing to Groq (fast)")
    
    # Extract text from non-image files and append to message
    if files:
        text_content = []
        for file in files:
            mime = file.get("type", "")
            name = file.get("name", "unknown")
            b64_data = file.get("content", "")
            
            extracted = _extract_text_from_file(b64_data, mime, name)
            if extracted:
                text_content.append(f"\n--- File: {name} ---\n{extracted}\n--- End of {name} ---\n")
        
        if text_content:
            message += "\n\n" + "".join(text_content)
    
    # Try Groq first
    if GROQ_API_KEY:
        try:
            return _chat_with_groq(message)
        except Exception as e:
            print(f"[AI Chat] Groq failed: {e}")
            # Fallback to Gemini if Groq fails
            if GEMINI_API_KEY:
                print("[AI Chat] Falling back to Gemini (text only)")
                return _chat_with_gemini_text(message)
            return f"AI error: {e}"
    
    # No Groq key? Try Gemini
    if GEMINI_API_KEY:
        print("[AI Chat] No Groq key, using Gemini (text only)")
        return _chat_with_gemini_text(message)
    
    return "No AI configured. Please set GROQ_API_KEY or GEMINI_API_KEY."


# ══════════════════════════════════════════════════════════════════════════════
#  GROQ — Fast, unlimited, text-only (DEFAULT)
# ══════════════════════════════════════════════════════════════════════════════

def _chat_with_groq(message: str) -> str:
    """
    Groq API — fast, unlimited free tier, text only.
    This is the DEFAULT path for all text queries.
    """
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are JARVIS, a helpful and witty AI assistant."},
            {"role": "user", "content": message}
        ],
        "temperature": 0.7,
        "max_tokens": 1024
    }
    
    data = json.dumps(payload).encode("utf-8")
    
    req = urllib.request.Request(
        url, 
        data=data, 
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "User-Agent": "JARVIS/1.0"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            resp_body = response.read().decode("utf-8")
            resp_data = json.loads(resp_body)
            return resp_data["choices"][0]["message"]["content"].strip()
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise Exception(f"Groq HTTP {e.code}: {error_body}")
    except Exception as e:
        raise Exception(f"Groq error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  GEMINI — Only for vision (images) or fallback
# ══════════════════════════════════════════════════════════════════════════════

def _chat_with_gemini_vision(message: str, files: List[Dict[str, Any]]) -> str:
    """
    Gemini vision — ONLY for image analysis.
    Single attempt, no retry loops (to avoid rate limit cascades).
    """
    if not GEMINI_API_KEY:
        return "Vision unavailable (no GEMINI_API_KEY). Please add images via upload."

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

        parts = []
        if message:
            parts.append({"text": message})

        # Add files
        for file in files:
            mime_type = file.get("type", "application/octet-stream")
            base64_data = file.get("content", "")
            name = file.get("name", "unknown")
            
            # Images, audio, PDF → inline
            if mime_type.startswith("image/") or mime_type.startswith("audio/") or mime_type == "application/pdf":
                parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": base64_data
                    }
                })
            else:
                # Extract text from other files
                extracted = _extract_text_from_file(base64_data, mime_type, name)
                if extracted:
                    parts.append({"text": f"\n[File: {name}]\n{extracted}\n[End of file]\n"})

        payload = {"contents": [{"parts": parts}]}
        data_json = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            url, 
            data=data_json, 
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=20) as response:
            resp_body = response.read().decode("utf-8")
            resp_data = json.loads(resp_body)
            try:
                return resp_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            except (KeyError, IndexError):
                return "Gemini processed the request but returned no text."

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        print(f"[Gemini Vision] HTTP {e.code}: {error_body}")
        
        # If rate limited, try Groq as text fallback
        if e.code == 429 and GROQ_API_KEY:
            print("[Gemini Vision] Rate limited. Falling back to Groq (text only, no vision).")
            fallback_msg = f"{message}\n\n[Note: Images were attached but Gemini is rate-limited. Answering text only.]"
            try:
                return _chat_with_groq(fallback_msg)
            except:
                pass
        
        return f"Vision error: HTTP {e.code} - Gemini overloaded. Try again in a minute."
    
    except Exception as e:
        print(f"[Gemini Vision] Error: {e}")
        return f"Vision error: {e}"


def _chat_with_gemini_text(message: str) -> str:
    """
    Gemini text-only mode (fallback when Groq unavailable).
    Single attempt, no retries.
    """
    if not GEMINI_API_KEY:
        return "AI unavailable (no API keys configured)."

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [{"parts": [{"text": message}]}]
        }
        
        data_json = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, 
            data=data_json, 
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=15) as response:
            resp_body = response.read().decode("utf-8")
            resp_data = json.loads(resp_body)
            try:
                return resp_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            except (KeyError, IndexError):
                return "Gemini returned no response."

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        print(f"[Gemini Text] HTTP {e.code}: {error_body}")
        return f"Gemini error: {e.code} - Rate limited or overloaded."
    
    except Exception as e:
        print(f"[Gemini Text] Error: {e}")
        return f"Gemini error: {e}"