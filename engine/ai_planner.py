import json
import os
import urllib.request
import urllib.error
from typing import List, Dict, Any

# Configuration - Use Gemini for planning
API_KEY = os.environ.get("GEMINI_API_KEY", "") 
MODEL_NAME = os.environ.get("LLM_MODEL_NAME", "gemini-2.0-flash")

def generate_plan_ai(project_name: str, description: str, team_size: int = 1) -> List[Dict[str, Any]]:
    """
    Generates a list of tasks for the given project using Gemini.
    Fallback to Basic Plan if API fails or is not configured.
    """
    if not API_KEY:
        print("Warning: GEMINI_API_KEY not set. Using fallback plan.")
        return []

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
    The output must be RAW JSON only. No markdown formatting.
    
    Example format:
    [
        {{"id": "t1", "name": "Setup", "description": "Initialize project", "duration_days": 1, "depends_on": [], "priority": "high", "role": "general"}},
        {{"id": "t2", "name": "Design", "description": "Create wireframes", "duration_days": 2, "depends_on": ["t1"], "priority": "high", "role": "design"}}
    ]
    """

    try:
        # --- GOOGLE GEMINI REST API ---
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"
        
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
        
        with urllib.request.urlopen(req) as response:
            resp_body = response.read().decode("utf-8")
            resp_data = json.loads(resp_body)
            # Gemini response path: candidates[0].content.parts[0].text
            content = resp_data["candidates"][0]["content"]["parts"][0]["text"]

        # Common Cleanup & Parsing
        content = content.replace("```json", "").replace("```", "").strip()
        tasks = json.loads(content)
        
        # Handle if the model wrapped it in a key
        if isinstance(tasks, dict) and "tasks" in tasks:
            tasks = tasks["tasks"]
            
        return tasks

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return []

