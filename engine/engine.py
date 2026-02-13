import uuid
from datetime import date, timedelta
from typing import Dict, Any, List, Tuple
from .models import Project, Task
from .storage import load_data, save_data

def _today_iso() -> str:
    return date.today().isoformat()

def create_project(name: str, deadline_iso: str | None = None, description: str = "") -> Dict[str, Any]:
    data = load_data()
    pid = str(uuid.uuid4())[:8]
    project = {
        "id": pid,
        "name": name,
        "description": description,
        "deadline": deadline_iso,
        "created_at": _today_iso(),
        "tasks": []
    }
    data["projects"].append(project)
    data["active_project_id"] = pid
    save_data(data)
    return project

def get_active_project() -> Dict[str, Any] | None:
    data = load_data()
    pid = data.get("active_project_id")
    for p in data.get("projects", []):
        if p.get("id") == pid:
            return p
    return None

def set_active_project(project_id: str) -> Dict[str, Any] | None:
    data = load_data()
    for p in data.get("projects", []):
        if p.get("id") == project_id:
            data["active_project_id"] = project_id
            save_data(data)
            return p
    return None

def generate_plan_basic(project: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Simple, demo-proof default plan (replace later with AI)
    tasks = [
        {"id": "t1", "name": "Scope & Requirements", "duration_days": 1, "depends_on": [], "status": "pending", "delay_days": 0},
        {"id": "t2", "name": "UI / Design", "duration_days": 1, "depends_on": ["t1"], "status": "pending", "delay_days": 0},
        {"id": "t3", "name": "Core Build (Engine + UI)", "duration_days": 2, "depends_on": ["t2"], "status": "pending", "delay_days": 0},
        {"id": "t4", "name": "Integrations (Voice + Actions)", "duration_days": 1, "depends_on": ["t3"], "status": "pending", "delay_days": 0},
        {"id": "t5", "name": "Testing & Demo Prep", "duration_days": 1, "depends_on": ["t4"], "status": "pending", "delay_days": 0},
    ]
    return tasks

def save_tasks(project_id: str, tasks: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    data = load_data()
    for p in data.get("projects", []):
        if p.get("id") == project_id:
            p["tasks"] = tasks
            save_data(data)
            return p
    return None

def mark_task_done(task_id: str) -> Tuple[bool, str]:
    data = load_data()
    pid = data.get("active_project_id")
    for p in data.get("projects", []):
        if p.get("id") == pid:
            for t in p.get("tasks", []):
                if t.get("id") == task_id:
                    t["status"] = "done"
                    save_data(data)
                    return True, f"Marked {task_id} as done."
    return False, "Task not found."

def delay_task(task_id: str, days: int) -> Tuple[bool, str]:
    data = load_data()
    pid = data.get("active_project_id")
    for p in data.get("projects", []):
        if p.get("id") == pid:
            for t in p.get("tasks", []):
                if t.get("id") == task_id:
                    t["delay_days"] = int(t.get("delay_days", 0)) + int(days)
                    save_data(data)
                    return True, f"Delayed {task_id} by {days} day(s)."
    return False, "Task not found."

def compute_schedule(project: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Simple dependency scheduling: assumes task list already topologically ordered
    start = date.today()
    schedule = []
    end_dates = {}

    for t in project.get("tasks", []):
        deps = t.get("depends_on", [])
        base_start = start
        for d in deps:
            if d in end_dates:
                base_start = max(base_start, end_dates[d] + timedelta(days=1))

        duration = int(t.get("duration_days", 1)) + int(t.get("delay_days", 0))
        task_start = base_start
        task_end = task_start + timedelta(days=max(duration - 1, 0))

        end_dates[t["id"]] = task_end
        schedule.append({**t, "start": task_start.isoformat(), "end": task_end.isoformat()})

    return schedule

def get_status(project: Dict[str, Any]) -> Dict[str, Any]:
    schedule = compute_schedule(project)
    if not schedule:
        return {"status": "unknown", "message": "No tasks yet.", "schedule": []}

    final_end = schedule[-1]["end"]
    deadline = project.get("deadline")

    if not deadline:
        return {"status": "ok", "message": f"Estimated finish: {final_end} (no deadline set).", "schedule": schedule}

    if final_end <= deadline:
        return {"status": "on-track", "message": f"On track. Estimated finish {final_end} before deadline {deadline}.", "schedule": schedule}
    return {"status": "off-track", "message": f"Off track. Estimated finish {final_end} after deadline {deadline}.", "schedule": schedule}
