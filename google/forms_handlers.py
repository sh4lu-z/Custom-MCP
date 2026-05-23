"""
📋 Google Forms Handler Tools
"""
import uuid
from mcp.server.fastmcp import FastMCP
from google_common import get_service

mcp = FastMCP("Google-Forms-Tools")


def _forms():
    return get_service('forms', 'v1')


def _drive():
    return get_service('drive', 'v3')


@mcp.tool()
def list_forms(max_results: int = 10) -> str:
    """Forms list කරයි. Use when user says: 'list forms', 'google forms'."""
    try:
        results = _drive().files().list(
            q="mimeType='application/vnd.google-apps.form' and trashed=false",
            pageSize=max_results,
            fields="files(id, name, modifiedTime, webViewLink)"
        ).execute()
        files = results.get('files', [])
        if not files:
            return "📋 Forms හමු නොවීය."
        output = f"📋 GOOGLE FORMS — {len(files)}\n{'─'*40}\n"
        for f in files:
            output += f"📝 {f['name']} | ID: {f['id']}\n"
        return output
    except Exception as e:
        return f"❌ Forms list දෝෂයක්: {e}"


@mcp.tool()
def create_form(title: str, description: str = "") -> str:
    """නව Form සාදයි. Use when user says: 'create form', 'new google form'."""
    try:
        body = {'info': {'title': title}}
        if description:
            body['info']['description'] = description
        form = _forms().forms().create(body=body).execute()
        fid = form['formId']
        return (
            f"✅ Form '{title}' created.\n"
            f"   🔑 ID: {fid}\n"
            f"   📤 {form.get('responderUri', '')}\n"
            f"   💡 Use ID to add questions / read responses."
        )
    except Exception as e:
        return f"❌ Form create දෝෂයක්: {e}"


@mcp.tool()
def get_form_info(form_id: str) -> str:
    """Form details + questions. Use when user says: 'form info', 'form questions'."""
    try:
        form = _forms().forms().get(formId=form_id).execute()
        info = form.get('info', {})
        items = form.get('items', [])
        output = (
            f"📋 FORM: {info.get('title')}\n"
            f"Questions: {len(items)}\n"
            f"Edit: https://docs.google.com/forms/d/{form_id}/edit\n"
            f"Share: {form.get('responderUri', 'N/A')}\n{'─'*40}\n"
        )
        for i, item in enumerate(items, 1):
            qid = item.get('questionItem', {}).get('question', {}).get('questionId', '')
            output += f"  {i}. {item.get('title', '?')} (itemId: {item.get('itemId', '')}, qId: {qid})\n"
        return output
    except Exception as e:
        return f"❌ Form info දෝෂයක්: {e}"


@mcp.tool()
def get_form_responses(form_id: str, max_responses: int = 10) -> str:
    """Form responses ලබාගනී. Use when user says: 'form responses', 'form answers'."""
    try:
        svc = _forms()
        result = svc.forms().responses().list(formId=form_id, pageSize=max_responses).execute()
        responses = result.get('responses', [])
        if not responses:
            return f"📋 No responses for form {form_id}."
        form = svc.forms().get(formId=form_id).execute()
        q_map = {}
        for item in form.get('items', []):
            if 'questionItem' in item:
                qid = item['questionItem']['question']['questionId']
                q_map[qid] = item.get('title', qid)
        output = f"📊 RESPONSES ({len(responses)})\n{'═'*40}\n"
        for i, resp in enumerate(responses, 1):
            output += f"\n🔹 Response {i}\n"
            for qid, ans in resp.get('answers', {}).items():
                vals = [v.get('value', '') for v in ans.get('textAnswers', {}).get('answers', [])]
                output += f"  ❓ {q_map.get(qid, qid)}: {', '.join(vals)}\n"
        return output
    except Exception as e:
        return f"❌ Form responses දෝෂයක්: {e}"


@mcp.tool()
def add_text_question(form_id: str, question_title: str, required: bool = False) -> str:
    """
    Text question add කරයි.
    Use when user says: 'add text question', 'add question to form'.
    """
    try:
        item_id = f"item_{uuid.uuid4().hex[:8]}"
        _forms().forms().batchUpdate(
            formId=form_id,
            body={'requests': [{
                'createItem': {
                    'item': {
                        'itemId': item_id,
                        'title': question_title,
                        'questionItem': {
                            'question': {
                                'required': required,
                                'textQuestion': {'paragraph': False},
                            }
                        },
                    },
                    'location': {'index': 0},
                }
            }]}
        ).execute()
        return f"✅ Text question added: '{question_title}' (itemId: {item_id})."
    except Exception as e:
        return f"❌ Add text question දෝෂයක්: {e}"


@mcp.tool()
def add_multiple_choice_question(
    form_id: str, question_title: str, options_csv: str, required: bool = False
) -> str:
    """
    Multiple choice question add කරයි.
    Use when user says: 'add choice question', 'multiple choice form'.
    options_csv: 'Yes,No,Maybe'
    """
    try:
        options = [{'value': o.strip()} for o in options_csv.split(',') if o.strip()]
        if not options:
            return "❌ Provide at least one option."
        item_id = f"item_{uuid.uuid4().hex[:8]}"
        _forms().forms().batchUpdate(
            formId=form_id,
            body={'requests': [{
                'createItem': {
                    'item': {
                        'itemId': item_id,
                        'title': question_title,
                        'questionItem': {
                            'question': {
                                'required': required,
                                'choiceQuestion': {
                                    'type': 'RADIO',
                                    'options': options,
                                },
                            }
                        },
                    },
                    'location': {'index': 0},
                }
            }]}
        ).execute()
        return f"✅ Choice question added: '{question_title}' ({len(options)} options)."
    except Exception as e:
        return f"❌ Add choice question දෝෂයක්: {e}"


@mcp.tool()
def add_checkbox_question(
    form_id: str, question_title: str, options_csv: str, required: bool = False
) -> str:
    """
    Checkbox question add කරයි.
    Use when user says: 'add checkbox question', 'checkbox form question'.
    """
    try:
        options = [{'value': o.strip()} for o in options_csv.split(',') if o.strip()]
        item_id = f"item_{uuid.uuid4().hex[:8]}"
        _forms().forms().batchUpdate(
            formId=form_id,
            body={'requests': [{
                'createItem': {
                    'item': {
                        'itemId': item_id,
                        'title': question_title,
                        'questionItem': {
                            'question': {
                                'required': required,
                                'choiceQuestion': {
                                    'type': 'CHECKBOX',
                                    'options': options,
                                },
                            }
                        },
                    },
                    'location': {'index': 0},
                }
            }]}
        ).execute()
        return f"✅ Checkbox question added: '{question_title}'."
    except Exception as e:
        return f"❌ Add checkbox question දෝෂයක්: {e}"


@mcp.tool()
def update_form_info(form_id: str, title: str = "", description: str = "") -> str:
    """
    Form title/description update කරයි.
    Use when user says: 'update form title', 'edit form description'.
    """
    try:
        info = {}
        if title:
            info['title'] = title
        if description:
            info['description'] = description
        if not info:
            return "❌ Provide title and/or description."
        _forms().forms().batchUpdate(
            formId=form_id,
            body={'requests': [{'updateFormInfo': {'info': info, 'updateMask': ','.join(info.keys())}}]}
        ).execute()
        return f"✅ Form info updated."
    except Exception as e:
        return f"❌ Update form info දෝෂයක්: {e}"


@mcp.tool()
def delete_form_question(form_id: str, item_id: str) -> str:
    """
    Question delete කරයි (itemId from get_form_info).
    Use when user says: 'delete form question', 'remove question'.
    """
    try:
        _forms().forms().batchUpdate(
            formId=form_id,
            body={'requests': [{'deleteItem': {'itemId': item_id}}]}
        ).execute()
        return f"🗑️ Question item {item_id} deleted."
    except Exception as e:
        return f"❌ Delete question දෝෂයක්: {e}"


@mcp.tool()
def reorder_form_questions(form_id: str, item_id: str, new_index: int) -> str:
    """
    Question order change කරයි.
    Use when user says: 'reorder form questions', 'move question'.
    """
    try:
        _forms().forms().batchUpdate(
            formId=form_id,
            body={'requests': [{
                'updateItemLocation': {
                    'location': {'index': new_index},
                    'itemId': item_id,
                }
            }]}
        ).execute()
        return f"✅ Question moved to index {new_index}."
    except Exception as e:
        return f"❌ Reorder question දෝෂයක්: {e}"


@mcp.tool()
def delete_form(form_id: str) -> str:
    """Form delete කරයි. Use when user says: 'delete form', 'remove google form'."""
    try:
        _drive().files().delete(fileId=form_id).execute()
        return f"🗑️ Form deleted (ID: {form_id})."
    except Exception as e:
        return f"❌ Delete form දෝෂයක්: {e}"


@mcp.tool()
def clear_form_responses(form_id: str) -> str:
    """
    Form responses delete — may be limited by Google API (readonly scope). Tries batch delete.
    Use when user says: 'clear form responses', 'delete all answers'.
    """
    try:
        svc = _forms()
        responses = svc.forms().responses().list(formId=form_id).execute().get('responses', [])
        if not responses:
            return "No responses to clear."
        for resp in responses:
            svc.forms().responses().delete(formId=form_id, responseId=resp['responseId']).execute()
        return f"🧹 Cleared {len(responses)} response(s)."
    except Exception as e:
        return f"❌ Clear responses දෝෂයක්: {e}"


@mcp.tool()
def get_form_responder_url(form_id: str) -> str:
    """Form public responder URL ලබාගනී. Use when user says: 'form link', 'share form url'."""
    try:
        form = _forms().forms().get(formId=form_id).execute()
        url = form.get('responderUri', f"https://docs.google.com/forms/d/{form_id}/viewform")
        return f"📤 Responder URL:\n{url}"
    except Exception as e:
        return f"❌ Get responder URL දෝෂයක්: {e}"


@mcp.tool()
def duplicate_form(form_id: str, new_title: str) -> str:
    """Form copy කරයි. Use when user says: 'duplicate form', 'copy form'."""
    try:
        result = _drive().files().copy(fileId=form_id, body={'name': new_title}).execute()
        return f"✅ Form copied as '{new_title}'. ID: {result['id']}"
    except Exception as e:
        return f"❌ Duplicate form දෝෂයක්: {e}"


if __name__ == "__main__":
    mcp.run(transport='stdio')
