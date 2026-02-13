from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict

@dataclass
class Task:
    id: str
    name: str
    duration_days: int = 1
    depends_on: List[str] = field(default_factory=list)
    status: str = "pending"  # pending | done
    delay_days: int = 0

@dataclass
class Project:
    id: str
    name: str
    description: str = ""
    deadline: Optional[str] = None  # ISO date string YYYY-MM-DD
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tasks: List[Task] = field(default_factory=list)
