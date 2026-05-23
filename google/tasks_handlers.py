"""
🎯 Google Tasks Handler Tools
"""
from mcp.server.fastmcp import FastMCP
from google_common import get_service

mcp = FastMCP("Google-Tasks-Tools")


def _tasks():
    return get_service('tasks', 'v1')


@mcp.tool()
def list_task_lists() -> str:
    """Task lists list කරයි. Use when user says: 'task lists', 'todo lists'."""
    try:
        lists = _tasks().tasklists().list(maxResults=20).execute().get('items', [])
        if not lists:
            return "📋 Task lists හමු නොවීය."
        output = f"📋 TASK LISTS — {len(lists)}\n{'─'*35}\n"
        for tl in lists:
            output += f"  📌 {tl['title']} (ID: {tl['id']})\n"
        return output
    except Exception as e:
        return f"❌ Task lists දෝෂයක්: {e}"


@mcp.tool()
def list_tasks(tasklist_id: str = "@default", show_completed: bool = False) -> str:
    """Tasks list කරයි. Use when user says: 'my tasks', 'todo list'."""
    try:
        tasks = _tasks().tasks().list(
            tasklist=tasklist_id, showCompleted=show_completed, maxResults=50
        ).execute().get('items', [])
        if not tasks:
            return "✅ Tasks නොමැත."
        pending = [t for t in tasks if t.get('status') != 'completed']
        completed = [t for t in tasks if t.get('status') == 'completed']
        output = f"📋 TASKS ({len(pending)} pending)\n{'─'*40}\n"
        for t in pending:
            due = t.get('due', '')[:10] if t.get('due') else 'No due'
            output += f"  ⬜ {t['title']} | Due: {due} | ID: {t['id']}\n"
        if show_completed and completed:
            output += "\n✅ DONE:\n"
            for t in completed:
                output += f"  ✅ {t['title']}\n"
        return output
    except Exception as e:
        return f"❌ List tasks දෝෂයක්: {e}"


@mcp.tool()
def create_task(title: str, tasklist_id: str = "@default", notes: str = "", due_date: str = "") -> str:
    """නව task සාදයි. Use when user says: 'add task', 'create todo'."""
    try:
        body = {'title': title, 'status': 'needsAction'}
        if notes:
            body['notes'] = notes
        if due_date:
            body['due'] = f"{due_date}T00:00:00.000Z"
        task = _tasks().tasks().insert(tasklist=tasklist_id, body=body).execute()
        return f"✅ Task '{title}' created.\n   🔑 ID: {task['id']}\n   💡 Use ID for update/complete/delete."
    except Exception as e:
        return f"❌ Create task දෝෂයක්: {e}"


@mcp.tool()
def update_task(
    task_id: str,
    tasklist_id: str = "@default",
    title: str = "",
    notes: str = "",
    due_date: str = "",
) -> str:
    """
    Task update කරයි (without completing).
    Use when user says: 'update task', 'edit todo', 'change task title'.
    """
    try:
        svc = _tasks()
        task = svc.tasks().get(tasklist=tasklist_id, task=task_id).execute()
        if title:
            task['title'] = title
        if notes:
            task['notes'] = notes
        if due_date:
            task['due'] = f"{due_date}T00:00:00.000Z"
        updated = svc.tasks().update(tasklist=tasklist_id, task=task_id, body=task).execute()
        return f"✅ Task updated: '{updated['title']}'."
    except Exception as e:
        return f"❌ Update task දෝෂයක්: {e}"


@mcp.tool()
def set_task_due_date(task_id: str, due_date: str, tasklist_id: str = "@default") -> str:
    """Task due date set කරයි. Use when user says: 'set due date', 'task deadline'."""
    return update_task(task_id, tasklist_id, due_date=due_date)


@mcp.tool()
def complete_task(task_id: str, tasklist_id: str = "@default") -> str:
    """Task complete කරයි. Use when user says: 'complete task', 'mark done'."""
    try:
        svc = _tasks()
        task = svc.tasks().get(tasklist=tasklist_id, task=task_id).execute()
        task['status'] = 'completed'
        updated = svc.tasks().update(tasklist=tasklist_id, task=task_id, body=task).execute()
        return f"✅ Task '{updated['title']}' completed! 🎉"
    except Exception as e:
        return f"❌ Complete task දෝෂයක්: {e}"


@mcp.tool()
def uncomplete_task(task_id: str, tasklist_id: str = "@default") -> str:
    """
    Completed task reopen කරයි.
    Use when user says: 'uncomplete task', 'reopen todo', 'mark task not done'.
    """
    try:
        svc = _tasks()
        task = svc.tasks().get(tasklist=tasklist_id, task=task_id).execute()
        task['status'] = 'needsAction'
        task.pop('completed', None)
        updated = svc.tasks().update(tasklist=tasklist_id, task=task_id, body=task).execute()
        return f"✅ Task '{updated['title']}' reopened."
    except Exception as e:
        return f"❌ Uncomplete task දෝෂයක්: {e}"


@mcp.tool()
def delete_task(task_id: str, tasklist_id: str = "@default") -> str:
    """Task delete කරයි. Use when user says: 'delete task', 'remove todo'."""
    try:
        _tasks().tasks().delete(tasklist=tasklist_id, task=task_id).execute()
        return f"🗑️ Task deleted (ID: {task_id})."
    except Exception as e:
        return f"❌ Delete task දෝෂයක්: {e}"


@mcp.tool()
def move_task_to_list(task_id: str, source_list_id: str, target_list_id: str) -> str:
    """
    Task වෙන list එකට move කරයි.
    Use when user says: 'move task', 'move todo to list'.
    """
    try:
        svc = _tasks()
        task = svc.tasks().get(tasklist=source_list_id, task=task_id).execute()
        body = {k: task[k] for k in ('title', 'notes', 'due', 'status') if k in task}
        new_task = svc.tasks().insert(tasklist=target_list_id, body=body).execute()
        svc.tasks().delete(tasklist=source_list_id, task=task_id).execute()
        return f"✅ Moved '{new_task['title']}' to list {target_list_id}. New ID: {new_task['id']}"
    except Exception as e:
        return f"❌ Move task දෝෂයක්: {e}"


@mcp.tool()
def create_task_list(title: str) -> str:
    """Task list සාදයි. Use when user says: 'create task list', 'new todo group'."""
    try:
        result = _tasks().tasklists().insert(body={'title': title}).execute()
        return f"✅ Task list '{title}' created. ID: {result['id']}"
    except Exception as e:
        return f"❌ Create task list දෝෂයක්: {e}"


@mcp.tool()
def rename_task_list(tasklist_id: str, new_title: str) -> str:
    """Task list rename කරයි. Use when user says: 'rename task list'."""
    try:
        _tasks().tasklists().patch(tasklist=tasklist_id, body={'title': new_title}).execute()
        return f"✅ Task list renamed to '{new_title}'."
    except Exception as e:
        return f"❌ Rename task list දෝෂයක්: {e}"


@mcp.tool()
def delete_task_list(tasklist_id: str) -> str:
    """Task list delete කරයි. Use when user says: 'delete task list'."""
    try:
        _tasks().tasklists().delete(tasklist=tasklist_id).execute()
        return f"🗑️ Task list deleted (ID: {tasklist_id})."
    except Exception as e:
        return f"❌ Delete task list දෝෂයක්: {e}"


@mcp.tool()
def clear_completed_tasks(tasklist_id: str = "@default") -> str:
    """
    Completed tasks delete කරයි.
    Use when user says: 'clear completed tasks', 'remove done todos'.
    """
    try:
        svc = _tasks()
        tasks = svc.tasks().list(
            tasklist=tasklist_id, showCompleted=True, showHidden=True, maxResults=100
        ).execute().get('items', [])
        completed = [t for t in tasks if t.get('status') == 'completed']
        for t in completed:
            svc.tasks().delete(tasklist=tasklist_id, task=t['id']).execute()
        return f"🧹 Cleared {len(completed)} completed task(s)."
    except Exception as e:
        return f"❌ Clear completed දෝෂයක්: {e}"


@mcp.tool()
def search_tasks(query: str, tasklist_id: str = "@default") -> str:
    """
    Task title අනුව search කරයි.
    Use when user says: 'search tasks', 'find todo'.
    """
    try:
        tasks = _tasks().tasks().list(tasklist=tasklist_id, maxResults=100).execute().get('items', [])
        q = query.lower()
        matches = [t for t in tasks if q in t.get('title', '').lower()]
        if not matches:
            return f"🔍 No tasks matching '{query}'."
        output = f"🔍 TASKS: '{query}'\n{'─'*30}\n"
        for t in matches:
            status = t.get('status', '?')
            output += f"  [{status}] {t['title']} (ID: {t['id']})\n"
        return output
    except Exception as e:
        return f"❌ Search tasks දෝෂයක්: {e}"


if __name__ == "__main__":
    mcp.run(transport='stdio')
