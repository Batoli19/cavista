from engine.engine import (
    create_project, get_active_project, generate_plan, save_tasks,
    mark_task_done, delay_task, get_status, get_project_diagnosis
)
from actions.system_actions import (
    minimize_all_windows, open_notes, open_word, open_excel, open_url
)
from documents.exporter import export_plan_to_word, export_schedule_to_excel
from engine.ai_chat import chat_with_ai 
from engine.ai_router import route_request
from engine.intelligence import analyze_project_risk, smart_prioritize, predict_delays
from engine.knowledge_base import search_knowledge

try:
    from voice.voice_io import speak, listen_command
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    def speak(t): print(f"[TTS] {t}")
    def listen_command(): return "VOICE_ERROR: Module not found"


# ══════════════════════════════════════════════════════════════════════════════
#  OPTIMIZED AI ROUTING — Groq first, Gemini only for images
# ══════════════════════════════════════════════════════════════════════════════

def has_images(files):
    """Check if files list contains any images."""
    if not files:
        return False
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.tiff')
    return any(str(f).lower().endswith(image_extensions) for f in files)


def handle_command(text: str, files: list = None) -> str:
    """
    Main command handler with OPTIMIZED AI routing:
    - Text-only queries → Groq (FAST, unlimited)
    - Image analysis → Gemini vision (only when needed)
    """
    cmd = text.strip().lower()
    files = files or []

    # ── FILES WITH IMAGES: Use Gemini Vision (ONLY path that uses Gemini) ────
    if files and has_images(files):
        print(f"[Main] 🖼️  Images detected ({len(files)} files) → using AI vision")
        return chat_with_ai(text, files)  # This should route to Gemini vision

    # ── HELP ──────────────────────────────────────────────────────────────────
    if "help" in cmd or "what can you do" in cmd:
        return (
            "I can help with:\n"
            "1. Projects: 'Create project <name>', 'Generate plan', 'Status', 'Doctor', 'Export plan'.\n"
            "2. Tasks: 'Done <task_id>', 'Delay <task_id> <days>'.\n"
            "3. System: 'Open notes', 'Open word', 'Open excel', 'Minimize windows', 'Play music'."
        )

    # ── SYSTEM ACTIONS ────────────────────────────────────────────────────────
    if "minimize" in cmd or "hide windows" in cmd:
        return minimize_all_windows()
        
    if "close" in cmd or "terminate" in cmd or "kill" in cmd:
        from actions.system_actions import close_application
        for keyword in ["close ", "terminate ", "kill "]:
            if keyword in cmd:
                app_name = text.lower().split(keyword, 1)[1].strip()
                print(f"[Main] Closing app: {app_name}")
                return close_application(app_name)
    
    if "open" in cmd:
        # Check for specific built-ins first
        if "note" in cmd or "notepad" in cmd: 
            return open_notes()
        if "word" in cmd: 
            return open_word()
        if "excel" in cmd: 
            return open_excel()
        if "folder" in cmd or "directory" in cmd: 
            import os
            from actions.system_actions import open_folder
            return open_folder(os.getcwd())
        if "url" in cmd or "browser" in cmd or "google" in cmd:
            if "pixel" in cmd or "cavista" in cmd: 
                return open_url("https://www.cavista.net")
            return open_url("https://www.google.com")
            
        # Generic App Open: "Open whatsapp", "Open spotify"
        from actions.system_actions import open_application
        app_name = text.lower().replace("open", "", 1).strip()
        print(f"[Main] Opening app: {app_name}")
        if app_name:
            return open_application(app_name)

    if "music" in cmd or "spotify" in cmd or "play" in cmd:
        from actions.system_actions import play_music
        return play_music()

    if "folder" in cmd or "directory" in cmd or "workspace" in cmd:
        from actions.system_actions import open_folder
        import os
        return open_folder(os.getcwd())

    if "browser" in cmd or "google" in cmd or "open url" in cmd:
        if "pixel" in cmd or "cavista" in cmd:
            return open_url("https://www.cavista.net")
        return open_url("https://www.google.com")

    # ── PROJECT ACTIONS ───────────────────────────────────────────────────────
    
    # "Create project Hackathon"
    if "create" in cmd and "project" in cmd:
        for prefix in ["create project", "new project", "create a project"]:
            if prefix in cmd:
                name = text.lower().replace(prefix, "", 1).strip()
                name = name.title() or "Untitled Project"
                p = create_project(name=name)
                return f'Created project "{p["name"]}" (ID: {p["id"]}). Ready to plan?'

    # "Generate plan", "Make a plan", "Plan it"
    if "plan" in cmd and ("generate" in cmd or "make" in cmd or "create" in cmd):
        p = get_active_project()
        if not p: 
            return "No active project. Say 'Create project <name>' first."
        
        use_ai = True 
        tasks = generate_plan(p, use_ai=use_ai)
        save_tasks(p["id"], tasks)
        return f"Plan generated! I've created {len(tasks)} tasks. Say 'Status' to see them."

    # "Status", "Show me", "How is it going"
    if "status" in cmd or "progress" in cmd or "list tasks" in cmd:
        p = get_active_project()
        if not p: 
            return "No active project."
        s = get_status(p)
        return s["message"]

    # "Doctor", "Diagnose", "Check health"
    if "doctor" in cmd or "diagnose" in cmd or "health" in cmd or "check" in cmd:
        p = get_active_project()
        if not p: 
            return "No active project."
        diags = get_project_diagnosis(p["id"])
        if not diags: 
            return "Project is healthy!"
        
        # Add AI Risk Analysis
        ai_risk = analyze_project_risk(p)
        return "\n".join(["[Doctor 🩺] Diagnosis:"] + [f"- {d}" for d in diags] + ["\n[AI Risk Assessment]:", ai_risk])

    # "Risk check", "Analyze risk"
    if "risk" in cmd:
        p = get_active_project()
        if not p: 
            return "No active project."
        return analyze_project_risk(p)

    # "Optimize schedule", "Smart prioritize"
    if "optimize" in cmd or "prioritize" in cmd:
        p = get_active_project()
        if not p: 
            return "No active project."
        
        new_tasks = smart_prioritize(p)
        if new_tasks:
            save_tasks(p["id"], new_tasks)
            return "I've re-ordered your tasks for maximum efficiency based on dependencies and logic. Say 'Status' to view."
        return "Could not optimize schedule."

    # "Ask project...", "Where is...", "Who is..." (RAG)
    if "where" in cmd or "who" in cmd or "what" in cmd or "how" in cmd:
        p = get_active_project()
        if p:
            # Try RAG first
            context = search_knowledge(text)
            if context:
                # Route to fast chat with context
                response = route_request(text, context=context, task_type="fast")
                return f"[Context Aware]: {response}"

    # "Mark t1 done", "t1 is finished"
    if "done" in cmd or "finish" in cmd or "complete" in cmd:
        import re
        match = re.search(r"\b(t\d+)\b", cmd)
        if match:
            task_id = match.group(1)
            ok, msg = mark_task_done(task_id)
            return msg
        else:
            return "Which task? Say 'Mark t1 done'."

    # "Delay t1 by 2 days"
    if "delay" in cmd:
        import re
        t_match = re.search(r"\b(t\d+)\b", cmd)
        d_match = re.search(r"\b(\d+)\b", cmd)
        
        if t_match and d_match:
            task_id = t_match.group(1)
            days = int(d_match.group(1))
            ok, msg = delay_task(task_id, days)
            return msg
        return "To delay, say: 'Delay task t1 by 2 days'."

    # "Export plan", "Save to word"
    if "export" in cmd or "save" in cmd:
        p = get_active_project()
        if not p: 
            return "No active project."
        
        if "excel" in cmd or "schedule" in cmd:
            s = get_status(p)
            path = export_schedule_to_excel(p, s["schedule"])
            return f"Schedule saved to Excel: {path}"
        
        # Default to word
        path = export_plan_to_word(p)
        return f"Plan saved to Word: {path}"

    # ── FALLBACK TO AI CHAT (Groq — FAST) ────────────────────────────────────
    # This is the DEFAULT path for all unmatched text queries
    # NO images here, so it will use Groq (instant response)
    
    print(f"[Main] 💬 No command matched → asking AI (Groq - fast)")
    return chat_with_ai(text, files=[])  # Empty files = Groq path


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN CLI/VOICE LOOP
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    
    mode = "cli"
    if len(sys.argv) > 1 and sys.argv[1] == "--voice":
        mode = "voice"
        if not VOICE_AVAILABLE:
            print("Voice module not available. Installing requirements...")

    print(f"Jarvis ({mode.upper()} mode). Ctrl+C to exit.")
    
    if mode == "voice":
        speak("I am online. What is your command?")
        
    while True:
        try:
            if mode == "voice":
                print("Listening...")
                text = listen_command()
                if "VOICE_ERROR" in text:
                    if "Timeout" in text:
                        continue
                    print(text)
                    continue
                
                print(f"Heard: {text}")
                if "exit" in text.lower() or "quit" in text.lower():
                    speak("Goodbye.")
                    break
                    
                reply = handle_command(text)
                print(f"Jarvis: {reply}")
                speak(reply)
                
            else:
                text = input("> ")
                if text.lower() in ["exit", "quit"]:
                    break
                reply = handle_command(text)
                print(reply)
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()