# Syntiox MCP Tools

> **Model Context Protocol (MCP)** server collection for **Cursor**, **Claude Desktop**, and **LM Studio** on Windows.  
> Local PC control, Google Workspace (Gmail, Sheets, Docs, Drive, Calendar, …), weather, news, and more.

---

## Project structure

```
MCP/
├── credentials.json            ← Google OAuth client (from Cloud Console; do not commit)
├── requirements.txt
├── master_router.py            ← Optional: one gateway → all categories (needs LM Studio)
│
├── clipboard_mcp.py
├── file_mcp.py
├── reminder_mcp.py
├── screenshot_mcp.py
├── search_mcp.py               ← DuckDuckGo web search
├── sri_news_mcp.py             ← Sri Lanka Sinhala news (Esena)
├── system_mcp.py
├── weather_mcp.py
├── python_sandbox_mcp.py
│
└── google/
    ├── google_common.py        ← Shared auth (auto-refresh), Drive share helpers
    ├── auth_setup.py           ← One-time Google login → token.json
    ├── token.json              ← Generated after auth_setup (do not commit)
    │
    ├── gmail_handlers.py       ← 9 tools
    ├── calendar_handlers.py    ← 13 tools
    ├── drive_handlers.py       ← 18 tools
    ├── docs_handlers.py          ← 16 tools
    ├── sheets_handlers.py      ← 21 tools
    ├── slides_handlers.py      ← 16 tools
    ├── tasks_handlers.py       ← 14 tools
    ├── forms_handlers.py       ← 14 tools
    └── google_news_handlers.py ← 3 tools (RSS, no OAuth)
```

**Total Google tools: ~124** (each `*_handlers.py` is a **standalone** MCP server).

---

## Quick setup

### 1. Install dependencies

```bash
cd d:\01_PROJECTS\Tools\MCP
pip install -r requirements.txt
```

### 2. Google OAuth (once)

```bash
# Copy template → fill from Google Cloud Console (never commit real file)
copy credentials.json.example credentials.json
python google/auth_setup.py
```

This creates `google/token.json`. All Google handler scripts use the same token.

If Gmail shows `invalid_scope` for `forms.responses`, delete the old token and re-login (that scope was removed — Google does not support it):

```powershell
Remove-Item google\token.json -ErrorAction SilentlyContinue
python google\auth_setup.py
```

### 3. Register MCP servers in your client

See [How to connect](#how-to-connect-mcp) below — you choose **per-service** and/or **master router**.

---

## How to connect MCP

Each `.py` MCP server runs on its own via `python path/to/script.py` (stdio).  
**You only add the servers you need** — Gmail alone works without Sheets, Docs, etc.

### Option A — Separate handlers (recommended)

Register only the scripts you want. The agent sees **real tool names** directly (`update_single_cell`, `send_gmail_email`, …).

**Cursor** — edit MCP config (e.g. `.cursor/mcp.json` or Settings → MCP):

```json
{
  "mcpServers": {
    "google-gmail": {
      "command": "python",
      "args": ["d:/01_PROJECTS/Tools/MCP/google/gmail_handlers.py"]
    },
    "google-sheets": {
      "command": "python",
      "args": ["d:/01_PROJECTS/Tools/MCP/google/sheets_handlers.py"]
    },
    "google-docs": {
      "command": "python",
      "args": ["d:/01_PROJECTS/Tools/MCP/google/docs_handlers.py"]
    },
    "google-drive": {
      "command": "python",
      "args": ["d:/01_PROJECTS/Tools/MCP/google/drive_handlers.py"]
    },
    "google-calendar": {
      "command": "python",
      "args": ["d:/01_PROJECTS/Tools/MCP/google/calendar_handlers.py"]
    },
    "google-forms": {
      "command": "python",
      "args": ["d:/01_PROJECTS/Tools/MCP/google/forms_handlers.py"]
    },
    "google-slides": {
      "command": "python",
      "args": ["d:/01_PROJECTS/Tools/MCP/google/slides_handlers.py"]
    },
    "google-tasks": {
      "command": "python",
      "args": ["d:/01_PROJECTS/Tools/MCP/google/tasks_handlers.py"]
    },
    "google-news": {
      "command": "python",
      "args": ["d:/01_PROJECTS/Tools/MCP/google/google_news_handlers.py"]
    },
    "syntiox-system": {
      "command": "python",
      "args": ["d:/01_PROJECTS/Tools/MCP/system_mcp.py"]
    }
  }
}
```

| Need only… | Add this file |
|------------|----------------|
| Email | `google/gmail_handlers.py` |
| Spreadsheets / cell edit | `google/sheets_handlers.py` |
| Documents | `google/docs_handlers.py` |
| Files in Drive | `google/drive_handlers.py` |
| Calendar | `google/calendar_handlers.py` |
| Forms / surveys | `google/forms_handlers.py` |
| Presentations | `google/slides_handlers.py` |
| To-do lists | `google/tasks_handlers.py` |

Paths: use your real project path; forward slashes work on Windows.

**Claude Desktop** — same JSON under `%APPDATA%\Claude\claude_desktop_config.json` → `mcpServers`.

### Option B — Master router (single entry)

One server, one tool: `syntiox_gateway(instruction)`.

```json
{
  "mcpServers": {
    "syntiox-router": {
      "command": "python",
      "args": ["d:/01_PROJECTS/Tools/MCP/master_router.py"]
    }
  }
}
```

**Requirements:**

- LM Studio (or compatible) API at `http://localhost:1234/v1/chat/completions`
- Env optional: `LM_STUDIO_MODEL` (default `ceylex-4-e2b-it`)
- `sentence-transformers` for routing (installed via requirements)

Flow: your message → **planner splits into 1–N steps** → each step runs the right handler → local LLM picks tool + args → results chain to the next step (e.g. news + weather → email body).

**Multi-step example** (news + weather + email):

> අලුත් ලංකාවෙ නිවුස් බලලා ලංකාවෙ වෙදර් එකත් චෙක් කරලා මගෙ mail එකට දාන්න your.name@gmail.com

Use **`syntiox_gateway`** with natural language — it detects **any combination** of services (news + weather + mail, news + system + mail, calendar + tasks, etc.), not one fixed workflow.

Fast path (no LM Studio): when all steps have direct tool mappings, gather steps (news, weather, search, …) run **in parallel**, then action steps (gmail, calendar, …) run in order.

Examples in one message:
- ලංකා නිවුස් + වෙදර් + mail to `you@gmail.com`
- world news + weather + email
- system stats + email

If you see `MCP error -32001: Request timed out`, increase MCP timeout in LM Studio or register fewer heavy servers.

Optional env: `SYNTHIOX_USE_LM_PLANNER=1`, `SYNTHIOX_MAX_STEPS` (default 8).

Use Option A if you want reliable direct tool calls in Cursor; use Option B for one natural-language gateway with chained tasks.

### Test a handler alone

```bash
python google/sheets_handlers.py
```

(Starts stdio MCP — normally your IDE spawns this; useful to confirm imports/auth.)

---

## Google Workspace tools (summary)

Shared auth: `google/token.json` via [`google/google_common.py`](google/google_common.py) (auto-refresh on expiry).

### Gmail — `gmail_handlers.py` (9)

| Tool | Purpose |
|------|---------|
| `list_latest_emails` | Inbox list |
| `send_gmail_email` | Send plain text |
| `send_email_with_attachment` | Send with file |
| `search_emails` | Gmail search query |
| `get_email_body` | Full body |
| `reply_to_email` | Reply in thread |
| `mark_email_as_read` | Mark read |
| `delete_email` | Trash |
| `list_email_labels` | Labels |

### Calendar — `calendar_handlers.py` (13)

List/create/**update**/delete events, get by ID, date range, all-day, attendees, reminders, duplicate, move between calendars, search.

Key tools: `update_calendar_event`, `get_calendar_event`, `list_events_date_range`, `add_event_attendees`.

### Drive — `drive_handlers.py` (18)

List, search, upload, **download**, **export**, rename, move, copy, share, permissions, trash/restore, shortcut, shared-with-me, storage quota.

### Docs — `docs_handlers.py` (16)

Read, create, append, **insert/replace/delete text**, headings, tables, structure outline, export PDF/DOCX, share, rename, trash.

### Sheets — `sheets_handlers.py` (21)

Read/write, **`update_single_cell`**, batch read/write, append row, clear, find/replace, **tabs** add/delete/rename/duplicate, **format** (bold/color), sort, auto-resize columns, copy/share/delete spreadsheet.

### Slides — `slides_handlers.py` (16)

Create, read text, add slide, **update/delete/duplicate/reorder** slides, image slide, bullets, background color, export PDF/PPTX, share.

### Tasks — `tasks_handlers.py` (14)

Lists, create, **`update_task`**, complete, **uncomplete**, delete, move between lists, rename/delete lists, search, clear completed.

### Forms — `forms_handlers.py` (14)

Create, info, responses, add text/choice/checkbox questions, update title, delete/reorder questions, **clear responses**, responder URL, duplicate, delete form.

### Google News — `google_news_handlers.py` (3)

RSS headlines (English); no Google login.

---

## Other MCP servers

### Clipboard — `clipboard_mcp.py`

`get_clipboard`, `set_clipboard`, `clear_clipboard`

### File system — `file_mcp.py`

`read_file`, `write_file`, `list_directory`, `search_files`, `get_file_info`, `delete_file`, `create_directory`, `copy_file`

### Sri Lanka news — `sri_news_mcp.py`

Sinhala/local news via Esena (not `news_mcp.py`).

### Web search — `search_mcp.py`

DuckDuckGo: `web_search`, `search_news`, `search_images`, `search_site`, `quick_answer`

### Reminder — `reminder_mcp.py`

`set_reminder`, `list_reminders`, `cancel_reminder`, `quick_notify` — uses `reminders.json` + Windows Task Scheduler

### Screenshot — `screenshot_mcp.py`

`take_screenshot`, `take_region_screenshot`, `screenshot_to_clipboard`, `list_recent_screenshots` → `~/Pictures/MCP_Screenshots/`

### System — `system_mcp.py`

CPU/RAM/disk/GPU, brightness, volume, processes, battery, uptime, network, open app, shutdown/restart/sleep

### Weather — `weather_mcp.py`

`get_weather`, `get_weather_forecast`, `get_air_quality`, `get_uv_index` (multi-provider fallback)

---

## Dependencies

```
mcp[cli]
google-api-python-client
google-auth-oauthlib
requests
sentence-transformers          # master_router.py only
psutil
GPUtil
screen-brightness-control
pycaw
comtypes
pyperclip
Pillow
pyautogui
winotify
googlesearch-python
```

---

## Google Cloud setup

1. [Google Cloud Console](https://console.cloud.google.com/) — create project  
2. Enable APIs: Gmail, Calendar, Drive, Docs, Sheets, Slides, Tasks, Forms  
3. OAuth 2.0 Desktop client → download → save as `MCP/credentials.json`  
4. Run `python google/auth_setup.py` and sign in in the browser  

Scopes are defined in [`google/auth_setup.py`](google/auth_setup.py) and [`google/google_common.py`](google/google_common.py).

---

## Security & GitHub

**Never push to a public repo:**

| File | Why |
|------|-----|
| `credentials.json` | Google OAuth client secret |
| `google/token.json` | Your Google access + refresh tokens |
| `.env` | API keys |
| `reminders.json` | Local personal reminders |

These are listed in [`.gitignore`](.gitignore). Use [`credentials.json.example`](credentials.json.example) as a template only.

**If you already committed secrets:** delete them from Git history, then in [Google Cloud Console](https://console.cloud.google.com/) → Credentials → reset client secret and revoke old tokens. Re-run `python google/auth_setup.py`.

**Docs:** use placeholders like `your.name@gmail.com` — not your real email.

## Notes

- Built primarily for **Windows** (brightness, volume, notifications).  
- Each Google handler is **independent** — MCP config decides what the agent can use.  
- `google_main_mcp.py` is **not** in this repo; use individual `*_handlers.py` or `master_router.py`.  
- Large tool counts (~100+ Google tools) may be heavy for small local models; prefer registering only the services you need.

---

*Syntiox MCP Tools — Cursor / Claude Desktop / LM Studio on Windows*
