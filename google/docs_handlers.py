"""
📄 Google Docs Handler Tools
"""
import io
import os
from mcp.server.fastmcp import FastMCP
from googleapiclient.http import MediaIoBaseDownload
from google_common import get_service, escape_drive_query, share_file

mcp = FastMCP("Google-Docs-Tools")


def _docs():
    return get_service('docs', 'v1')


def _drive():
    return get_service('drive', 'v3')


def _doc_end_index(doc_id: str) -> int:
    doc = _docs().documents().get(documentId=doc_id).execute()
    return doc['body']['content'][-1]['endIndex'] - 1


def _extract_doc_text(doc: dict) -> str:
    text = ""
    for element in doc.get('body', {}).get('content', []):
        paragraph = element.get('paragraph')
        if paragraph:
            for run in paragraph.get('elements', []):
                text_run = run.get('textRun')
                if text_run:
                    text += text_run.get('content', '')
    return text


@mcp.tool()
def list_documents(max_results: int = 10) -> str:
    """Google Drive හි Documents list කරයි. Use when user says: 'list docs', 'google documents'."""
    try:
        results = _drive().files().list(
            q="mimeType='application/vnd.google-apps.document' and trashed=false",
            pageSize=max_results,
            fields="files(id, name, modifiedTime, webViewLink)"
        ).execute()
        files = results.get('files', [])
        if not files:
            return "📄 Google Documents හමු නොවීය."
        output = f"📄 GOOGLE DOCS — {len(files)} DOCUMENTS\n{'─'*40}\n"
        for f in files:
            output += (
                f"📝 {f['name']}\n"
                f"   🔑 ID: {f['id']}\n"
                f"   🔗 {f.get('webViewLink','N/A')}\n"
                f"{'─'*40}\n"
            )
        return output
    except Exception as e:
        return f"❌ Documents list දෝෂයක්: {e}"


@mcp.tool()
def get_document_content(doc_id: str) -> str:
    """Google Doc content read කරයි. Use when user says: 'read document', 'open doc'."""
    try:
        doc = _docs().documents().get(documentId=doc_id).execute()
        title = doc.get('title', 'Untitled')
        text = _extract_doc_text(doc)
        preview = text[:2000] + ("..." if len(text) > 2000 else "")
        return f"📄 DOCUMENT: {title}\n{'═'*40}\n{preview}\n{'─'*40}\n📏 Chars: {len(text)} | ID: {doc_id}"
    except Exception as e:
        return f"❌ Document read දෝෂයක්: {e}"


@mcp.tool()
def get_document_structure(doc_id: str) -> str:
    """
    Document structure (paragraphs, headings) list කරයි — edit සඳහා indices.
    Use when user says: 'document structure', 'doc outline', 'heading list'.
    """
    try:
        doc = _docs().documents().get(documentId=doc_id).execute()
        output = f"📄 STRUCTURE: {doc.get('title', 'Untitled')}\n{'─'*40}\n"
        for element in doc.get('body', {}).get('content', []):
            start = element.get('startIndex', '?')
            end = element.get('endIndex', '?')
            if 'paragraph' in element:
                style = element['paragraph'].get('paragraphStyle', {}).get('namedStyleType', 'NORMAL_TEXT')
                snippet = ""
                for run in element['paragraph'].get('elements', []):
                    tr = run.get('textRun', {})
                    snippet += tr.get('content', '')
                snippet = snippet.strip()[:60]
                output += f"  [{start}-{end}] {style}: {snippet or '(empty)'}\n"
            elif 'table' in element:
                output += f"  [{start}-{end}] TABLE\n"
        return output
    except Exception as e:
        return f"❌ Document structure දෝෂයක්: {e}"


@mcp.tool()
def create_document(title: str) -> str:
    """නව Google Doc සාදයි. Use when user says: 'create doc', 'new document'."""
    try:
        doc = _docs().documents().create(body={'title': title}).execute()
        doc_id = doc['documentId']
        return (
            f"✅ Document '{title}' සාදන ලදී!\n"
            f"   🔑 ID: {doc_id}\n"
            f"   🔗 https://docs.google.com/document/d/{doc_id}/edit\n"
            f"   💡 Use this ID for update/delete/share tools."
        )
    except Exception as e:
        return f"❌ Document සෑදීමේ දෝෂයක්: {e}"


@mcp.tool()
def append_text_to_document(doc_id: str, text: str) -> str:
    """Doc end ලෙ text append කරයි. Use when user says: 'add text to doc', 'doc ලෙ ලියන්න'."""
    try:
        end_index = _doc_end_index(doc_id)
        _docs().documents().batchUpdate(
            documentId=doc_id,
            body={'requests': [{'insertText': {'location': {'index': end_index}, 'text': '\n' + text}}]}
        ).execute()
        return f"✅ Text appended to document (ID: {doc_id})."
    except Exception as e:
        return f"❌ Text append දෝෂයක්: {e}"


@mcp.tool()
def insert_text_at_index(doc_id: str, index: int, text: str) -> str:
    """
    Specific index එකේ text insert කරයි.
    Use when user says: 'insert text in doc', 'write at position'.
    """
    try:
        _docs().documents().batchUpdate(
            documentId=doc_id,
            body={'requests': [{'insertText': {'location': {'index': index}, 'text': text}}]}
        ).execute()
        return f"✅ Text inserted at index {index}."
    except Exception as e:
        return f"❌ Insert text දෝෂයක්: {e}"


@mcp.tool()
def replace_text_in_document(doc_id: str, find_text: str, replace_text: str) -> str:
    """
    Document එකේ text replace කරයි (all occurrences).
    Use when user says: 'replace in doc', 'find replace document'.
    """
    try:
        _docs().documents().batchUpdate(
            documentId=doc_id,
            body={'requests': [{
                'replaceAllText': {
                    'containsText': {'text': find_text, 'matchCase': False},
                    'replaceText': replace_text,
                }
            }]}
        ).execute()
        return f"✅ Replaced '{find_text}' → '{replace_text}' in document."
    except Exception as e:
        return f"❌ Replace text දෝෂයක්: {e}"


@mcp.tool()
def find_replace_in_document(doc_id: str, find_text: str, replace_text: str) -> str:
    """find/replace alias. Use when user says: 'find replace doc'."""
    return replace_text_in_document(doc_id, find_text, replace_text)


@mcp.tool()
def delete_text_range(doc_id: str, start_index: int, end_index: int) -> str:
    """
    Index range delete කරයි (end_index exclusive in API).
    Use when user says: 'delete text from doc', 'remove paragraph'.
    """
    try:
        _docs().documents().batchUpdate(
            documentId=doc_id,
            body={'requests': [{
                'deleteContentRange': {'range': {'startIndex': start_index, 'endIndex': end_index}}
            }]}
        ).execute()
        return f"✅ Deleted content [{start_index}, {end_index})."
    except Exception as e:
        return f"❌ Delete range දෝෂයක්: {e}"


@mcp.tool()
def add_heading_to_document(doc_id: str, text: str, level: int = 1) -> str:
    """
    Heading add කරයි (level 1 or 2).
    Use when user says: 'add heading', 'heading to doc'.
    """
    try:
        style = 'HEADING_1' if level <= 1 else 'HEADING_2'
        end_index = _doc_end_index(doc_id)
        insert_text = '\n' + text + '\n'
        _docs().documents().batchUpdate(
            documentId=doc_id,
            body={'requests': [
                {'insertText': {'location': {'index': end_index}, 'text': insert_text}},
                {
                    'updateParagraphStyle': {
                        'range': {
                            'startIndex': end_index + 1,
                            'endIndex': end_index + 1 + len(text),
                        },
                        'paragraphStyle': {'namedStyleType': style},
                        'fields': 'namedStyleType',
                    }
                },
            ]}
        ).execute()
        return f"✅ Heading ({style}) added: '{text}'."
    except Exception as e:
        return f"❌ Add heading දෝෂයක්: {e}"


@mcp.tool()
def add_table_to_document(doc_id: str, rows: int, cols: int) -> str:
    """
    Simple table add කරයි.
    Use when user says: 'add table to doc', 'insert table'.
    """
    try:
        if rows < 1 or cols < 1 or rows > 20 or cols > 10:
            return "❌ rows 1-20, cols 1-10."
        end_index = _doc_end_index(doc_id)
        _docs().documents().batchUpdate(
            documentId=doc_id,
            body={'requests': [{
                'insertTable': {
                    'rows': rows,
                    'columns': cols,
                    'location': {'index': end_index},
                }
            }]}
        ).execute()
        return f"✅ Table {rows}x{cols} added at end of document."
    except Exception as e:
        return f"❌ Add table දෝෂයක්: {e}"


@mcp.tool()
def search_documents(query: str) -> str:
    """Documents search කරයි. Use when user says: 'find doc', 'search document'."""
    try:
        q = escape_drive_query(query)
        results = _drive().files().list(
            q=f"mimeType='application/vnd.google-apps.document' and name contains '{q}' and trashed=false",
            pageSize=10,
            fields="files(id, name, webViewLink)"
        ).execute()
        files = results.get('files', [])
        if not files:
            return f"🔍 '{query}' Documents හමු නොවීය."
        output = f"🔍 DOCS SEARCH: '{query}'\n{'─'*40}\n"
        for f in files:
            output += f"📝 {f['name']} | ID: {f['id']}\n"
        return output
    except Exception as e:
        return f"❌ Document search දෝෂයක්: {e}"


@mcp.tool()
def share_document(doc_id: str, email: str, role: str = "reader") -> str:
    """Document share කරයි. Use when user says: 'share doc', 'share document'."""
    try:
        perm = share_file(doc_id, email, role)
        return f"✅ Shared with {perm.get('emailAddress', email)} as {perm.get('role', role)}."
    except Exception as e:
        return f"❌ Share document දෝෂයක්: {e}"


@mcp.tool()
def rename_document(doc_id: str, new_title: str) -> str:
    """Document rename කරයි. Use when user says: 'rename doc', 'rename document'."""
    try:
        _drive().files().update(fileId=doc_id, body={'name': new_title}).execute()
        return f"✅ Renamed to '{new_title}'."
    except Exception as e:
        return f"❌ Rename document දෝෂයක්: {e}"


@mcp.tool()
def delete_document(doc_id: str, permanent: bool = False) -> str:
    """
    Document delete කරයි. permanent=False → trash.
    Use when user says: 'delete doc', 'remove document'.
    """
    try:
        if permanent:
            _drive().files().delete(fileId=doc_id).execute()
            return f"🗑️ Document permanently deleted (ID: {doc_id})."
        _drive().files().update(fileId=doc_id, body={'trashed': True}).execute()
        return f"🗑️ Document moved to trash (ID: {doc_id})."
    except Exception as e:
        return f"❌ Delete document දෝෂයක්: {e}"


@mcp.tool()
def export_document(doc_id: str, local_path: str, export_format: str = "pdf") -> str:
    """
    Document export කර local file ලෙ save කරයි.
    Use when user says: 'export doc', 'download doc as pdf'.
    export_format: pdf | docx
    """
    try:
        mime_map = {'pdf': 'application/pdf', 'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}
        mime = mime_map.get(export_format.lower())
        if not mime:
            return "❌ export_format must be pdf or docx."
        parent = os.path.dirname(os.path.abspath(local_path))
        if parent and not os.path.isdir(parent):
            return f"❌ Directory not found: {parent}"
        request = _drive().files().export_media(fileId=doc_id, mimeType=mime)
        fh = io.FileIO(local_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.close()
        return f"✅ Exported to {local_path} ({export_format})."
    except Exception as e:
        return f"❌ Export document දෝෂයක්: {e}"


if __name__ == "__main__":
    mcp.run(transport='stdio')
