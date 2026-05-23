import os
import sys
import json
import re
from typing import Optional, Tuple, List, Dict
import asyncio
import threading
import requests
from mcp.server.fastmcp import FastMCP
from sentence_transformers import SentenceTransformer, util
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

mcp = FastMCP("Syntiox-Master-Router")

LM_STUDIO_MODEL = os.environ.get("LM_STUDIO_MODEL", "ceylex-4-e2b-it")
LM_STUDIO_URL = os.environ.get("LM_STUDIO_URL", "http://localhost:1234/v1/chat/completions")
MAX_STEPS = int(os.environ.get("SYNTHIOX_MAX_STEPS", "8"))
ROUTING_THRESHOLD = float(os.environ.get("SYNTHIOX_ROUTING_THRESHOLD", "0.55"))
LM_TIMEOUT = int(os.environ.get("SYNTHIOX_LM_TIMEOUT", "45"))
USE_LM_PLANNER = os.environ.get("SYNTHIOX_USE_LM_PLANNER", "").strip() in ("1", "true", "yes")

# Categories that only fetch data — can run in parallel before action steps
GATHER_CATEGORIES = frozenset({"sri_news", "weather", "google_news", "search", "system"})

CATEGORIES = {
    "clipboard": {"script": "clipboard_mcp.py", "description": "passage: Clipboard read write clear."},
    "filesystem": {"script": "file_mcp.py", "description": "passage: Local files folders read write search."},
    "reminder": {"script": "reminder_mcp.py", "description": "passage: Windows reminders notifications."},
    "screenshot": {"script": "screenshot_mcp.py", "description": "passage: Screen capture screenshots."},
    "search": {"script": "search_mcp.py", "description": "passage: DuckDuckGo web search."},
    "sri_news": {"script": "sri_news_mcp.py", "description": "passage: Sri Lanka Sinhala news Esena."},
    "system": {"script": "system_mcp.py", "description": "passage: Windows CPU RAM volume brightness processes."},
    "weather": {"script": "weather_mcp.py", "description": "passage: Weather temperature forecast city."},
    "calendar": {"script": "google/calendar_handlers.py", "description": "passage: Google Calendar events schedule."},
    "docs": {"script": "google/docs_handlers.py", "description": "passage: Google Docs read write edit."},
    "drive": {"script": "google/drive_handlers.py", "description": "passage: Google Drive files upload download."},
    "forms": {"script": "google/forms_handlers.py", "description": "passage: Google Forms surveys."},
    "gmail": {"script": "google/gmail_handlers.py", "description": "passage: Gmail send read email mail."},
    "google_news": {"script": "google/google_news_handlers.py", "description": "passage: International English Google News RSS."},
    "sheets": {"script": "google/sheets_handlers.py", "description": "passage: Google Sheets cells spreadsheet edit."},
    "slides": {"script": "google/slides_handlers.py", "description": "passage: Google Slides presentation."},
    "tasks": {"script": "google/tasks_handlers.py", "description": "passage: Google Tasks todo list."},
}

print("Loading embedding model (intfloat/multilingual-e5-small)...", file=sys.stderr)
try:
    model = SentenceTransformer('intfloat/multilingual-e5-small')
    print("Model loaded successfully!", file=sys.stderr)
except Exception as e:
    print(f"Model load failed: {e}", file=sys.stderr)
    sys.exit(1)

category_names = list(CATEGORIES.keys())
descriptions = [CATEGORIES[name]["description"] for name in category_names]
category_embeddings = model.encode(descriptions, convert_to_tensor=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VALID_CATEGORIES = set(category_names)


def _run_async(coro):
    result_holder = {}
    def _thread_target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result_holder["value"] = loop.run_until_complete(coro)
        except Exception as exc:
            result_holder["error"] = exc
        finally:
            loop.close()

    t = threading.Thread(target=_thread_target)
    t.start()
    t.join()
    if "error" in result_holder:
        raise result_holder["error"]
    return result_holder.get("value")


async def execute_tool_on_server(script_path: str, tool_name: str, args: dict):
    full_path = os.path.join(BASE_DIR, script_path)
    params = StdioServerParameters(command=sys.executable, args=[full_path])
    try:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, args)
                if result and result.content:
                    return "\n".join(
                        c.text for c in result.content if getattr(c, "type", "") == "text"
                    )
                return "Tool executed successfully (empty result)."
    except Exception as e:
        return f"Tool execution error: {e}"


async def fetch_tools_from_server(script_path: str):
    full_path = os.path.join(BASE_DIR, script_path)
    params = StdioServerParameters(command=sys.executable, args=[full_path])
    try:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                return result.tools
    except Exception as e:
        print(f"Error fetching tools from {script_path}: {e}", file=sys.stderr)
        return None


def _run_tool(script: str, tool_name: str, args: dict) -> str:
    return _run_async(execute_tool_on_server(script, tool_name, args))


def _extract_email(text: str) -> Optional[str]:
    m = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    return m.group(0) if m else None


def _weather_location(instruction: str) -> str:
    text = instruction.lower()
    for city, label in [
        ("kandy", "Kandy, Sri Lanka"),
        ("galle", "Galle, Sri Lanka"),
        ("jaffna", "Jaffna, Sri Lanka"),
        ("negombo", "Negombo, Sri Lanka"),
    ]:
        if city in text:
            return label
    return "Colombo, Sri Lanka"


def _search_query_from_instruction(instruction: str) -> str:
    m = re.search(r"(?:search|හොය|find)\s+(.+?)(?:\s+and\s+|\s*[,;]|\s+then\s+|$)", instruction, re.I)
    if m:
        return m.group(1).strip()[:200]
    return instruction.strip()[:120]


def _parse_json_from_ai(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        parts = cleaned.split("```")
        cleaned = parts[1] if len(parts) > 1 else cleaned
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    return json.loads(cleaned.strip())


def _call_lm_studio(system_prompt: str, user_prompt: str) -> str:
    payload = {
        "model": LM_STUDIO_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "tool_choice": "none",
    }
    response = requests.post(LM_STUDIO_URL, json=payload, timeout=LM_TIMEOUT)
    if response.status_code != 200:
        raise RuntimeError(f"LM Studio HTTP {response.status_code}: {response.text}")
    data = response.json()
    if "choices" not in data:
        raise RuntimeError(f"No 'choices' in LM Studio response: {data}")
    return data["choices"][0]["message"]["content"].strip()


def _match_category_semantic(instruction: str) -> Tuple[str, float]:
    query_embedding = model.encode(f"query: {instruction}", convert_to_tensor=True)
    similarities = util.cos_sim(query_embedding, category_embeddings)[0]
    best_idx = similarities.argmax().item()
    return category_names[best_idx], similarities[best_idx].item()


def _detect_category_in_text(text: str) -> List[str]:
    """Return categories implied by keywords (order preserved, no duplicates)."""
    t = text.lower()
    found: List[str] = []

    def add(cat: str):
        if cat not in found:
            found.append(cat)

    sri_markers = ["ලංකා", "lanka", "sri lanka", "ශ්‍රී", "sinhala", "esena", "ලංකාව", "ලංකාවෙ"]
    news_markers = ["news", "පුවත්", "නිවුස්", "nivus", "headline"]
    if any(m in t for m in news_markers):
        if any(m in t for m in sri_markers):
            add("sri_news")
        elif any(m in t for m in ["world", "international", "global", "english news"]):
            add("google_news")
        else:
            add("sri_news")

    if any(m in t for m in ["weather", "කාලගුණ", "වෙදර්", "temperature", "forecast", "rain"]):
        add("weather")
    if any(m in t for m in ["search", "හොය", "google ", "duckduck", "browse web"]):
        add("search")
    if any(m in t for m in ["cpu", "ram", "system", "battery", "volume", "brightness", "process"]):
        add("system")
    if any(m in t for m in ["calendar", "event", "meeting", "schedule", "appointment", "රැස්වීම"]):
        add("calendar")
    if any(m in t for m in ["sheet", "spreadsheet", "excel", "cell"]):
        add("sheets")
    if any(m in t for m in ["doc", "document", "google doc"]):
        add("docs")
    if any(m in t for m in ["drive", "upload", "folder"]):
        add("drive")
    if any(m in t for m in ["slide", "presentation", "powerpoint"]):
        add("slides")
    if any(m in t for m in ["task", "todo", "to-do", "කාර්ය"]):
        add("tasks")
    if any(m in t for m in ["form", "survey", "ප්‍රශ්නාවලිය"]):
        add("forms")
    if any(m in t for m in ["clipboard", "copy", "paste"]):
        add("clipboard")
    if any(m in t for m in ["screenshot", "screen capture"]):
        add("screenshot")
    if any(m in t for m in ["remind", "notification", "alarm"]):
        add("reminder")
    if any(m in t for m in ["file", "folder", "directory", "read file", "write file"]):
        add("filesystem")
    if _extract_email(text) or any(m in t for m in ["mail", "email", "gmail", "ඊමේල්", "e-mail", "send to"]):
        add("gmail")

    return found


def _heuristic_plan(instruction: str) -> Optional[List[Dict]]:
    """
    Build multi-step plan from keywords — works for ANY combo (not one fixed workflow).
    Order: data-gather steps first, then actions (gmail, calendar, ...).
    """
    cats = _detect_category_in_text(instruction)
    if not cats:
        return None

  # Re-order: gather → actions
    gather = [c for c in cats if c in GATHER_CATEGORIES]
    actions = [c for c in cats if c not in GATHER_CATEGORIES]
    ordered = gather + actions

    if len(ordered) < 2:
        return None

    steps = [{"category": c, "instruction": instruction} for c in ordered[:MAX_STEPS]]
    return steps


def _email_subject(instruction: str) -> str:
    if re.search(r"news|පුවත්|නිවුස්", instruction, re.I):
        return "Update: News & Information"
    return "Syntiox automated update"


def _direct_tool(
    category: str,
    full_instruction: str,
    prior_results: str,
) -> Optional[Tuple[str, dict]]:
    """Direct tool mapping — no LM Studio (fast). Returns None if step needs LM."""
    if category == "sri_news":
        return ("get_latest_news", {})
    if category == "weather":
        return ("get_weather", {"location": _weather_location(full_instruction)})
    if category == "google_news":
        return ("get_google_top_news", {"max_results": 10})
    if category == "search":
        return ("web_search", {"query": _search_query_from_instruction(full_instruction), "max_results": 5})
    if category == "system":
        return ("get_system_stats", {})
    if category == "clipboard":
        return ("get_clipboard", {})
    if category == "calendar":
        return ("list_upcoming_events", {"days": 7})
    if category == "tasks":
        return ("list_tasks", {"tasklist_id": "@default", "show_completed": False})
    if category == "sheets":
        return ("list_spreadsheets", {"max_results": 5})
    if category == "docs":
        return ("list_documents", {"max_results": 5})
    if category == "drive":
        return ("list_drive_files", {"max_results": 10})
    if category == "gmail":
        to_email = _extract_email(full_instruction)
        if not to_email:
            return None
        body = prior_results.strip() if prior_results else full_instruction
        if len(body) > 48000:
            body = body[:48000] + "\n...(truncated)"
        return (
            "send_gmail_email",
            {
                "to_email": to_email,
                "subject": _email_subject(full_instruction),
                "email_body": body,
            },
        )
    return None


async def _run_gather_parallel(steps: List[Dict], full_instruction: str) -> Dict[str, str]:
    async def one_step(step: Dict):
        cat = step["category"]
        script = CATEGORIES[cat]["script"]
        direct = _direct_tool(cat, full_instruction, "")
        if not direct:
            return cat, f"(skipped — no direct tool for {cat})"
        tool_name, args = direct
        result = await execute_tool_on_server(script, tool_name, args)
        return cat, result

    pairs = await asyncio.gather(*[one_step(s) for s in steps])
    return dict(pairs)


def _fast_multi_step_pipeline(instruction: str, steps: List[Dict]) -> Optional[str]:
    """
    Generic fast executor: parallel gather steps, then sequential action steps.
    Works for news+weather+mail, news+mail, weather+system+mail, etc.
    """
    if len(steps) < 2:
        return None

    gather_steps = [s for s in steps if s["category"] in GATHER_CATEGORIES]
    action_steps = [s for s in steps if s["category"] not in GATHER_CATEGORIES]

    for s in action_steps:
        if _direct_tool(s["category"], instruction, "placeholder") is None:
            print(f"[Router] Fast path skip: no direct tool for action '{s['category']}'", file=sys.stderr)
            return None

    print(
        f"[Router] ⚡ FAST multi-step: {len(gather_steps)} gather (parallel) + "
        f"{len(action_steps)} action(s)",
        file=sys.stderr,
    )

    prior_parts: List[str] = []
    lines = [
        f"⚡ Multi-step workflow ({len(steps)} steps, no LM routing)\n"
        f"{'═' * 40}",
    ]

    if gather_steps:
        try:
            results = _run_async(_run_gather_parallel(gather_steps, instruction))
        except Exception as e:
            return f"❌ Gather phase failed: {e}"
        for cat in [s["category"] for s in gather_steps]:
            lines.append(f"\n▶ {cat} (parallel)\n{'─' * 30}")
            block = results.get(cat, "(no data)")
            lines.append(block)
            prior_parts.append(f"=== {cat.upper()} ===\n{block}")

    prior = "\n\n".join(prior_parts)

    for i, step in enumerate(action_steps, 1):
        cat = step["category"]
        lines.append(f"\n▶ Step action {i}: {cat}\n{'─' * 30}")
        try:
            result = _execute_step(cat, step["instruction"], instruction, prior)
            lines.append(result)
            prior += f"\n\n=== {cat} ===\n{result}"
        except Exception as e:
            lines.append(f"❌ Failed: {e}")
            break

    return "\n".join(lines)


def _plan_steps(instruction: str) -> List[Dict]:
    heuristic = _heuristic_plan(instruction)
    if heuristic:
        print(f"[Router] Heuristic plan ({len(heuristic)} steps): {[s['category'] for s in heuristic]}", file=sys.stderr)
        return heuristic

    if USE_LM_PLANNER:
        try:
            category_list = ", ".join(category_names)
            system_prompt = (
                "Split the user request into ordered steps. Each step one category from: "
                f"{category_list}. Gather data before send-email actions. "
                'Output ONLY JSON: {"steps":[{"category":"...","instruction":"..."}]}'
            )
            raw = _call_lm_studio(system_prompt, instruction)
            parsed = _parse_json_from_ai(raw)
            validated = []
            for s in parsed.get("steps", [])[:MAX_STEPS]:
                cat = s.get("category", "").strip()
                if cat in VALID_CATEGORIES:
                    validated.append({"category": cat, "instruction": s.get("instruction", instruction)})
            if validated:
                return validated
        except Exception as e:
            print(f"[Router] LM planner failed: {e}", file=sys.stderr)

    cat, score = _match_category_semantic(instruction)
    if score >= ROUTING_THRESHOLD:
        return [{"category": cat, "instruction": instruction}]
    return []


def _pick_tool_with_lm(category, step_instruction, full_instruction, prior_results, tools):
    tools_context = [
        {"name": t.name, "description": t.description, "parameters": t.inputSchema.get("properties", {})}
        for t in tools
    ]
    ctx = f"\nPrior results:\n{prior_results}\n" if prior_results else ""
    system_prompt = (
        "Pick ONE tool. Output ONLY JSON {\"tool_name\":\"...\",\"args\":{...}}\n"
        f"Tools:\n{json.dumps(tools_context, indent=2)}"
    )
    user_prompt = f"Request: {full_instruction}\nStep ({category}): {step_instruction}{ctx}"
    ai_result = _call_lm_studio(system_prompt, user_prompt)
    parsed = _parse_json_from_ai(ai_result)
    return parsed.get("tool_name"), parsed.get("args", {})


def _execute_step(category: str, step_instruction: str, full_instruction: str, prior_results: str) -> str:
    script = CATEGORIES[category]["script"]
    direct = _direct_tool(category, full_instruction, prior_results)
    if direct:
        tool_name, args = direct
        print(f"[Router] Direct [{category} › {tool_name}]", file=sys.stderr)
    else:
        tools = _run_async(fetch_tools_from_server(script))
        if not tools:
            return f"Could not connect to '{category}' ({script})."
        tool_name, args = _pick_tool_with_lm(
            category, step_instruction, full_instruction, prior_results, tools
        )
        print(f"[Router] LM pick [{category} › {tool_name}]", file=sys.stderr)
    return _run_tool(script, tool_name, args)


@mcp.tool()
def syntiox_gateway(instruction: str) -> str:
    """
    Universal Syntiox gateway — MULTI-STEP workflows (any combination).

    Examples in one message:
    - Sri Lanka news + weather + email to someone@gmail.com
    - news + system stats + mail
    - weather + calendar + tasks (each step runs in order)

    Uses fast path when possible (no LM Studio). Keyword planner detects all parts.
    """
    instruction = instruction.strip()
    if not instruction:
        return "Please provide an instruction."

    steps = _plan_steps(instruction)
    if not steps:
        return "Could not match this request. Try naming services: news, weather, email, sheets, calendar, etc."

    if len(steps) >= 2:
        fast = _fast_multi_step_pipeline(instruction, steps)
        if fast:
            return fast

    lines = [f"Running {len(steps)} step(s).\n{'═' * 40}"]
    prior = ""
    for i, step in enumerate(steps, 1):
        cat = step["category"]
        lines.append(f"\n▶ Step {i}/{len(steps)}: {cat}\n{'─' * 40}")
        try:
            result = _execute_step(cat, step["instruction"], instruction, prior)
            lines.append(result)
            prior += f"\n\n--- {cat} ---\n{result}"
        except Exception as e:
            lines.append(f"❌ Step {i} failed: {e}")
            break
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport='stdio')
