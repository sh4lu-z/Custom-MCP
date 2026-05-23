import os
import json
import uuid
import datetime
import subprocess
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Syntiox-Reminder-Tool")

# Reminders store කෙරෙන JSON file
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
REMINDERS_FILE = os.path.join(BASE_DIR, 'reminders.json')


def _load() -> list:
    if os.path.exists(REMINDERS_FILE):
        with open(REMINDERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def _save(reminders: list):
    with open(REMINDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(reminders, f, indent=2, ensure_ascii=False)


def _show_toast(title: str, message: str):
    """Windows toast notification (winotify)."""
    try:
        from winotify import Notification, audio
        toast = Notification(
            app_id="Syntiox MCP",
            title=title,
            msg=message,
            duration="long"
        )
        toast.set_audio(audio.Default, loop=False)
        toast.show()
    except ImportError:
        # Fallback: PowerShell toast
        ps_script = (
            f"Add-Type -AssemblyName System.Windows.Forms;"
            f"[System.Windows.Forms.MessageBox]::Show('{message}', '{title}')"
        )
        subprocess.Popen(['powershell', '-command', ps_script])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 1: Set Reminder
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def set_reminder(message: str, delay_minutes: int = 0, remind_at: str = "") -> str:
    """
    Windows reminder/notification set කරයි.
    Use when user says: 'remind me', 'set reminder', 'notify me', 'reminder set කරන්න'.

    delay_minutes: minutes පසු notify කරන්න (0 = immediate notification)
    remind_at: specific time 'YYYY-MM-DD HH:MM' format (optional, overrides delay_minutes)
    """
    try:
        now = datetime.datetime.now()

        # Calculate trigger time
        if remind_at:
            trigger_time = datetime.datetime.strptime(remind_at, "%Y-%m-%d %H:%M")
        else:
            trigger_time = now + datetime.timedelta(minutes=delay_minutes)

        reminder_id = str(uuid.uuid4())[:8]
        reminder    = {
            "id"          : reminder_id,
            "message"     : message,
            "trigger_time": trigger_time.strftime("%Y-%m-%d %H:%M"),
            "created_at"  : now.strftime("%Y-%m-%d %H:%M:%S"),
            "done"        : False
        }

        # Save to JSON
        reminders = _load()
        reminders.append(reminder)
        _save(reminders)

        # Windows Task Scheduler හරහා notification schedule කරන්න
        trigger_str = trigger_time.strftime("%Y-%m-%dT%H:%M:00")
        task_name   = f"SyntioxReminder_{reminder_id}"
        ps_action   = (
            f"$action = New-ScheduledTaskAction -Execute 'powershell.exe' "
            f"-Argument \"-WindowStyle Hidden -command \\\"Add-Type -AssemblyName System.Windows.Forms; "
            f"[System.Windows.Forms.MessageBox]::Show('{message}', '⏰ Syntiox Reminder')\\\"\";"
            f"$trigger = New-ScheduledTaskTrigger -Once -At '{trigger_str}';"
            f"Register-ScheduledTask -TaskName '{task_name}' -Action $action -Trigger $trigger -Force"
        )
        subprocess.run(['powershell', '-command', ps_action], capture_output=True, timeout=10)

        # Immediate notification (delay=0)
        if delay_minutes == 0 and not remind_at:
            _show_toast("⏰ Syntiox Reminder", message)
            return f"🔔 Reminder ඉක්මනින් notify කරන ලදී: '{message}'"

        time_str = trigger_time.strftime('%Y-%m-%d %H:%M')
        return (
            f"✅ Reminder set!\n"
            f"  ⏰ Time    : {time_str}\n"
            f"  📝 Message : {message}\n"
            f"  🔑 ID      : {reminder_id}"
        )
    except Exception as e:
        return f"❌ Reminder set error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 2: List Reminders
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def list_reminders() -> str:
    """
    Pending reminders list කරයි.
    Use when user says: 'my reminders', 'upcoming reminders', 'reminders show කරන්න'.
    """
    try:
        reminders = [r for r in _load() if not r.get('done')]
        if not reminders:
            return "📋 Pending reminders නොමැත."

        now    = datetime.datetime.now()
        output = f"⏰ REMINDERS ({len(reminders)} pending)\n{'─'*40}\n"
        for r in reminders:
            trigger = datetime.datetime.strptime(r['trigger_time'], "%Y-%m-%d %H:%M")
            diff    = trigger - now
            if diff.total_seconds() > 0:
                mins = int(diff.total_seconds() // 60)
                remaining = f"⏳ {mins} min remaining" if mins < 60 else f"⏳ {mins//60}h {mins%60}m remaining"
            else:
                remaining = "🔴 Overdue"
            output += (
                f"  🔔 {r['message']}\n"
                f"     🕐 {r['trigger_time']} | {remaining}\n"
                f"     🔑 ID: {r['id']}\n"
                f"{'─'*40}\n"
            )
        return output
    except Exception as e:
        return f"❌ List reminders error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 3: Cancel Reminder
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def cancel_reminder(reminder_id: str) -> str:
    """
    Reminder ID ෙකන් reminder cancel කරයි.
    Use when user says: 'cancel reminder', 'delete reminder', 'reminder cancel'.
    """
    try:
        reminders = _load()
        found     = False
        for r in reminders:
            if r['id'] == reminder_id:
                r['done'] = True
                found     = True
                msg       = r['message']
                # Windows Task Scheduler ෙකන් remove
                task_name = f"SyntioxReminder_{reminder_id}"
                subprocess.run(
                    ['powershell', '-command', f"Unregister-ScheduledTask -TaskName '{task_name}' -Confirm:$false"],
                    capture_output=True
                )
                break

        if not found:
            return f"❌ Reminder ID '{reminder_id}' හමු නොවීය."

        _save(reminders)
        return f"✅ Reminder '{msg}' (ID: {reminder_id}) cancel කරන ලදී."
    except Exception as e:
        return f"❌ Cancel reminder error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 4: Quick Notify (Immediate)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def quick_notify(title: str, message: str) -> str:
    """
    ඉක්මනින් Windows notification එකක් දමයි.
    Use when user says: 'notify me now', 'show notification', 'popup message'.
    """
    try:
        _show_toast(title, message)
        return f"🔔 Notification sent: '{title}' — '{message}'"
    except Exception as e:
        return f"❌ Notify error: {e}"


if __name__ == "__main__":
    mcp.run(transport='stdio')
