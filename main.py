from engine.engine import (
    create_project, get_active_project, generate_plan_basic, save_tasks,
    mark_task_done, delay_task, get_status
)
from actions.system_actions import (
    minimize_all_windows, open_notes, open_word, open_excel, open_url
)
from documents.exporter import export_plan_to_word, export_schedule_to_excel

def handle_command(text: str) -> str:
    cmd = text.strip().lower()

    # System actions
    if "minimize" in cmd and "window" in cmd:
        return minimize_all_windows()
    if "open notes" in cmd or "open notepad" in cmd:
        return open_notes()
    if "open word" in cmd:
        return open_word()
    if "open excel" in cmd:
        return open_excel()
    if cmd.startswith("open url "):
        url = text.split(" ", 2)[2].strip()
        return open_url(url)

    # Project actions (simple)
    if cmd.startswith("create project"):
        name = text.replace("create project", "", 1).strip() or "Untitled Project"
        p = create_project(name=name)
        return f'Created project "{p["name"]}" (id {p["id"]}).'

    if "generate plan" in cmd:
        p = get_active_project()
        if not p:
            return "No active project. Say: create project <name>."
        tasks = generate_plan_basic(p)
        save_tasks(p["id"], tasks)
        return f"Generated a basic plan with {len(tasks)} tasks."

    if cmd.startswith("done "):
        task_id = text.split(" ", 1)[1].strip()
        ok, msg = mark_task_done(task_id)
        return msg

    if cmd.startswith("delay "):
        # format: delay t3 2
        parts = text.split()
        if len(parts) >= 3:
            task_id = parts[1]
            days = int(parts[2])
            ok, msg = delay_task(task_id, days)
            return msg
        return "Usage: delay <task_id> <days>"

    if "status" in cmd:
        p = get_active_project()
        if not p:
            return "No active project."
        s = get_status(p)
        return s["message"]

    if "export plan" in cmd and "word" in cmd:
        p = get_active_project()
        if not p:
            return "No active project."
        path = export_plan_to_word(p)
        return f"Exported plan to Word: {path}"

    if "export schedule" in cmd and "excel" in cmd:
        p = get_active_project()
        if not p:
            return "No active project."
        s = get_status(p)
        path = export_schedule_to_excel(p, s.get("schedule", []))
        return f"Exported schedule to Excel: {path}"

    return "I didn't understand. Try: create project <name>, generate plan, status, export plan to word."

if __name__ == "__main__":
    print("Jarvis (CLI mode). Type commands. Ctrl+C to exit.")
    while True:
        text = input("> ")
        reply = handle_command(text)
        print(reply)
