from engine.engine import (
    create_project, get_active_project, generate_plan, save_tasks,
    mark_task_done, delay_task, get_status, get_project_diagnosis
)
from actions.system_actions import (
    minimize_all_windows, open_notes, open_word, open_excel, open_url
)
from documents.exporter import export_plan_to_word, export_schedule_to_excel
from engine.ai_chat import chat_with_ai # New Intelligence Module

try:
    from voice.voice_io import speak, listen_command
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    def speak(t): print(f"[TTS] {t}")
    def listen_command(): return "VOICE_ERROR: Module not found"


def handle_command(text: str, files: list = None) -> str:
    cmd = text.strip().lower()

    # If there are files attached, go straight to AI Analysis
    if files and len(files) > 0:
        return chat_with_ai(text, files)

    # --- HELP ---
    if "help" in cmd or "what can you do" in cmd:
        return (
            "I can help with:\n"
            "1. Projects: 'Create project <name>', 'Generate plan', 'Status', 'Doctor', 'Export plan'.\n"
            "2. Tasks: 'Done <task_id>', 'Delay <task_id> <days>'.\n"
            "3. System: 'Open notes', 'Open word', 'Open excel', 'Minimize windows', 'Play music'."
        )

    # --- SYSTEM ACTIONS ---
    if "minimize" in cmd or "hide windows" in cmd:
        return minimize_all_windows()
        
    if "close" in cmd or "terminate" in cmd or "kill" in cmd:
        # "Close whatsapp", "Terminate spotify"
        from actions.system_actions import close_application
        # Extract app name
        for keyword in ["close ", "terminate ", "kill "]:
            if keyword in cmd:
                app_name = text.lower().split(keyword, 1)[1].strip()
                print(f"[DEBUG main.py] Closing app: {app_name}")
                return close_application(app_name)
    
    if "open" in cmd:
        # Check for specific built-ins first
        if "note" in cmd or "notepad" in cmd: return open_notes()
        if "word" in cmd: return open_word()
        if "excel" in cmd: return open_excel()
        if "folder" in cmd or "directory" in cmd: 
            import os
            from actions.system_actions import open_folder
            return open_folder(os.getcwd())
        if "url" in cmd or "browser" in cmd or "google" in cmd:
            if "pixel" in cmd or "cavista" in cmd: return open_url("https://www.cavista.net")
            return open_url("https://www.google.com")
            
        # Generic App Open: "Open whatsapp", "Open spotify"
        from actions.system_actions import open_application
        app_name = text.lower().replace("open", "", 1).strip()
        print(f"[DEBUG main.py] Opening app generic: {app_name}")
        if app_name:
            return open_application(app_name)

    if "music" in cmd or "spotify" in cmd or "play" in cmd:
        from actions.system_actions import play_music
        return play_music()

    if "folder" in cmd or "directory" in cmd or "workspace" in cmd:
        # For this hackathon, just open the current directory
        # In a real app, this would open the specific project's folder
        from actions.system_actions import open_folder
        import os
        return open_folder(os.getcwd())

    if "browser" in cmd or "google" in cmd or "open url" in cmd:
        if "pixel" in cmd or "cavista" in cmd: # Hackathon easter egg?
            return open_url("https://www.cavista.net")
        return open_url("https://www.google.com")

    # --- PROJECT ACTIONS ---
    
    # "Create project Hackathon"
    if "create" in cmd and "project" in cmd:
        # Extract name: "create project X" or "new project X"
        for prefix in ["create project", "new project", "create a project"]:
            if prefix in cmd:
                name = text.lower().replace(prefix, "", 1).strip()
                # Restore case if possible? No, voice is lowercase. 
                # Just Title Case it.
                name = name.title() or "Untitled Project"
                p = create_project(name=name)
                return f'Created project "{p["name"]}" (ID: {p["id"]}). Ready to plan?'

    # "Generate plan", "Make a plan", "Plan it"
    if "plan" in cmd and ("generate" in cmd or "make" in cmd or "create" in cmd):
        p = get_active_project()
        if not p: return "No active project. Say 'Create project <name>' first."
        
        # Check if AI is configured (simple check)
        use_ai = True 
        tasks = generate_plan(p, use_ai=use_ai)
        save_tasks(p["id"], tasks)
        return f"Plan generated! I've created {len(tasks)} tasks. Say 'Status' to see them."

    # "Status", "Show me", "How is it going"
    if "status" in cmd or "progress" in cmd or "list tasks" in cmd:
        p = get_active_project()
        if not p: return "No active project."
        s = get_status(p)
        return s["message"]

    # "Doctor", "Diagnose", "Check health"
    if "doctor" in cmd or "diagnose" in cmd or "health" in cmd or "check" in cmd:
        p = get_active_project()
        if not p: return "No active project."
        diags = get_project_diagnosis(p["id"])
        if not diags: return "Project is healthy!"
        return "\n".join(["[Doctor 🩺] Diagnosis:"] + [f"- {d}" for d in diags])

    # "Mark t1 done", "t1 is finished"
    if "done" in cmd or "finish" in cmd or "complete" in cmd:
        # Try to find a task ID (e.g., t1, t2)
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
        # Look for "t1" and a number
        t_match = re.search(r"\b(t\d+)\b", cmd)
        d_match = re.search(r"\b(\d+)\b", cmd)
        
        if t_match and d_match:
            task_id = t_match.group(1)
            days = int(d_match.group(1))
            # If the number is the task id (e.g. t1), find the other number
            if str(days) in task_id: 
                 # This logic is tricky with regex, simpler approach:
                 pass
            
            ok, msg = delay_task(task_id, days)
            return msg
        return "To delay, say: 'Delay task t1 by 2 days'."

    # "Export plan", "Save to word"
    if "export" in cmd or "save" in cmd:
        p = get_active_project()
        if not p: return "No active project."
        
        if "excel" in cmd or "schedule" in cmd:
            s = get_status(p)
            path = export_schedule_to_excel(p, s["schedule"])
            return f"Schedule saved to Excel: {path}"
        
        # Default to word
        path = export_plan_to_word(p)
        return f"Plan saved to Word: {path}"

    # Removed early return "I'm listening..." to allow fallback to AI Chat

    # Fallback to General AI Chat
    print(f"[Main] No command matched. Asking AI: {text}")
    return chat_with_ai(text)

if __name__ == "__main__":
    import sys
    
    mode = "cli"
    if len(sys.argv) > 1 and sys.argv[1] == "--voice":
        mode = "voice"
        if not VOICE_AVAILABLE:
            print("Voice module not available. Installing requirements...")
            # Optional: auto-install or just fail
            pass

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
                        continue # just listen again
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
