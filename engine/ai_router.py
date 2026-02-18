"""
AI Router — Smart routing between Groq and Gemini
==================================================
- Default: Groq (fast, unlimited)
- Vision: Gemini (when images present)
- Planning/Heavy: Optional Gemini for complex tasks
"""

import os
from typing import Optional

# Import the chat function
try:
    from engine.ai_chat import chat_with_ai, _chat_with_groq, _chat_with_gemini_text
except ImportError:
    # Fallback if running standalone
    def chat_with_ai(msg, files=None): 
        return "AI router not properly configured"
    def _chat_with_groq(msg): 
        return "Groq not available"
    def _chat_with_gemini_text(msg): 
        return "Gemini not available"


def route_request(
    prompt: str, 
    context: str = None,
    task_type: str = "fast",
    files: list = None
) -> str:
    """
    Smart AI routing with context awareness.
    
    Args:
        prompt: The user's question/command
        context: Optional RAG context from knowledge base
        task_type: "fast" (default, Groq) | "vision" (Gemini) | "planning" (Gemini)
        files: Optional file attachments
    
    Returns:
        AI response string
    """
    files = files or []
    
    # Append context if provided (RAG/knowledge base)
    if context:
        full_prompt = f"{context}\n\nUser Question: {prompt}"
    else:
        full_prompt = prompt
    
    # ── VISION: Force Gemini ─────────────────────────────────────────────
    if task_type == "vision" or files:
        print("[AI Router] Vision task → Gemini")
        return chat_with_ai(full_prompt, files)
    
    # ── PLANNING: Use Gemini for complex planning ────────────────────────
    if task_type == "planning":
        print("[AI Router] Planning task → Gemini (structured output)")
        # Gemini has better JSON mode for structured planning
        try:
            return _chat_with_gemini_text(full_prompt)
        except Exception as e:
            print(f"[AI Router] Gemini planning failed: {e}, falling back to Groq")
            return _chat_with_groq(full_prompt)
    
    # ── FAST (DEFAULT): Use Groq ─────────────────────────────────────────
    print("[AI Router] Fast task → Groq")
    return chat_with_ai(full_prompt, files=[])  # No files = Groq path


# ── Convenience functions ─────────────────────────────────────────────────────

def ask_fast(prompt: str, context: str = None) -> str:
    """Quick questions — uses Groq (instant)."""
    return route_request(prompt, context=context, task_type="fast")


def ask_vision(prompt: str, files: list) -> str:
    """Image analysis — uses Gemini vision."""
    return route_request(prompt, task_type="vision", files=files)


def ask_planner(prompt: str) -> str:
    """Complex planning — uses Gemini for structured output."""
    return route_request(prompt, task_type="planning")


# ── Example usage ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test fast routing
    print("\n=== Fast Question (Groq) ===")
    print(ask_fast("What's 2+2?"))
    
    # Test with context
    print("\n=== Question with Context (Groq) ===")
    ctx = "Project deadline: March 1st. Team size: 3 developers."
    print(ask_fast("When is the deadline?", context=ctx))
    
    # Test planning
    print("\n=== Planning Task (Gemini) ===")
    print(ask_planner("Create a 5-task plan for building a website"))
