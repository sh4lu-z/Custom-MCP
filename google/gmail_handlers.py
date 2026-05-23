"""
📧 Gmail Handler Tools
"""
import os
import base64
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from mcp.server.fastmcp import FastMCP
from google_common import get_service

mcp = FastMCP("Google-Gmail-Tools")


def _gmail():
    return get_service('gmail', 'v1')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 1: Latest Emails
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def list_latest_emails(max_results: int = 5) -> str:
    """
    Inbox ලෙ ඇති නවතම emails list කරයි.
    Use when user asks: 'emails', 'inbox', 'mail check', 'ඊමේල් බලන්න'.
    """
    try:
        svc = _gmail()
        results = svc.users().messages().list(
            userId='me', labelIds=['INBOX'], maxResults=max_results
        ).execute()
        messages = results.get('messages', [])

        if not messages:
            return "📥 Inbox හි ඊමේල් කිසිවක් හමු නොවීය."

        output = f"📥 INBOX — TOP {len(messages)} EMAILS\n{'─'*40}\n"
        for msg in messages:
            data = svc.users().messages().get(
                userId='me', id=msg['id'], format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            headers = {h['name']: h['value'] for h in data.get('payload', {}).get('headers', [])}
            snippet = data.get('snippet', '')[:100]
            output += (
                f"📌 Subject : {headers.get('Subject', 'No Subject')}\n"
                f"   From    : {headers.get('From', 'Unknown')}\n"
                f"   Date    : {headers.get('Date', '')}\n"
                f"   Preview : {snippet}...\n"
                f"   ID      : {msg['id']}\n"
                f"{'─'*40}\n"
            )
        return output
    except Exception as e:
        return f"❌ Emails ලබාගැනීමේ දෝෂයක්: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 2: Send Email
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def send_gmail_email(to_email: str, subject: str, email_body: str) -> str:
    """
    Gmail හරහා email එකක් යවයි.
    Use when user says: 'send email', 'mail යවන්න'.
    """
    try:
        svc = _gmail()
        msg = MIMEText(email_body)
        msg['to'] = to_email
        msg['from'] = 'me'
        msg['subject'] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        sent = svc.users().messages().send(userId='me', body={'raw': raw}).execute()
        return f"✅ ඊමේල් {to_email} වෙත සාර්ථකව යවන ලදී! (ID: {sent['id']})"
    except Exception as e:
        return f"❌ Email යැවීමේ දෝෂයක්: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 3: Search Emails
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def search_emails(query: str, max_results: int = 5) -> str:
    """
    Gmail messages search කරයි (subject, sender, keyword).
    Use when user says: 'find email', 'search mail', 'email හොයන්න'.
    Examples: query='from:boss@company.com', query='invoice', query='subject:meeting'
    """
    try:
        svc = _gmail()
        results = svc.users().messages().list(
            userId='me', q=query, maxResults=max_results
        ).execute()
        messages = results.get('messages', [])

        if not messages:
            return f"🔍 '{query}' සඳහා emails හමු නොවීය."

        output = f"🔍 SEARCH: '{query}' — {len(messages)} RESULTS\n{'─'*40}\n"
        for msg in messages:
            data = svc.users().messages().get(
                userId='me', id=msg['id'], format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            headers = {h['name']: h['value'] for h in data.get('payload', {}).get('headers', [])}
            output += (
                f"📌 {headers.get('Subject', 'No Subject')}\n"
                f"   From: {headers.get('From', 'Unknown')} | Date: {headers.get('Date', '')}\n"
                f"   ID: {msg['id']}\n"
                f"{'─'*40}\n"
            )
        return output
    except Exception as e:
        return f"❌ Email සොයීමේ දෝෂයක්: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 4: Get Full Email Body
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def get_email_body(email_id: str) -> str:
    """
    Email ID එකෙන් email සම්පූර්ණ content ලබාගනී.
    Use when user says: 'read this email', 'show email content', 'email details'.
    """
    try:
        svc = _gmail()
        msg = svc.users().messages().get(userId='me', id=email_id, format='full').execute()
        headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}

        # Body decode
        body = ""
        payload = msg.get('payload', {})

        def extract_body(part):
            if part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            for sub in part.get('parts', []):
                result = extract_body(sub)
                if result:
                    return result
            return ""

        body = extract_body(payload)
        if not body:
            body = "(Body හමු නොවීය)"

        return (
            f"📧 EMAIL DETAILS\n{'═'*40}\n"
            f"From    : {headers.get('From', 'Unknown')}\n"
            f"To      : {headers.get('To', 'Unknown')}\n"
            f"Subject : {headers.get('Subject', 'No Subject')}\n"
            f"Date    : {headers.get('Date', '')}\n"
            f"{'─'*40}\n"
            f"{body}\n"
        )
    except Exception as e:
        return f"❌ Email body ලබාගැනීමේ දෝෂයක්: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 5: Delete Email
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def delete_email(email_id: str) -> str:
    """
    Email Trash ලෙ දමයි (delete).
    Use when user says: 'delete email', 'remove mail', 'ඊමේල් delete කරන්න'.
    """
    try:
        svc = _gmail()
        svc.users().messages().trash(userId='me', id=email_id).execute()
        return f"🗑️ Email (ID: {email_id}) Trash ලෙ දමන ලදී."
    except Exception as e:
        return f"❌ Email delete කිරීමේ දෝෂයක්: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 6: Mark Email as Read
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def mark_email_as_read(email_id: str) -> str:
    """
    Email Read ලෙ mark කරයි.
    Use when user says: 'mark as read', 'read කරන්න'.
    """
    try:
        svc = _gmail()
        svc.users().messages().modify(
            userId='me', id=email_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        return f"✅ Email (ID: {email_id}) Read ලෙ mark කරන ලදී."
    except Exception as e:
        return f"❌ Mark as read දෝෂයක්: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 7: Reply to Email
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def reply_to_email(email_id: str, reply_body: str) -> str:
    """
    Email ID එකට reply යවයි.
    Use when user says: 'reply to email', 'respond to mail', 'reply කරන්න'.
    """
    try:
        svc = _gmail()
        original = svc.users().messages().get(userId='me', id=email_id, format='metadata',
                                               metadataHeaders=['From', 'Subject', 'Message-ID', 'To']).execute()
        headers = {h['name']: h['value'] for h in original.get('payload', {}).get('headers', [])}
        thread_id = original.get('threadId', '')

        reply_to = headers.get('From', '')
        subject  = headers.get('Subject', '')
        if not subject.startswith('Re:'):
            subject = f"Re: {subject}"
        msg_id   = headers.get('Message-ID', '')

        msg = MIMEText(reply_body)
        msg['to']          = reply_to
        msg['from']        = 'me'
        msg['subject']     = subject
        msg['In-Reply-To'] = msg_id
        msg['References']  = msg_id

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        svc.users().messages().send(
            userId='me', body={'raw': raw, 'threadId': thread_id}
        ).execute()
        return f"✅ Reply {reply_to} වෙත සාර්ථකව යවන ලදී!"
    except Exception as e:
        return f"❌ Reply යැවීමේ දෝෂයක්: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 8: List Gmail Labels
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def list_email_labels() -> str:
    """
    Gmail labels / folders ලයිස්ටුව ලබාදෙයි.
    Use when user says: 'gmail labels', 'folders', 'categories'.
    """
    try:
        svc = _gmail()
        result = svc.users().labels().list(userId='me').execute()
        labels = result.get('labels', [])

        if not labels:
            return "📂 Labels හමු නොවීය."

        output = "📂 GMAIL LABELS\n" + "─" * 30 + "\n"
        for lbl in labels:
            output += f"  🏷️  {lbl['name']}  (ID: {lbl['id']})\n"
        return output
    except Exception as e:
        return f"❌ Labels ලබාගැනීමේ දෝෂයක්: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 9: Send Email with Attachment
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def send_email_with_attachment(to_email: str, subject: str, email_body: str, file_path: str) -> str:
    """
    File attachment සමඟ email යවයි.
    Use when user says: 'send with file', 'attach and send', 'file attach කරලා mail යවන්න'.
    """
    try:
        if not os.path.exists(file_path):
            return f"❌ File හමු නොවීය: {file_path}"

        svc = _gmail()
        msg = MIMEMultipart()
        msg['to']      = to_email
        msg['from']    = 'me'
        msg['subject'] = subject
        msg.attach(MIMEText(email_body))

        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'
        main_type, sub_type = mime_type.split('/', 1)

        with open(file_path, 'rb') as f:
            attachment = MIMEBase(main_type, sub_type)
            attachment.set_payload(f.read())
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment',
                              filename=os.path.basename(file_path))
        msg.attach(attachment)

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        sent = svc.users().messages().send(userId='me', body={'raw': raw}).execute()
        return f"✅ Attachment සමඟ email {to_email} වෙත යවන ලදී! (ID: {sent['id']})"
    except Exception as e:
        return f"❌ Attachment email යැවීමේ දෝෂයක්: {e}"

# ──────────────────────────────────────────────────────────────
# ▶️ Entry Point
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport='stdio')