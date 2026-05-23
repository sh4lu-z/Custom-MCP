"""
📅 Google Calendar Handler Tools
"""
from datetime import datetime, timedelta, timezone
from mcp.server.fastmcp import FastMCP
from google_common import get_service

mcp = FastMCP("Google-Calendar-Tools")


def _cal():
    return get_service('calendar', 'v3')


def _fmt_event(ev: dict) -> str:
    start = ev['start'].get('dateTime', ev['start'].get('date', ''))
    return (
        f"🗓️  {ev.get('summary', '(No Title)')}\n"
        f"   🕐 {start}\n"
        f"   📍 {ev.get('location', 'N/A')}\n"
        f"   🔑 ID: {ev['id']}\n"
        f"{'─'*40}\n"
    )


@mcp.tool()
def list_upcoming_events(days: int = 7) -> str:
    """ඉදිරි events list කරයි. Use when user says: 'upcoming events', 'calendar schedule'."""
    try:
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=days)
        events = _cal().events().list(
            calendarId='primary', timeMin=now.isoformat(), timeMax=end.isoformat(),
            maxResults=20, singleEvents=True, orderBy='startTime'
        ).execute().get('items', [])
        if not events:
            return f"📅 ඉදිරි {days} දිනවල events නොමැත."
        output = f"📅 UPCOMING — {days} DAYS\n{'─'*40}\n"
        for ev in events:
            output += _fmt_event(ev)
        return output
    except Exception as e:
        return f"❌ Events list දෝෂයක්: {e}"


@mcp.tool()
def create_calendar_event(
    title: str, start_datetime: str, end_datetime: str,
    description: str = "", location: str = ""
) -> str:
    """
    Calendar event සාදයි.
    Use when user says: 'add event', 'schedule meeting', 'create appointment'.
    Datetime: '2025-06-15T10:00:00'
    """
    try:
        event = {
            'summary': title, 'location': location, 'description': description,
            'start': {'dateTime': start_datetime, 'timeZone': 'Asia/Colombo'},
            'end': {'dateTime': end_datetime, 'timeZone': 'Asia/Colombo'},
        }
        created = _cal().events().insert(calendarId='primary', body=event).execute()
        return (
            f"✅ Event created: {title}\n"
            f"   🔑 ID: {created['id']}\n"
            f"   🔗 {created.get('htmlLink', '')}\n"
            f"   💡 Use ID for update/delete."
        )
    except Exception as e:
        return f"❌ Event create දෝෂයක්: {e}"


@mcp.tool()
def update_calendar_event(
    event_id: str,
    title: str = "",
    start_datetime: str = "",
    end_datetime: str = "",
    description: str = "",
    location: str = "",
) -> str:
    """
    Event update කරයි (patch).
    Use when user says: 'update event', 'edit meeting', 'change appointment', 'reschedule'.
    Empty fields are not changed.
    """
    try:
        body = {}
        if title:
            body['summary'] = title
        if description:
            body['description'] = description
        if location:
            body['location'] = location
        if start_datetime:
            body['start'] = {'dateTime': start_datetime, 'timeZone': 'Asia/Colombo'}
        if end_datetime:
            body['end'] = {'dateTime': end_datetime, 'timeZone': 'Asia/Colombo'}
        if not body:
            return "❌ Provide at least one field to update."
        updated = _cal().events().patch(
            calendarId='primary', eventId=event_id, body=body
        ).execute()
        return f"✅ Event updated: {updated.get('summary')} (ID: {event_id})"
    except Exception as e:
        return f"❌ Event update දෝෂයක්: {e}"


@mcp.tool()
def get_calendar_event(event_id: str) -> str:
    """Event by ID ලබාගනී. Use when user says: 'get event', 'event details'."""
    try:
        ev = _cal().events().get(calendarId='primary', eventId=event_id).execute()
        attendees = ', '.join(a.get('email', '') for a in ev.get('attendees', []))
        start = ev['start'].get('dateTime', ev['start'].get('date', ''))
        end = ev['end'].get('dateTime', ev['end'].get('date', ''))
        return (
            f"📅 EVENT\n{'═'*40}\n"
            f"Title: {ev.get('summary')}\nStart: {start}\nEnd: {end}\n"
            f"Location: {ev.get('location', 'N/A')}\n"
            f"Description: {(ev.get('description') or '')[:200]}\n"
            f"Attendees: {attendees or 'None'}\n"
            f"ID: {event_id}\nLink: {ev.get('htmlLink', 'N/A')}\n"
        )
    except Exception as e:
        return f"❌ Get event දෝෂයක්: {e}"


@mcp.tool()
def delete_calendar_event(event_id: str) -> str:
    """Event delete කරයි. Use when user says: 'delete event', 'cancel meeting'."""
    try:
        _cal().events().delete(calendarId='primary', eventId=event_id).execute()
        return f"🗑️ Event deleted (ID: {event_id})."
    except Exception as e:
        return f"❌ Event delete දෝෂයක්: {e}"


@mcp.tool()
def search_calendar_events(query: str, max_results: int = 5) -> str:
    """Events search කරයි. Use when user says: 'find event', 'search calendar'."""
    try:
        events = _cal().events().list(
            calendarId='primary', q=query, maxResults=max_results,
            singleEvents=True, orderBy='startTime',
            timeMin=datetime.now(timezone.utc).isoformat()
        ).execute().get('items', [])
        if not events:
            return f"🔍 '{query}' events හමු නොවීය."
        output = f"🔍 SEARCH: '{query}'\n{'─'*40}\n"
        for ev in events:
            output += _fmt_event(ev)
        return output
    except Exception as e:
        return f"❌ Calendar search දෝෂයක්: {e}"


@mcp.tool()
def list_events_date_range(start_date: str, end_date: str, max_results: int = 30) -> str:
    """
    Date range එකේ events list කරයි (past or future).
    Use when user says: 'events between dates', 'calendar range'.
    Dates: '2025-01-01' or ISO datetime.
    """
    try:
        tmin = start_date if 'T' in start_date else f"{start_date}T00:00:00Z"
        tmax = end_date if 'T' in end_date else f"{end_date}T23:59:59Z"
        events = _cal().events().list(
            calendarId='primary', timeMin=tmin, timeMax=tmax,
            maxResults=max_results, singleEvents=True, orderBy='startTime'
        ).execute().get('items', [])
        if not events:
            return f"📅 No events between {start_date} and {end_date}."
        output = f"📅 EVENTS {start_date} → {end_date}\n{'─'*40}\n"
        for ev in events:
            output += _fmt_event(ev)
        return output
    except Exception as e:
        return f"❌ Date range list දෝෂයක්: {e}"


@mcp.tool()
def list_calendars() -> str:
    """User calendars list කරයි. Use when user says: 'list calendars', 'my calendars'."""
    try:
        items = _cal().calendarList().list().execute().get('items', [])
        if not items:
            return "No calendars found."
        output = f"📅 CALENDARS — {len(items)}\n{'─'*40}\n"
        for c in items:
            output += f"  📌 {c.get('summary')} (ID: {c['id']}, primary: {c.get('primary', False)})\n"
        return output
    except Exception as e:
        return f"❌ List calendars දෝෂයක්: {e}"


@mcp.tool()
def add_event_attendees(event_id: str, emails_csv: str) -> str:
    """
    Event ලෙ attendees add කරයි.
    Use when user says: 'add attendees', 'invite to meeting'.
    emails_csv: 'a@x.com,b@y.com'
    """
    try:
        ev = _cal().events().get(calendarId='primary', eventId=event_id).execute()
        existing = ev.get('attendees', [])
        new_emails = [e.strip() for e in emails_csv.split(',') if e.strip()]
        for email in new_emails:
            existing.append({'email': email})
        updated = _cal().events().patch(
            calendarId='primary', eventId=event_id,
            body={'attendees': existing}, sendUpdates='all'
        ).execute()
        return f"✅ Attendees added to '{updated.get('summary')}' ({len(new_emails)} new)."
    except Exception as e:
        return f"❌ Add attendees දෝෂයක්: {e}"


@mcp.tool()
def create_all_day_event(title: str, start_date: str, end_date: str, description: str = "") -> str:
    """
    All-day event සාදයි.
    Use when user says: 'all day event', 'full day appointment'.
    Dates: '2025-06-15' (end_date is exclusive in Google Calendar API)
    """
    try:
        event = {
            'summary': title, 'description': description,
            'start': {'date': start_date}, 'end': {'date': end_date},
        }
        created = _cal().events().insert(calendarId='primary', body=event).execute()
        return f"✅ All-day event '{title}' created. ID: {created['id']}"
    except Exception as e:
        return f"❌ All-day event දෝෂයක්: {e}"


@mcp.tool()
def duplicate_calendar_event(event_id: str, new_start_datetime: str, new_end_datetime: str) -> str:
    """
    Event copy කර new times සමඟ සාදයි.
    Use when user says: 'duplicate event', 'copy meeting'.
    """
    try:
        ev = _cal().events().get(calendarId='primary', eventId=event_id).execute()
        for key in ('id', 'htmlLink', 'created', 'updated', 'etag', 'iCalUID', 'sequence'):
            ev.pop(key, None)
        ev['start'] = {'dateTime': new_start_datetime, 'timeZone': 'Asia/Colombo'}
        ev['end'] = {'dateTime': new_end_datetime, 'timeZone': 'Asia/Colombo'}
        created = _cal().events().insert(calendarId='primary', body=ev).execute()
        return f"✅ Duplicated event. New ID: {created['id']}"
    except Exception as e:
        return f"❌ Duplicate event දෝෂයක්: {e}"


@mcp.tool()
def set_event_reminder(event_id: str, minutes_before: int = 30) -> str:
    """
    Event reminder set කරයි.
    Use when user says: 'set reminder', 'notify before event'.
    """
    try:
        updated = _cal().events().patch(
            calendarId='primary', eventId=event_id,
            body={'reminders': {
                'useDefault': False,
                'overrides': [{'method': 'popup', 'minutes': minutes_before}],
            }}
        ).execute()
        return f"✅ Reminder set {minutes_before} min before '{updated.get('summary')}'."
    except Exception as e:
        return f"❌ Set reminder දෝෂයක්: {e}"


@mcp.tool()
def move_event_to_calendar(event_id: str, target_calendar_id: str) -> str:
    """
    Event වෙන calendar එකට move කරයි.
    Use when user says: 'move event to calendar'.
    """
    try:
        moved = _cal().events().move(
            calendarId='primary', eventId=event_id, destination=target_calendar_id
        ).execute()
        return f"✅ Moved '{moved.get('summary')}' to calendar {target_calendar_id}."
    except Exception as e:
        return f"❌ Move event දෝෂයක්: {e}"


if __name__ == "__main__":
    mcp.run(transport='stdio')
