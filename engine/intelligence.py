import json
from typing import Dict, Any, List
from .ai_router import route_request
from .knowledge_base import search_knowledge

def analyze_project_risk(project: Dict[str, Any]) -> str:
    """
    Uses Reasoning AI (Mistral/GPT via OpenRouter) to analyze project risk.
    """
    if not project: return "No project to analyze."

    # 1. Gather Context
    tasks = project.get("tasks", [])
    task_summary = "\n".join([f"- {t['name']} ({t['status']}), {t['duration_days']} days" for t in tasks])
    deadline = project.get("deadline", "None")
    
    prompt = (
        f"Analyze the risk for project '{project['name']}'.\n"
        f"Deadline: {deadline}\n"
        f"Tasks:\n{task_summary}\n\n"
        "Identify potential bottlenecks, unrealistic timelines, or missing steps. "
        "Provide a risk score (1-10) and 3 specific recommendations."
    )

    # 2. Call Reasoning Model
    print("[Intelligence] Analyzing project risk...")
    response = route_request(prompt, task_type="reasoning")
    return response

def smart_prioritize(project: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Re-orders tasks based on AI logic (dependencies, impact, deadlines).
    """
    tasks = project.get("tasks", [])
    if not tasks: return []

    task_json = json.dumps(tasks)
    prompt = (
        "Re-order these tasks for maximum efficiency. "
        "Consider dependencies and logical flow. "
        "Return ONLY the JSON array of re-ordered tasks. No markdown.\n"
        f"{task_json}"
    )

    print("[Intelligence] Optimizing schedule...")
    response = route_request(prompt, task_type="reasoning")
    
    try:
        # Clean response (sometimes models add backticks)
        cleaned = response.replace("```json", "").replace("```", "").strip()
        optimized_tasks = json.loads(cleaned)
        return optimized_tasks
    except Exception as e:
        print(f"[Intelligence] Optimization failed: {e}")
        return tasks # Fallback to original

def predict_delays(project: Dict[str, Any]) -> str:
    """
    Predicts likely delays based on task descriptions and historical patterns (simulated).
    """
    # In a real app, this would use historical data. 
    # Here, we ask the AI to estimate based on complexity.
    
    tasks = project.get("tasks", [])
    prompt = (
        "Review these tasks and predict which ones are most likely to be delayed due to complexity or vagueness. "
        "Return a short list of 'At Risk' tasks with estimated extra days needed.\n"
        f"{json.dumps(tasks)}"
    )
    
    print("[Intelligence] Predicting delays...")
    return route_request(prompt, task_type="fast")
