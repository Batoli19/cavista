"""
AI Plan Generator — Optimized for Groq
=======================================
Uses Groq by default for fast JSON generation.
Falls back to Gemini if Groq fails.
"""

import json
import os
import urllib.request
import urllib.error
from typing import List, Dict, Any

# Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "") 
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")


def generate_plan_ai(project_name: str, description: str, team_size: int = 1) -> List[Dict[str, Any]]:
    """
    Generates a list of tasks for the given project.
    
    NEW: Uses Groq first (fast, unlimited), falls back to Gemini if needed.
    """
    
    prompt = f"""
Act as a Senior Project Manager.
Create a detailed Work Breakdown Structure (WBS) for a project named "{project_name}".
Description: {description}
Team Size: {team_size} users.

Return a JSON array of tasks. Each task must have:
- id: string (t1, t2, etc.)
- name: string (short title)
- description: string (detailed instruction)
- duration_days: integer (1-5)
- depends_on: list of strings (ids of parent tasks)
- priority: string (low, medium, high)
- role: string (frontend, backend, design, devops, general)

The plan should be realistic and have at least 5-10 tasks.
The output must be ONLY valid JSON. No markdown, no explanations.

Example:
[
  {{"id": "t1", "name": "Setup", "description": "Initialize project", "duration_days": 1, "depends_on": [], "priority": "high", "role": "general"}},
  {{"id": "t2", "name": "Design", "description": "Create wireframes", "duration_days": 2, "depends_on": ["t1"], "priority": "high", "role": "design"}}
]
"""

    # ── TRY GROQ FIRST (fast, unlimited) ──────────────────────────────────────
    if GROQ_API_KEY:
        print("[Plan Generator] Using Groq (fast)...")
        try:
            return _generate_with_groq(prompt)
        except Exception as e:
            print(f"[Plan Generator] Groq failed: {e}, falling back to Gemini")
    
    # ── FALLBACK TO GEMINI ────────────────────────────────────────────────────
    if GEMINI_API_KEY:
        print("[Plan Generator] Using Gemini (fallback)...")
        try:
            return _generate_with_gemini(prompt)
        except Exception as e:
            print(f"[Plan Generator] Gemini failed: {e}")
            return []
    
    print("[Plan Generator] No AI configured. Please set GROQ_API_KEY or GEMINI_API_KEY.")
    return []


def _generate_with_groq(prompt: str) -> List[Dict[str, Any]]:
    """Generate plan using Groq (fast, unlimited)."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a project planning expert. Return ONLY valid JSON, no markdown."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
        "max_tokens": 2000
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, 
        data=data, 
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}"
        }
    )
    
    with urllib.request.urlopen(req, timeout=20) as response:
        resp_body = response.read().decode("utf-8")
        resp_data = json.loads(resp_body)
        content = resp_data["choices"][0]["message"]["content"]
    
    # Clean and parse
    content = content.replace("```json", "").replace("```", "").strip()
    tasks = json.loads(content)
    
    # Handle if wrapped in a key
    if isinstance(tasks, dict) and "tasks" in tasks:
        tasks = tasks["tasks"]
    
    return tasks


def _generate_with_gemini(prompt: str) -> List[Dict[str, Any]]:
    """Generate plan using Gemini (fallback)."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.5,
            "responseMimeType": "application/json"
        }
    }
    
    data_json = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, 
        data=data_json, 
        headers={"Content-Type": "application/json"}
    )
    
    with urllib.request.urlopen(req, timeout=20) as response:
        resp_body = response.read().decode("utf-8")
        resp_data = json.loads(resp_body)
        content = resp_data["candidates"][0]["content"]["parts"][0]["text"]
    
    # Clean and parse
    content = content.replace("```json", "").replace("```", "").strip()
    tasks = json.loads(content)
    
    # Handle if wrapped
    if isinstance(tasks, dict) and "tasks" in tasks:
        tasks = tasks["tasks"]
    
    return tasks