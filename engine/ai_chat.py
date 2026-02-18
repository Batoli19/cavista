
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

# Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Defaults
DEFAULT_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini").lower()
GEMINI_MODEL = os.environ.get("LLM_MODEL_NAME", "gemini-2.5-flash")
GROQ_MODEL = os.environ.get("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")

def _extract_text_from_file(base64_data: str, mime_type: str, filename: str) -> str:
    """
    Extracts text from base64 encoded file data.
    Supports: .txt, .docx, code files.
    """
    try:
        file_bytes = base64.b64decode(base64_data)
        
        # 1. DOCX Handling (Zip of XMLs)
        if "wordprocessingml.document" in mime_type or filename.endswith(".docx"):
            try:
                with io.BytesIO(file_bytes) as f:
                    with zipfile.ZipFile(f) as z:
                        xml_content = z.read("word/document.xml")
                        tree = ET.fromstring(xml_content)
                        # Namespace for word processing ml
                        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                        text_parts = []
                        for node in tree.iter():
                            if node.tag == f"{{{ns['w']}}}t": # Text node
                                if node.text:
                                    text_parts.append(node.text)
                            elif node.tag == f"{{{ns['w']}}}p": # Paragraph (add newline)
                                text_parts.append("\n")
                        return "".join(text_parts).strip()
            except Exception as e:
                print(f"[Text Extraction] Failed to parse DOCX: {e}")
                return None

        # 2. Plain Text / Code Handling
        # Try to decode as UTF-8
        try:
            return file_bytes.decode('utf-8')
        except UnicodeDecodeError:
            # If standard utf-8 fails, it might be binary or other encoding. 
            # For now, we only support utf-8 text.
            print(f"[Text Extraction] Could not decode file as UTF-8: {mime_type}")
            return None

    except Exception as e:
        print(f"[Text Extraction] Error: {e}")
        return None


def chat_with_ai(message: str, files: List[Dict[str, Any]] = None) -> str:
    """
    Sends a message to the AI. Smartly routes between Gemini and Groq.
    - Files present? -> Gemini (Multimodal)
    - Groq configured? -> Try Groq first, fallback to Gemini on error.
    - Default -> Gemini.
    """
    if not message and not files:
        return "I'm listening..."

    # 1. Force Gemini if files are present (Groq text models don't support images easily via this method)
    if files and len(files) > 0:
        return _chat_with_gemini(message, files)

    # 2. Check Provider Preference
    provider = DEFAULT_PROVIDER
    
    # Logic: If Groq is requested, try it. If it fails, fallback to Gemini.
    if provider == "groq":
        if not GROQ_API_KEY:
            return "Groq API Key missing. Please set GROQ_API_KEY or switch provider to 'gemini'."
        
        try:
            return _chat_with_groq(message)
        except Exception as e:
            print(f"[AI Chat] Groq failed: {e}. Falling back to Gemini.")
            return _chat_with_gemini(message, files) # Fallback

    # 3. Default to Gemini
    return _chat_with_gemini(message, files)

def _chat_with_groq(message: str) -> str:
    """
    Interacts with Groq API using urllib (standard library).
    """
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful, witty, and concise assistant."},
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" 
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            resp_body = response.read().decode("utf-8")
            resp_data = json.loads(resp_body)
            return resp_data["choices"][0]["message"]["content"]
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise Exception(f"HTTP {e.code} - {error_body}")


def _chat_with_gemini(message: str, files: List[Dict[str, Any]] = None) -> str:
    """
    Interacts with Google Gemini API with Retry Logic and Model Fallback.
    """
    if not GEMINI_API_KEY:
        return "I'm not connected to my primary brain (Gemini API Key missing)."

    # Define fallback models in order of preference
    # 1. User configured model (current default)
    # 2. Flash Lite (Fastest, cheapest)
    # 3. Flash 2.0 (Standard)
    # 4. Flash 2.5 (Newer)
    
    current_model = GEMINI_MODEL if "gemini" in GEMINI_MODEL else "gemini-2.0-flash"
    fallback_models = [
        "gemini-2.0-flash-lite-001",
        "gemini-2.0-flash",
        "gemini-2.5-flash" 
    ]
    
    # Construct distinct list of models to try
    models_to_try = [current_model]
    for m in fallback_models:
        if m != current_model and m not in models_to_try:
            models_to_try.append(m)

    max_retries_per_model = 1
    base_delay = 2

    all_errors = []

    for model in models_to_try:
        print(f"[Gemini] Attempting with model: {model}")
        
        for attempt in range(max_retries_per_model + 1):
            try:
                # Construct Gemini API URL
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"

                parts = []
                if message:
                    parts.append({"text": message})

                if files:
                    for file in files:
                        mime_type = file.get("type", "application/octet-stream")
                        base64_data = file.get("content", "")
                        
                        # Check for supported inline types
                        if mime_type.startswith("image/") or mime_type.startswith("audio/") or mime_type == "application/pdf":
                            parts.append({
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": base64_data
                                }
                            })
                        else:
                            # Attempt to extract text for other types (docx, txt, json, code)
                            extracted_text = _extract_text_from_file(base64_data, mime_type, file.get("name", ""))
                            if extracted_text:
                                # Append extracted text to the message parts
                                parts.append({"text": f"\n\n[Content of file '{file.get('name', 'unknown')}':]\n{extracted_text}\n[End of file]\n"})
                            else:
                                # Fallback or skip
                                 print(f"[Gemini] Skipping unsupported file type: {mime_type}")

                payload = {"contents": [{"parts": parts}]}
                data_json = json.dumps(payload).encode("utf-8")

                req = urllib.request.Request(
                    url, 
                    data=data_json, 
                    headers={"Content-Type": "application/json"}
                )

                with urllib.request.urlopen(req) as response:
                    resp_body = response.read().decode("utf-8")
                    resp_data = json.loads(resp_body)
                    try:
                        return resp_data["candidates"][0]["content"]["parts"][0]["text"]
                    except (KeyError, IndexError):
                        return "I thought about it, but couldn't form a response."

            except urllib.error.HTTPError as e:
                # Read error body
                try:
                    error_body = e.read().decode('utf-8')
                except:
                    error_body = "Could not read error body"
                
                error_msg = f"{model}: HTTP {e.code} - {error_body}"
                print(f"[Gemini] Error: {error_msg}")
                
                # Retryable errors for SAME model
                if e.code == 429 and attempt < max_retries_per_model:
                     # Wait and retry same model
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"[Gemini] Retrying {model} in {delay:.1f}s...")
                    time.sleep(delay)
                    continue
                
                all_errors.append(error_msg)
                # If 404, 429, 503, try next MODEL
                if e.code in [404, 429, 503, 400]: 
                    break 
                break
                
            except Exception as e:
                print(f"[Gemini] Error: {e}")
                all_errors.append(f"{model}: {str(e)}")
                break # Try next model
        
    # If all Gemini models fail, try Groq as a last resort
    if GROQ_API_KEY:
        print("[Gemini] All Gemini models failed. Falling back to Groq (Text Only).")
        try:
            # Append note about missing files if relevant
            groq_message = message
            if files:
                file_names = ", ".join([f.get("name", "unnamed") for f in files])
                groq_message += f"\n\n[System Note: User attached files ({file_names}) but Gemini is overloaded. Please answer the text prompt only.]"
            
            return _chat_with_groq(groq_message)
        except Exception as e:
            all_errors.append(f"Groq Fallback: {str(e)}")

    return f"All AI models failed.\nDetails:\n" + "\n".join(all_errors)
