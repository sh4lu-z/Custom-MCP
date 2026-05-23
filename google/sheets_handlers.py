"""
📊 Google Sheets Handler Tools
docs.google.com/spreadsheets
"""
import json
from mcp.server.fastmcp import FastMCP
from google_common import get_service, share_file

mcp = FastMCP("Google-Sheets-Tools")


def _sheets():
    return get_service('sheets', 'v4')


def _drive():
    return get_service('drive', 'v3')


def _sheet_id_by_name(spreadsheet_id: str, sheet_name: str) -> int:
    meta = _sheets().spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for s in meta.get('sheets', []):
        p = s.get('properties', {})
        if p.get('title') == sheet_name:
            return p['sheetId']
    raise ValueError(f"Sheet tab '{sheet_name}' not found")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LIST / CREATE / READ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def list_spreadsheets(max_results: int = 10) -> str:
    """
    Google Drive හි ඇති Spreadsheets list කරයි.
    Use when user says: 'list sheets', 'google sheets', 'spreadsheets'.
    """
    try:
        svc = _drive()
        results = svc.files().list(
            q="mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
            pageSize=max_results,
            fields="files(id, name, modifiedTime, webViewLink)"
        ).execute()
        files = results.get('files', [])
        if not files:
            return "📊 Spreadsheets හමු නොවීය."
        output = f"📊 GOOGLE SHEETS — {len(files)} SPREADSHEETS\n{'─'*40}\n"
        for f in files:
            output += (
                f"📊 {f['name']}\n"
                f"   🕐 Modified : {f.get('modifiedTime','')[:10]}\n"
                f"   🔗 Link     : {f.get('webViewLink','N/A')}\n"
                f"   🔑 ID       : {f['id']}\n"
                f"{'─'*40}\n"
            )
        return output
    except Exception as e:
        return f"❌ Spreadsheets list කිරීමේ දෝෂයක්: {e}"


@mcp.tool()
def create_spreadsheet(title: str) -> str:
    """
    නව Google Spreadsheet සාදයි.
    Use when user says: 'create sheet', 'new spreadsheet', 'new excel'.
    """
    try:
        result = _sheets().spreadsheets().create(body={'properties': {'title': title}}).execute()
        sid = result['spreadsheetId']
        link = f"https://docs.google.com/spreadsheets/d/{sid}/edit"
        return (
            f"✅ Spreadsheet '{title}' සාදන ලදී!\n"
            f"   🔑 ID   : {sid}\n"
            f"   🔗 Link : {link}\n"
            f"   💡 Use this ID for update/delete/share tools."
        )
    except Exception as e:
        return f"❌ Spreadsheet සෑදීමේ දෝෂයක්: {e}"


@mcp.tool()
def read_sheet_data(spreadsheet_id: str, range_name: str = "Sheet1!A1:Z100") -> str:
    """
    Google Sheet cell data ලබාගනී.
    Use when user says: 'read sheet', 'get sheet data', 'sheet values'.
    """
    if not spreadsheet_id.strip():
        return "❌ spreadsheet_id හිස් විය නොහැක."
    try:
        result = _sheets().spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name
        ).execute()
        values = result.get('values', [])
        if not values:
            return f"📊 Range '{range_name}' හි data නොමැත."
        output = f"📊 SHEET DATA — {range_name}\n{'─'*40}\n"
        for i, row in enumerate(values[:50], 1):
            output += f"  Row {i:02}: {' | '.join(str(c) for c in row)}\n"
        if len(values) > 50:
            output += f"  ... (total {len(values)} rows)\n"
        return output
    except Exception as e:
        return f"❌ Sheet read කිරීමේ දෝෂයක්: {e}"


@mcp.tool()
def write_sheet_data(spreadsheet_id: str, range_name: str, values_json: str) -> str:
    """
    Google Sheet cells ලෙ data ලියයි / edit cells / update range.
    Use when user says: 'write to sheet', 'update cells', 'edit cell', 'sheet ලෙ දාන්න', 'sheet එකේ ලියන්න'.
    values_json: JSON 2D array — e.g. '[["Name","Age"],["Alice","25"]]'
    """
    if not spreadsheet_id.strip():
        return "❌ spreadsheet_id හිස් විය නොහැක."
    try:
        values = json.loads(values_json)
        result = _sheets().spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body={'values': values}
        ).execute()
        updated = result.get('updatedCells', 0)
        return f"✅ {updated} cells Sheet '{range_name}' ලෙ ලියන ලදී."
    except json.JSONDecodeError:
        return '❌ values_json invalid JSON. Example: [["Name","Age"],["Alice","25"]]'
    except Exception as e:
        return f"❌ Sheet write දෝෂයක්: {e}"


@mcp.tool()
def update_single_cell(spreadsheet_id: str, cell_range: str, value: str) -> str:
    """
    එක cell එක edit කරයි (e.g. Sheet1!B3).
    Use when user says: 'edit cell', 'update cell', 'change cell value', 'cell edit කරන්න'.
    """
    if not spreadsheet_id.strip():
        return "❌ spreadsheet_id හිස් විය නොහැක."
    try:
        result = _sheets().spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=cell_range,
            valueInputOption='USER_ENTERED',
            body={'values': [[value]]}
        ).execute()
        return f"✅ Cell '{cell_range}' = '{value}' ({result.get('updatedCells', 1)} cell)."
    except Exception as e:
        return f"❌ Cell update දෝෂයක්: {e}"


@mcp.tool()
def update_cells_batch(spreadsheet_id: str, batch_json: str) -> str:
    """
    Multiple ranges එකවර update කරයි.
    Use when user says: 'batch update sheet', 'update multiple ranges'.
    batch_json: '{"Sheet1!A1":"Hi","Sheet1!B2":"Bye"}' or valueRanges array JSON.
    """
    try:
        data = json.loads(batch_json)
        if isinstance(data, dict):
            value_ranges = [
                {'range': k, 'values': [[v]] if not isinstance(v, list) else v}
                for k, v in data.items()
            ]
        else:
            value_ranges = data
        result = _sheets().spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'valueInputOption': 'USER_ENTERED', 'data': value_ranges}
        ).execute()
        total = result.get('totalUpdatedCells', 0)
        return f"✅ Batch update: {total} cells updated."
    except json.JSONDecodeError:
        return "❌ batch_json invalid JSON."
    except Exception as e:
        return f"❌ Batch update දෝෂයක්: {e}"


@mcp.tool()
def read_sheet_ranges_batch(spreadsheet_id: str, ranges_csv: str) -> str:
    """
    Multiple ranges එකවර read කරයි.
    Use when user says: 'read multiple ranges', 'batch read sheet'.
    ranges_csv: comma-separated — 'Sheet1!A1:B2,Sheet2!A1:C5'
    """
    try:
        ranges = [r.strip() for r in ranges_csv.split(',') if r.strip()]
        result = _sheets().spreadsheets().values().batchGet(
            spreadsheetId=spreadsheet_id, ranges=ranges
        ).execute()
        output = f"📊 BATCH READ — {len(ranges)} ranges\n{'─'*40}\n"
        for vr in result.get('valueRanges', []):
            output += f"\n📋 {vr.get('range', '?')}:\n"
            for row in vr.get('values', [])[:20]:
                output += f"  {' | '.join(str(c) for c in row)}\n"
        return output
    except Exception as e:
        return f"❌ Batch read දෝෂයක්: {e}"


@mcp.tool()
def append_row_to_sheet(spreadsheet_id: str, sheet_name: str, row_values: str) -> str:
    """
    Google Sheet ලෙ නව row append කරයි.
    Use when user says: 'add row', 'append row to sheet'.
    row_values: comma-separated — 'Alice,25,Engineer'
    """
    try:
        row = [v.strip() for v in row_values.split(',')]
        result = _sheets().spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=sheet_name,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={'values': [row]}
        ).execute()
        updated_range = result.get('updates', {}).get('updatedRange', '')
        return f"✅ Row append කරන ලදී. ({updated_range})"
    except Exception as e:
        return f"❌ Row append දෝෂයක්: {e}"


@mcp.tool()
def get_sheet_names(spreadsheet_id: str) -> str:
    """
    Spreadsheet හි sheet tabs list කරයි.
    Use when user says: 'sheet names', 'tabs in spreadsheet'.
    """
    try:
        result = _sheets().spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = result.get('sheets', [])
        title = result.get('properties', {}).get('title', 'Unknown')
        output = f"📊 '{title}' SHEET TABS\n{'─'*30}\n"
        for s in sheets:
            p = s.get('properties', {})
            output += f"  📋 {p.get('title','?')}  (Index: {p.get('index',0)}, ID: {p.get('sheetId','')})\n"
        return output
    except Exception as e:
        return f"❌ Sheet names ලබාගැනීමේ දෝෂයක්: {e}"


@mcp.tool()
def clear_sheet_range(spreadsheet_id: str, range_name: str) -> str:
    """
    Google Sheet range clear කරයි.
    Use when user says: 'clear sheet', 'delete sheet data', 'range clear කරන්න'.
    """
    try:
        _sheets().spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id, range=range_name
        ).execute()
        return f"🧹 Range '{range_name}' clear කරන ලදී."
    except Exception as e:
        return f"❌ Clear range දෝෂයක්: {e}"


@mcp.tool()
def find_replace_in_sheet(spreadsheet_id: str, sheet_id: int, find_text: str, replace_text: str) -> str:
    """
    Sheet එකේ text find & replace කරයි.
    Use when user says: 'find replace sheet', 'replace in spreadsheet'.
    sheet_id: numeric tab ID from get_sheet_names.
    """
    try:
        result = _sheets().spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': [{
                'findReplace': {
                    'find': find_text,
                    'replacement': replace_text,
                    'sheetId': sheet_id,
                    'matchCase': False,
                    'allSheets': False,
                }
            }]}
        ).execute()
        reps = result.get('replies', [{}])[0].get('findReplace', {}).get('occurrencesChanged', 0)
        return f"✅ Replaced {reps} occurrence(s): '{find_text}' → '{replace_text}'."
    except Exception as e:
        return f"❌ Find/replace දෝෂයක්: {e}"


@mcp.tool()
def add_sheet_tab(spreadsheet_id: str, tab_name: str) -> str:
    """
    Spreadsheet ලෙ නව sheet tab add කරයි.
    Use when user says: 'add sheet tab', 'new tab', 'create worksheet'.
    """
    try:
        result = _sheets().spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': [{'addSheet': {'properties': {'title': tab_name}}}]}
        ).execute()
        sid = result['replies'][0]['addSheet']['properties']['sheetId']
        return f"✅ Tab '{tab_name}' added (sheetId: {sid})."
    except Exception as e:
        return f"❌ Add tab දෝෂයක්: {e}"


@mcp.tool()
def delete_sheet_tab(spreadsheet_id: str, sheet_name: str) -> str:
    """
    Sheet tab delete කරයි.
    Use when user says: 'delete sheet tab', 'remove worksheet'.
    """
    try:
        sid = _sheet_id_by_name(spreadsheet_id, sheet_name)
        _sheets().spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': [{'deleteSheet': {'sheetId': sid}}]}
        ).execute()
        return f"🗑️ Tab '{sheet_name}' deleted."
    except Exception as e:
        return f"❌ Delete tab දෝෂයක්: {e}"


@mcp.tool()
def rename_sheet_tab(spreadsheet_id: str, old_name: str, new_name: str) -> str:
    """
    Sheet tab rename කරයි.
    Use when user says: 'rename sheet tab', 'rename worksheet'.
    """
    try:
        sid = _sheet_id_by_name(spreadsheet_id, old_name)
        _sheets().spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': [{
                'updateSheetProperties': {
                    'properties': {'sheetId': sid, 'title': new_name},
                    'fields': 'title',
                }
            }]}
        ).execute()
        return f"✅ Tab renamed: '{old_name}' → '{new_name}'."
    except Exception as e:
        return f"❌ Rename tab දෝෂයක්: {e}"


@mcp.tool()
def duplicate_sheet_tab(spreadsheet_id: str, sheet_name: str, new_name: str = "") -> str:
    """
    Sheet tab duplicate කරයි.
    Use when user says: 'duplicate sheet tab', 'copy worksheet'.
    """
    try:
        sid = _sheet_id_by_name(spreadsheet_id, sheet_name)
        req = {'duplicateSheet': {'sourceSheetId': sid}}
        if new_name:
            req['duplicateSheet']['newSheetName'] = new_name
        result = _sheets().spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body={'requests': [{'duplicateSheet': req['duplicateSheet']}]}
        ).execute()
        new_sid = result['replies'][0]['duplicateSheet']['properties']['sheetId']
        return f"✅ Tab duplicated (new sheetId: {new_sid})."
    except Exception as e:
        return f"❌ Duplicate tab දෝෂයක්: {e}"


@mcp.tool()
def format_sheet_cells(
    spreadsheet_id: str,
    sheet_name: str,
    start_row: int,
    start_col: int,
    end_row: int,
    end_col: int,
    bold: bool = False,
    bg_color_hex: str = "",
) -> str:
    """
    Cells format කරයි (bold, background color).
    Use when user says: 'format cells', 'bold cells', 'color cells'.
    Rows/cols: 0-based. bg_color_hex: e.g. '#FFFF00' or empty.
    """
    try:
        sid = _sheet_id_by_name(spreadsheet_id, sheet_name)
        fmt = {}
        fields = []
        if bold:
            fmt['textFormat'] = {'bold': True}
            fields.append('userEnteredFormat.textFormat.bold')
        if bg_color_hex and bg_color_hex.startswith('#') and len(bg_color_hex) == 7:
            r = int(bg_color_hex[1:3], 16) / 255
            g = int(bg_color_hex[3:5], 16) / 255
            b = int(bg_color_hex[5:7], 16) / 255
            fmt['backgroundColor'] = {'red': r, 'green': g, 'blue': b}
            fields.append('userEnteredFormat.backgroundColor')
        if not fields:
            return "❌ Specify bold=True and/or bg_color_hex='#RRGGBB'."
        _sheets().spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': [{
                'repeatCell': {
                    'range': {
                        'sheetId': sid,
                        'startRowIndex': start_row,
                        'endRowIndex': end_row + 1,
                        'startColumnIndex': start_col,
                        'endColumnIndex': end_col + 1,
                    },
                    'cell': {'userEnteredFormat': fmt},
                    'fields': ','.join(fields),
                }
            }]}
        ).execute()
        return f"✅ Formatted range on '{sheet_name}'."
    except Exception as e:
        return f"❌ Format cells දෝෂයක්: {e}"


@mcp.tool()
def auto_resize_columns(spreadsheet_id: str, sheet_name: str, start_col: int, end_col: int) -> str:
    """
    Columns auto-resize කරයි.
    Use when user says: 'auto resize columns', 'fit column width'.
    """
    try:
        sid = _sheet_id_by_name(spreadsheet_id, sheet_name)
        _sheets().spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': [{
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': sid,
                        'dimension': 'COLUMNS',
                        'startIndex': start_col,
                        'endIndex': end_col + 1,
                    }
                }
            }]}
        ).execute()
        return f"✅ Columns {start_col}-{end_col} auto-resized on '{sheet_name}'."
    except Exception as e:
        return f"❌ Auto-resize දෝෂයක්: {e}"


@mcp.tool()
def sort_sheet_range(
    spreadsheet_id: str,
    sheet_name: str,
    start_row: int,
    end_row: int,
    start_col: int,
    end_col: int,
    sort_column_index: int,
    ascending: bool = True,
) -> str:
    """
    Range sort කරයි.
    Use when user says: 'sort sheet', 'sort rows', 'sort column'.
    sort_column_index: 0-based column within the range.
    """
    try:
        sid = _sheet_id_by_name(spreadsheet_id, sheet_name)
        _sheets().spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': [{
                'sortRange': {
                    'range': {
                        'sheetId': sid,
                        'startRowIndex': start_row,
                        'endRowIndex': end_row + 1,
                        'startColumnIndex': start_col,
                        'endColumnIndex': end_col + 1,
                    },
                    'sortSpecs': [{
                        'dimensionIndex': sort_column_index,
                        'sortOrder': 'ASCENDING' if ascending else 'DESCENDING',
                    }],
                }
            }]}
        ).execute()
        return f"✅ Sorted range on '{sheet_name}'."
    except Exception as e:
        return f"❌ Sort දෝෂයක්: {e}"


@mcp.tool()
def copy_spreadsheet(spreadsheet_id: str, new_title: str) -> str:
    """
    Spreadsheet copy කරයි.
    Use when user says: 'copy spreadsheet', 'duplicate sheet file'.
    """
    try:
        result = _drive().files().copy(
            fileId=spreadsheet_id, body={'name': new_title}
        ).execute()
        nid = result['id']
        return (
            f"✅ Copied to '{new_title}'.\n"
            f"   🔑 ID: {nid}\n"
            f"   🔗 https://docs.google.com/spreadsheets/d/{nid}/edit"
        )
    except Exception as e:
        return f"❌ Copy spreadsheet දෝෂයක්: {e}"


@mcp.tool()
def share_spreadsheet(spreadsheet_id: str, email: str, role: str = "reader") -> str:
    """
    Spreadsheet share කරයි.
    Use when user says: 'share spreadsheet', 'share sheet with email'.
    role: reader | writer | commenter
    """
    try:
        perm = share_file(spreadsheet_id, email, role)
        return f"✅ Shared with {perm.get('emailAddress', email)} as {perm.get('role', role)}."
    except Exception as e:
        return f"❌ Share spreadsheet දෝෂයක්: {e}"


@mcp.tool()
def delete_spreadsheet(spreadsheet_id: str) -> str:
    """
    Spreadsheet permanently delete කරයි.
    Use when user says: 'delete spreadsheet', 'remove sheet file'.
    """
    try:
        _drive().files().delete(fileId=spreadsheet_id).execute()
        return f"🗑️ Spreadsheet (ID: {spreadsheet_id}) deleted."
    except Exception as e:
        return f"❌ Delete spreadsheet දෝෂයක්: {e}"


if __name__ == "__main__":
    mcp.run(transport='stdio')
