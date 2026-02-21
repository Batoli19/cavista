from __future__ import annotations

import os
import re
from typing import Any, Dict, List

from actions.system_actions import minimize_all_windows, open_excel, open_notes, open_url, open_word
from documents.exporter import export_plan_to_word, export_schedule_to_excel
from engine.ai_chat import chat_with_ai
from engine.artifacts import (
    MissingExportDependencyError,
    export_docx_from_research,
    export_pptx_from_research,
    export_xlsx_from_research,
)
from engine.engine import (
    create_project,
    delay_task,
    generate_plan,
    get_active_project,
    get_project_diagnosis,
    get_status,
    mark_task_done,
    save_tasks,
)
from engine.presenter import make_response
from engine.research_planner import create_project_plan_from_web_request
from engine.web_research import research_topic_with_wikipedia
from engine.youtube_learning import learn_from_youtube
from engine.os_actions import open_url as os_open_url
try:
    from engine.gmail_agent import (
        GmailSetupRequired,
        draft_reply as gmail_draft_reply,
        get_last_email as gmail_get_last_email,
        summarize_email as gmail_summarize_email,
    )
except Exception:
    GmailSetupRequired = RuntimeError
    gmail_get_last_email = None
    gmail_summarize_email = None
    gmail_draft_reply = None

PROJECT_CONVERSATION_STATE: Dict[str, Dict[str, str]] = {}
STATE_FIELDS = ["company_name", "domain", "chosen_workflow_area", "goal", "compliance_level"]
WORKFLOW_SESSION_STATE: Dict[str, Dict[str, Any]] = {}
DEBUG_INTENT = (os.environ.get("DEBUG_INTENT", "false").strip().lower() in {"1", "true", "yes", "on"})


def _state_key() -> str:
    active = get_active_project()
    if active and active.get("id"):
        return str(active["id"])
    return "__session__"


def _get_state() -> Dict[str, str]:
    key = _state_key()
    if key not in PROJECT_CONVERSATION_STATE:
        PROJECT_CONVERSATION_STATE[key] = {k: "" for k in STATE_FIELDS}
    return PROJECT_CONVERSATION_STATE[key]


def _get_workflow_session() -> Dict[str, Any]:
    key = _state_key()
    if key not in WORKFLOW_SESSION_STATE:
        WORKFLOW_SESSION_STATE[key] = {
            "last_research": None,
            "last_files": [],
            "last_intent": None,
            "artifacts": [],
            "pending": None,
            "context": {"topic": None, "country": None, "domain": None},
        }
    return WORKFLOW_SESSION_STATE[key]


def _extract_first(text: str, pattern: str) -> str:
    m = re.search(pattern, text, flags=re.IGNORECASE)
    return (m.group(1).strip() if m else "")


def _update_state_from_text(state: Dict[str, str], text: str) -> None:
    lowered = text.lower()
    company = _extract_first(text, r"for\s+([a-zA-Z0-9\s&-]+?)\s+company")
    if not company:
        company = _extract_first(text, r"for\s+([a-zA-Z0-9\s&-]+)")
    if company and not state.get("company_name"):
        state["company_name"] = company.title()

    if not state.get("domain"):
        for dom in ["health", "finance", "retail", "education", "logistics", "insurance"]:
            if dom in lowered:
                state["domain"] = dom
                break

    if not state.get("chosen_workflow_area"):
        for area in ["claims", "billing", "onboarding", "support", "audit", "compliance", "reporting", "sales"]:
            if area in lowered:
                state["chosen_workflow_area"] = area
                break

    goal = _extract_first(text, r"goal\s*(?:is|:)\s*([a-zA-Z0-9\s,-]+)")
    if not goal and " to " in lowered and not state.get("goal"):
        goal = text.split(" to ", 1)[1].strip(" .")
    if goal and not state.get("goal"):
        state["goal"] = goal

    if not state.get("compliance_level"):
        if "hipaa" in lowered:
            state["compliance_level"] = "hipaa"
        elif "soc 2" in lowered or "soc2" in lowered:
            state["compliance_level"] = "soc2"
        elif "gdpr" in lowered:
            state["compliance_level"] = "gdpr"
        elif "high compliance" in lowered:
            state["compliance_level"] = "high"


def _looks_cutoff(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False
    if t in {"hi", "hello", "hey", "yo"}:
        return False
    if len(t) <= 3:
        return True
    return t in {"and", "so", "uh", "umm", "hmm", "wait", "then", "..."} or t.endswith(("...", ",", " and", " so"))


def _extract_research_topic(text: str) -> str:
    t = (text or "").strip()
    lowered = t.lower()
    for prefix in ["research ", "find research on ", "research on ", "research about "]:
        if lowered.startswith(prefix):
            return t[len(prefix):].strip(" .")
    return t


def _to_research_object(topic: str, research_payload: Dict[str, Any]) -> Dict[str, Any]:
    raw = research_payload.get("raw", []) or []
    key_points = [f"{item.get('title','')}: {item.get('summary','')}" for item in raw[:5]]
    return {
        "topic": topic,
        "summary": research_payload.get("summary", ""),
        "key_points": key_points,
        "data_points": [],
        "sources": research_payload.get("sources", []),
    }


def _resolve_export_target(cmd: str) -> str | None:
    c = cmd.lower()
    if "word" in c or "docx" in c:
        return "docx"
    if "powerpoint" in c or "ppt" in c or "slides" in c:
        return "pptx"
    if "excel" in c or "xlsx" in c or "spreadsheet" in c:
        return "xlsx"
    return None


def _log_intent(intent: str, text: str) -> None:
    if DEBUG_INTENT:
        print(f"[Intent] {intent} <= {text}")


def _is_research_request(cmd: str) -> bool:
    patterns = [
        r"\bresearch\b",
        r"\bfind\b",
        r"\blook\s+up\b",
        r"\bweb\s+research\b",
        r"\bsearch\s+for\b",
    ]
    return any(re.search(p, cmd) for p in patterns)


def _is_project_analysis_request(cmd: str) -> bool:
    markers = ["project risk", "risk analysis", "deadline risk", "status report", "project health"]
    return any(m in cmd for m in markers)


def _classify_intent(cmd: str) -> str:
    """
    Unit-like checks:
    - 'can you do a research on ai impact on health' -> research
    - 'create a work plan for a health company with web research' -> research_plan
    - 'project health report' with active project -> project_analysis
    """
    if _is_research_request(cmd) and ("plan" in cmd or "workflow" in cmd):
        return "research_plan"
    if _is_research_request(cmd):
        return "research"
    if _is_project_analysis_request(cmd) and get_active_project():
        return "project_analysis"
    if "open gmail" in cmd:
        return "open_gmail"
    if "summarise the last email" in cmd or "summarize the last email" in cmd or "read last email" in cmd:
        return "gmail_summary"
    if "open youtube" in cmd:
        return "open_youtube"
    if "open a new tab" in cmd or "new tab" == cmd.strip():
        return "open_new_tab"
    if _resolve_export_target(cmd):
        return "export_ref"
    return "default"

try:
    from voice.voice_io import listen_command, speak
except ImportError:
    def speak(text: str) -> None:
        print(f"[TTS] {text}")

    def listen_command() -> str:
        return "VOICE_ERROR: Module not found"


def has_images(files: List[Any]) -> bool:
    if not files:
        return False
    image_extensions = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff")
    for f in files:
        if isinstance(f, dict):
            mime = (f.get("type") or "").lower()
            name = (f.get("name") or "").lower()
            if mime.startswith("image/") or name.endswith(image_extensions):
                return True
        else:
            if str(f).lower().endswith(image_extensions):
                return True
    return False


def _task_sections(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not tasks:
        return []
    chunks = [tasks[:3], tasks[3:6], tasks[6:]]
    sections: List[Dict[str, Any]] = []
    for i, group in enumerate(chunks, start=1):
        if not group:
            continue
        sections.append(
            {
                "title": f"Phase {i}",
                "items": [f"{t.get('name', 'Task')} ({t.get('duration_days', 1)} day)" for t in group],
            }
        )
    return sections


def _is_greeting(cmd: str) -> bool:
    return cmd in {"hi", "hello", "hey", "yo", "good morning", "good afternoon", "good evening"}


def _needs_workflow_clarification(cmd: str) -> bool:
    wants_workflow = any(k in cmd for k in ("workflow", "automate", "automation", "work plan", "project plan"))
    has_target = any(k in cmd for k in ("for ", "company", "team", "department", "health", "finance", "retail"))
    return wants_workflow and not has_target


def _normalize_stt_text(text: str) -> tuple[str, List[str]]:
    original = text or ""
    normalized = original
    changes: List[str] = []
    lowered = normalized.lower()

    if "contry" in lowered:
        normalized = re.sub(r"\bcontry\b", "country", normalized, flags=re.IGNORECASE)
        changes.append("contry->country")

    if re.search(r"\bexport play\b", lowered):
        normalized = re.sub(r"\bexport play\b", "export plan", normalized, flags=re.IGNORECASE)
        changes.append("export play->export plan")

    ai_context = any(k in lowered for k in ("research", "sources", "impact", "technology", "tech", "ai"))
    if ai_context and re.search(r"\brise of i\b", lowered):
        normalized = re.sub(r"\brise of i\b", "rise of AI", normalized, flags=re.IGNORECASE)
        changes.append("rise of I->rise of AI")

    return normalized, changes


def _pending_from_response(resp: Dict[str, Any]) -> Dict[str, Any] | None:
    actions = [a for a in (resp.get("actions") or []) if isinstance(a, dict) and a.get("command")]
    question_line = ""
    show_text = (resp.get("show_text") or "").strip()
    if show_text.endswith("?"):
        question_line = show_text.splitlines()[-1].strip()
    if not actions and not question_line:
        return None
    return {
        "type": str(resp.get("meta", {}).get("intent") or "follow_up"),
        "question": question_line,
        "options": [{"label": str(a.get("label", "")).strip(), "command": str(a.get("command", "")).strip()} for a in actions],
        "default_command": str(actions[0].get("command", "")).strip() if actions else "",
    }


def _is_affirmative(cmd: str) -> bool:
    return cmd.strip().lower() in {"yes", "yeah", "yep", "ok", "okay", "do it", "go ahead", "sure"}


def _is_negative(cmd: str) -> bool:
    return cmd.strip().lower() in {"no", "nope", "cancel", "stop", "not now"}


def _match_pending_option(cmd: str, pending: Dict[str, Any]) -> str | None:
    text = cmd.strip().lower()
    options = pending.get("options") or []
    m = re.search(r"\boption\s*(\d+)\b", text)
    if m:
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(options):
            return str(options[idx].get("command", "")).strip() or None
    for option in options:
        label = str(option.get("label", "")).strip().lower()
        command = str(option.get("command", "")).strip().lower()
        if label and (text == label or label in text or any(tok in label for tok in text.split())):
            return str(option.get("command", "")).strip() or None
        if command and text in command:
            return str(option.get("command", "")).strip() or None
    return None


def _finalize_response(wf_session: Dict[str, Any], resp: Dict[str, Any], debug_updates: Dict[str, Any] | None = None) -> Dict[str, Any]:
    meta = resp.setdefault("meta", {})
    debug = meta.setdefault("debug", {})
    if debug_updates:
        debug.update(debug_updates)
    pending = _pending_from_response(resp)
    wf_session["pending"] = pending
    return resp


def _handle_command_core(text: str, files: List[Any] | None = None) -> Dict[str, Any]:
    cmd = (text or "").strip().lower()
    files = files or []
    state = _get_state()
    wf_session = _get_workflow_session()
    _update_state_from_text(state, text or "")
    if state.get("domain"):
        wf_session["context"]["domain"] = state["domain"]

    if _looks_cutoff(text):
        return make_response(summary="Go on - what should I do?", intent="cutoff")

    intent = _classify_intent(cmd)
    _log_intent(intent, text or "")

    if intent == "open_gmail":
        os_open_url("https://mail.google.com")
        return make_response(summary="Opened Gmail in your browser.", intent="open_gmail", say_text="Opened Gmail.")

    if intent == "gmail_summary":
        if not gmail_get_last_email or not gmail_summarize_email:
            return make_response(
                summary="I need Gmail access first.",
                bullets=[
                    "Install Gmail dependencies and add OAuth credentials.",
                    "Open the local setup guide for exact steps.",
                ],
                actions=[
                    {"label": "Setup Gmail", "command": "open gmail setup guide"},
                    {"label": "Skip Gmail", "command": "skip gmail"},
                ],
                intent="gmail_summary",
                say_text="I need Gmail access first.",
            )
        try:
            email = gmail_get_last_email()
            summary = gmail_summarize_email(email)
            return make_response(
                summary="I summarized your latest email.",
                bullets=[
                    f"From: {email.get('from', 'Unknown')}",
                    f"Subject: {email.get('subject', 'No subject')}",
                    summary,
                ],
                intent="gmail_summary",
                say_text="I summarized your latest email.",
            )
        except GmailSetupRequired:
            return make_response(
                summary="I need Gmail access first.",
                bullets=[
                    "Put credentials.json in the project root.",
                    "Run Gmail setup once, then retry.",
                    "Guide: /gmail_setup.html",
                ],
                actions=[
                    {"label": "Setup Gmail", "command": "open gmail setup guide"},
                    {"label": "Skip Gmail", "command": "skip gmail"},
                ],
                intent="gmail_summary",
                say_text="I need Gmail access first.",
            )
        except Exception:
            return make_response(
                summary="I could not read Gmail right now.",
                bullets=["Please retry in a moment."],
                intent="gmail_summary",
                say_text="I could not read Gmail right now.",
            )

    if "open gmail setup guide" in cmd:
        os_open_url("http://localhost:8000/gmail_setup.html")
        return make_response(summary="Opened Gmail setup guide.", intent="gmail_setup")

    if cmd == "skip gmail":
        return make_response(summary="Okay, Gmail skipped.", intent="gmail_skip", question="What should I do next")

    if "specify country for research" in cmd:
        return make_response(summary="Tell me the country and I will rerun research.", intent="research", question="Which country should I use")

    if intent == "open_youtube":
        os_open_url("https://www.youtube.com")
        return make_response(summary="Opened YouTube in your browser.", intent="open_youtube", say_text="Opened YouTube.")

    if intent == "open_new_tab":
        return make_response(
            summary="I can open the site in a new window. Which site should I open?",
            actions=[
                {"label": "Open Gmail", "command": "open gmail"},
                {"label": "Open YouTube", "command": "open youtube"},
                {"label": "Open Google", "command": "open google"},
            ],
            intent="open_new_tab",
            say_text="Which site should I open?",
        )

    if intent == "research":
        topic = _extract_research_topic(text)
        country_hint_missing = ("country" in cmd or "our country" in cmd) and not wf_session.get("context", {}).get("country")
        if country_hint_missing and ("our country" in cmd or " in " not in cmd):
            return make_response(
                summary="I can run that research, but I need the country first.",
                actions=[
                    {"label": "Botswana", "command": f"research {topic} in Botswana"},
                    {"label": "United States", "command": f"research {topic} in United States"},
                    {"label": "Specify country", "command": "specify country for research"},
                ],
                intent="research",
                say_text="Which country should I use for this research?",
                question="Which country should I focus on",
                debug={"source_count": 0, "research_reason": "country_missing"},
            )
        needs_evidence = ("attach evidence" in cmd or "with evidence" in cmd or "evidence" in cmd)
        research_payload = research_topic_with_wikipedia(topic, limit=6, request_evidence=needs_evidence)
        research_obj = _to_research_object(topic, research_payload)
        source_count = len(research_obj.get("sources", []))
        has_summary = bool((research_obj.get("summary") or "").strip())
        if source_count > 0 or has_summary:
            wf_session["last_research"] = research_obj
            wf_session["last_intent"] = "research"
        wf_session["context"]["topic"] = topic
        if "botswana" in topic.lower():
            wf_session["context"]["country"] = "Botswana"
        research_meta = research_payload.get("meta", {}) or {}
        if source_count < 3:
            reason = research_meta.get("reason", "insufficient_sources")
            reason_line = (
                "Research provider failed or timed out."
                if reason == "provider_failure"
                else "The query is too broad or unclear."
            )
            return make_response(
                summary="I could not gather enough reliable sources yet.",
                bullets=[reason_line, "I need one detail to improve source quality."],
                actions=[
                    {"label": "Retry research", "command": f"research {topic}"},
                    {"label": "Continue without sources", "command": f"continue without sources for {topic}"},
                    {"label": "Specify country", "command": f"research {topic} in Botswana"},
                ],
                intent="research",
                say_text="I need one more detail before I continue research.",
                question="Which country or sub-topic should I focus on",
                debug={"research_reason": reason, "source_count": source_count},
            )
        bullets = [
            f"I found {source_count} sources.",
            "I stored this research for follow-up exports.",
        ]
        if needs_evidence and not research_payload.get("evidence"):
            bullets.append("No reliable visuals found.")
        return make_response(
            summary=f"I researched {topic}.",
            bullets=bullets,
            sources=research_obj.get("sources", []),
            evidence=research_payload.get("evidence", []),
            actions=[
                {"label": "Export to Word", "command": "export that to word"},
                {"label": "Create PowerPoint", "command": "make a powerpoint from this"},
                {"label": "Export to Excel", "command": "export to excel"},
            ],
            intent="research",
            say_text="Research is ready.",
            debug={"source_count": source_count, "needs_evidence": needs_evidence},
        )

    if intent == "research_plan":
        enriched_text = text
        if state.get("compliance_level") and state["compliance_level"] not in cmd:
            enriched_text += f" with {state['compliance_level']} compliance"
        result = create_project_plan_from_web_request(enriched_text)
        project = result.get("project", {})
        tasks = result.get("tasks", [])
        sources = result.get("sources", [])
        evidence = result.get("evidence", [])
        image_evidence_count = sum(1 for e in evidence if (e.get("type") or "").lower() == "image")
        wf_session["last_research"] = {
            "topic": result.get("topic", project.get("name", "Research")),
            "summary": result.get("summary", ""),
            "key_points": [f"{s.get('title', '')}: {s.get('note', 'overview')}" for s in sources[:5]],
            "data_points": [],
            "sources": sources,
        }
        wf_session["last_intent"] = "research_plan"
        return make_response(
            summary=f'Created "{project.get("name", "Project")}" with a researched workflow plan.',
            bullets=[f"Generated {len(tasks)} tasks.", f"Attached {image_evidence_count} evidence image(s)."],
            sections=result.get("phases", []),
            sources=sources,
            evidence=evidence,
            actions=[
                {"label": "Export Plan", "command": "export plan"},
                {"label": "Refine Workflow", "command": "refine this workflow with compliance focus"},
                {"label": "Run Audit First", "command": "doctor"},
            ],
            intent="research_plan",
            say_text=(
                f"Your researched workflow is ready with {len(tasks)} tasks."
                if image_evidence_count == 0
                else f"Your researched workflow is ready with {len(tasks)} tasks and visual evidence."
            ),
            question="Do you want me to export this plan or refine it first",
        )

    if intent == "project_analysis":
        p = get_active_project()
        if not p:
            return make_response(summary="No active project available for analysis.", intent="project_analysis")
        diags = get_project_diagnosis(p["id"])
        return make_response(
            summary="I analyzed project risk and status.",
            bullets=[d for d in diags[:5]],
            intent="project_analysis",
            say_text="Project analysis is ready.",
        )

    if files and has_images(files):
        ai_text = chat_with_ai(text, files)
        return make_response(
            summary=ai_text,
            intent="vision_chat",
            say_text="I reviewed the images and prepared the answer.",
            question="Do you want a short summary or a task list",
        )

    if _is_greeting(cmd):
        return make_response(
            summary="Hi. I can help you plan workflows, research options, and generate task plans.",
            actions=[
                {"label": "Create Workflow", "command": "make a project workflow for a health company"},
                {"label": "Web Research Plan", "command": "create a work plan for a health company with web research"},
            ],
            intent="greeting",
            question="What should I help you build first",
        )

    if "help" in cmd or "what can you do" in cmd:
        return make_response(
            summary="I can create plans, run web research, and build task workflows.",
            bullets=[
                "Planning: create project, generate plan, check status.",
                "Research: build plans using web sources and visual evidence.",
                "System actions: open notes, word, excel, youtube.",
            ],
            actions=[
                {"label": "Plan Workflow", "command": "make a project workflow for a health company"},
                {"label": "Research + Plan", "command": "create a work plan for a health company with web research"},
            ],
            intent="help",
            question="Which option do you want to run",
        )

    if "what are you" in cmd or "who are you" in cmd:
        return make_response(
            summary="I am your planning assistant for workflows, research, and execution steps.",
            bullets=[
                "I create project workflows with phases and tasks.",
                "I research sources and attach evidence when useful.",
                "I give actionable next options you can run right away.",
            ],
            actions=[
                {"label": "Create Workflow", "command": "make a project workflow for a health company"},
                {"label": "Research Plan", "command": "create a work plan for a health company with web research"},
            ],
            intent="identity",
            question="Do you want a workflow draft or a researched plan",
        )

    if _needs_workflow_clarification(cmd) or ("workflow" in cmd and ("create" in cmd or "make" in cmd or "build" in cmd)):
        missing = []
        if not state.get("company_name"):
            missing.append("Which company or team is this for?")
        if not state.get("chosen_workflow_area"):
            missing.append("Which workflow area should I target?")
        if not state.get("goal"):
            missing.append("What is your primary goal for this workflow?")
        if not state.get("compliance_level"):
            missing.append("Any compliance level should I apply?")
        missing = missing[:2]
        if missing:
            domain = state.get("domain") or "health"
            if domain == "health":
                quick_actions = [
                    {"label": "Claims Workflow", "command": "build claims workflow for a health company with hipaa compliance"},
                    {"label": "Onboarding Workflow", "command": "build onboarding workflow for a health company"},
                ]
            else:
                quick_actions = [
                    {"label": "Operations Workflow", "command": f"build operations workflow for a {domain} company"},
                    {"label": "Compliance Workflow", "command": f"build compliance workflow for a {domain} company"},
                ]
            return make_response(
                summary="I can build that workflow, and I need a couple details first.",
                bullets=missing,
                actions=quick_actions,
                intent="clarify_workflow",
                question="Which option should I use",
            )

    if "open" in cmd:
        if "youtube" in cmd:
            return make_response(summary=open_url("https://www.youtube.com"), intent="open_url")
        if "note" in cmd or "notepad" in cmd:
            return make_response(summary=open_notes(), intent="open_app")
        if "word" in cmd:
            return make_response(summary=open_word(), intent="open_app")
        if "excel" in cmd:
            return make_response(summary=open_excel(), intent="open_app")
        if "url" in cmd or "browser" in cmd or "google" in cmd:
            return make_response(summary=open_url("https://www.google.com"), intent="open_url")

    if "minimize" in cmd or "hide windows" in cmd:
        return make_response(summary=minimize_all_windows(), intent="system")

    if "learn" in cmd and "youtube" in cmd:
        result = learn_from_youtube(text)
        if not result.get("ok"):
            return make_response(summary=result.get("message", "Could not process this YouTube request."), intent="learning")
        return make_response(
            summary=f"I learned from {result.get('title', 'the video')}.",
            bullets=["I extracted key lessons and action steps.", "I can convert this into a project workflow next."],
            intent="youtube_learning",
            say_text="I finished learning from the video and prepared the key takeaways.",
            question="Do you want this turned into a workflow",
        )

    export_target = _resolve_export_target(cmd)
    export_ref = (
        any(k in cmd for k in ("that", "this", "it", "research", "from this", "use the research"))
        or cmd.startswith("export to ")
        or cmd.startswith("make a powerpoint")
        or cmd.startswith("make powerpoint")
    )
    if export_target and export_ref:
        research_obj = wf_session.get("last_research")
        if not research_obj:
            return make_response(summary="What should I research first?", intent="export")
        try:
            if export_target == "docx":
                fmeta = export_docx_from_research(research_obj)
            elif export_target == "pptx":
                fmeta = export_pptx_from_research(research_obj)
            else:
                fmeta = export_xlsx_from_research(research_obj)
        except (ModuleNotFoundError, MissingExportDependencyError) as e:
            missing = str(e).strip() or "export dependency"
            return make_response(
                summary=f"Export is not available until I install {missing}.",
                bullets=[f"Run: pip install {missing}", "Then retry your export command."],
                intent="export",
                say_text=f"Export is not available until I install {missing}.",
            )
        wf_session["last_files"] = [fmeta]
        wf_session["artifacts"].append({"id": fmeta["id"], "name": fmeta["name"], "type": fmeta["type"]})
        wf_session["last_intent"] = f"export_{export_target}"
        return make_response(
            summary=f"{fmeta['type'].upper()} export is ready.",
            bullets=[f"Created {fmeta['name']}."],
            files=[fmeta],
            intent=f"export_{export_target}",
            say_text="Your export is ready for download.",
        )

    if "create" in cmd and "project" in cmd:
        name = cmd
        for prefix in ["create project", "new project", "create a project"]:
            if prefix in cmd:
                name = text.lower().replace(prefix, "", 1).strip()
                break
        name = name.title() or "Untitled Project"
        p = create_project(name=name)
        if not state.get("company_name"):
            state["company_name"] = name
        return make_response(
            summary=f'Created project "{p["name"]}".',
            actions=[{"label": "Generate Plan", "command": "generate plan"}],
            intent="create_project",
            say_text="Project created.",
            question="Do you want me to generate the first workflow now",
        )

    if "plan" in cmd and ("generate" in cmd or "make" in cmd or "create" in cmd):
        p = get_active_project()
        if not p:
            return make_response(summary="No active project found.", bullets=["Create a project first."], intent="plan")
        tasks = generate_plan(p, use_ai=True)
        save_tasks(p["id"], tasks)
        return make_response(
            summary=f'Generated {len(tasks)} tasks for "{p["name"]}".',
            sections=_task_sections(tasks),
            actions=[
                {"label": "Show Status", "command": "status"},
                {"label": "Export Plan", "command": "export plan"},
            ],
            intent="plan",
            say_text=f"I generated {len(tasks)} tasks.",
            question="Do you want timeline status next",
        )

    if "status" in cmd or "progress" in cmd or "list tasks" in cmd:
        p = get_active_project()
        if not p:
            return make_response(summary="No active project.", intent="status")
        s = get_status(p)
        return make_response(summary=s["message"], intent="status", question="Do you want a detailed task breakdown")

    if "doctor" in cmd or "diagnose" in cmd:
        p = get_active_project()
        if not p:
            return make_response(summary="No active project.", intent="diagnostics")
        diags = get_project_diagnosis(p["id"])
        return make_response(
            summary="I reviewed project risk and health status.",
            bullets=[d for d in diags[:5]],
            intent="diagnostics",
            question="Do you want mitigation actions for the top risks",
        )

    if "done" in cmd or "finish" in cmd or "complete" in cmd:
        match = re.search(r"\b(t\d+)\b", cmd)
        if not match:
            return make_response(summary="Please specify a task ID, for example: mark t1 done.", intent="task_update")
        ok, msg = mark_task_done(match.group(1))
        return make_response(summary=msg, intent="task_update")

    if "delay" in cmd:
        t_match = re.search(r"\b(t\d+)\b", cmd)
        d_match = re.search(r"\b(\d+)\b", cmd)
        if not (t_match and d_match):
            return make_response(summary="Use: delay task t1 by 2 days.", intent="task_update")
        ok, msg = delay_task(t_match.group(1), int(d_match.group(1)))
        return make_response(summary=msg, intent="task_update")

    if "export" in cmd or "save" in cmd:
        p = get_active_project()
        if not p:
            return make_response(summary="No active project.", intent="export")
        if "excel" in cmd or "schedule" in cmd:
            s = get_status(p)
            try:
                path = export_schedule_to_excel(p, s["schedule"])
            except ModuleNotFoundError:
                return make_response(
                    summary="Export is not available until I install openpyxl.",
                    bullets=["Run: pip install openpyxl"],
                    intent="export",
                    say_text="Export is not available until I install openpyxl.",
                )
            return make_response(summary=f"Schedule exported successfully.", bullets=[f"Saved to: {path}"], intent="export")
        try:
            path = export_plan_to_word(p)
        except ModuleNotFoundError:
            return make_response(
                summary="Export is not available until I install python-docx.",
                bullets=["Run: pip install python-docx"],
                intent="export",
                say_text="Export is not available until I install python-docx.",
            )
        return make_response(summary="Plan exported successfully.", bullets=[f"Saved to: {path}"], intent="export")

    # Chat fallback
    ai_text = chat_with_ai(text, files=[])
    return make_response(summary=ai_text, intent="chat", question="Do you want me to turn this into a task plan")


def handle_command(text: str, files: List[Any] | None = None) -> Dict[str, Any]:
    files = files or []
    wf_session = _get_workflow_session()
    pending = wf_session.get("pending")
    normalized_text, corrections = _normalize_stt_text(text or "")
    cmd = normalized_text.strip().lower()

    if pending:
        if _is_negative(cmd):
            wf_session["pending"] = None
            resp = make_response(
                summary="Okay, canceled.",
                intent="pending_cancel",
                say_text="Okay, canceled.",
                question="What should I do next",
            )
            return _finalize_response(wf_session, resp, {"stt_corrections": corrections} if corrections else None)

        selected = _match_pending_option(cmd, pending)
        if selected:
            wf_session["pending"] = None
            resp = _handle_command_core(selected, files)
            return _finalize_response(wf_session, resp, {"resolved_from_pending": selected, "stt_corrections": corrections})

        if _is_affirmative(cmd):
            default_command = str(pending.get("default_command", "")).strip()
            if default_command:
                wf_session["pending"] = None
                resp = _handle_command_core(default_command, files)
                return _finalize_response(
                    wf_session,
                    resp,
                    {"resolved_from_pending": default_command, "stt_corrections": corrections},
                )

    if _is_affirmative(cmd):
        resp = make_response(
            summary="I do not have a pending action yet.",
            intent="pending_none",
            say_text="I do not have a pending action yet.",
            question="What should I do",
        )
        return _finalize_response(wf_session, resp, {"stt_corrections": corrections} if corrections else None)

    resp = _handle_command_core(normalized_text, files)
    debug_updates: Dict[str, Any] = {}
    if corrections:
        debug_updates["stt_corrections"] = corrections
        debug_updates["normalized_text"] = normalized_text
    return _finalize_response(wf_session, resp, debug_updates if debug_updates else None)


if __name__ == "__main__":
    import sys

    mode = "voice" if len(sys.argv) > 1 and sys.argv[1] == "--voice" else "cli"
    print(f"Assistant ({mode.upper()} mode). Ctrl+C to exit.")
    if mode == "voice":
        speak("Assistant online.")

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
                if text.lower() in ("exit", "quit"):
                    speak("Goodbye.")
                    break
                result = handle_command(text)
                print(result.get("show_text", ""))
                speak(result.get("say_text", ""))
            else:
                text = input("> ")
                if text.lower() in ("exit", "quit"):
                    break
                result = handle_command(text)
                print(result.get("show_text", ""))
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
