from __future__ import annotations

import re
from typing import Any, Dict, List

from .ai_planner import generate_plan_ai
from .engine import create_project, generate_plan_basic, save_tasks
from .web_research import research_topic_with_wikipedia


def _topic_from_request(user_text: str) -> str:
    raw = (user_text or "").strip()
    lowered = raw.lower()

    if " for " in lowered:
        idx = lowered.rfind(" for ")
        topic = raw[idx + 5 :].strip(" .,!?:;")
    else:
        topic = raw

    topic = re.sub(r"^(this|a|an|the)\s+", "", topic, flags=re.IGNORECASE)
    topic = re.sub(r"\b(create|make|build|generate|plan|project|work|automation|workflow)\b", "", topic, flags=re.IGNORECASE)
    topic = re.sub(r"\s+", " ", topic).strip(" .,!?:;")
    return topic or "Business Operations"


def _build_description(topic: str, research: Dict[str, Any]) -> str:
    lines = [f"Context for {topic}"]
    for i, row in enumerate(research.get("raw", [])[:4], start=1):
        lines.append(f"{i}. {row.get('title','')}: {row.get('summary','')}")
    return "\n".join(lines)


def _phase_sections(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not tasks:
        return []
    buckets = [tasks[:3], tasks[3:6], tasks[6:]]
    sections: List[Dict[str, Any]] = []
    for i, group in enumerate(buckets, start=1):
        if not group:
            continue
        sections.append(
            {
                "title": f"Phase {i}",
                "items": [f"{t.get('name', 'Task')} ({t.get('duration_days', 1)} day)" for t in group],
            }
        )
    return sections


def create_project_plan_from_web_request(user_text: str) -> Dict[str, Any]:
    topic = _topic_from_request(user_text)
    project_name = f"{topic.title()} Workflow Plan"

    research = research_topic_with_wikipedia(topic, limit=4)
    description = _build_description(topic, research)

    project = create_project(name=project_name, description=description)
    tasks = generate_plan_ai(project_name, description, team_size=3)
    if not tasks:
        tasks = generate_plan_basic(project)
    save_tasks(project["id"], tasks)

    return {
        "project": project,
        "topic": topic,
        "summary": research.get("summary", ""),
        "tasks": tasks,
        "phases": _phase_sections(tasks),
        "sources": research.get("sources", []),
        "evidence": research.get("evidence", []),
    }
