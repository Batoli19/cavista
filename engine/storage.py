import json
from pathlib import Path
from typing import Any, Dict

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "projects.json"

def load_data() -> Dict[str, Any]:
    if not DATA_PATH.exists():
        return {"active_project_id": None, "projects": []}
    try:
        return json.loads(DATA_PATH.read_text(encoding="utf-8") or "{}") or {"active_project_id": None, "projects": []}
    except Exception:
        return {"active_project_id": None, "projects": []}

def save_data(data: Dict[str, Any]) -> None:
    DATA_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
