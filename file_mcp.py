import os
import glob
import shutil
import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Syntiox-FileSystem-Tool")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 1: Read File
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def read_file(file_path: str) -> str:
    """
    Local file content ලබාගනී.
    Use when user says: 'read file', 'open file', 'file content', 'file read කරන්න'.
    """
    try:
        if not os.path.exists(file_path):
            return f"❌ File නොමැත: {file_path}"
        size = os.path.getsize(file_path)
        if size > 500_000:
            return f"⚠️ File ගොඩක් විශාලයි ({size//1024} KB). 500KB limit."
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        lines   = content.count('\n') + 1
        preview = content[:3000] + ("...\n[truncated]" if len(content) > 3000 else "")
        return (
            f"📄 FILE: {os.path.basename(file_path)}\n"
            f"📏 Size: {size} bytes | Lines: {lines}\n"
            f"{'═'*40}\n"
            f"{preview}"
        )
    except Exception as e:
        return f"❌ File read error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 2: Write File
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def write_file(file_path: str, content: str, overwrite: bool = False) -> str:
    """
    Local file ලෙ content ලියයි.
    Use when user says: 'write file', 'create file', 'save to file', 'file ලෙ ලියන්න'.
    overwrite=True නොමැතිව existing file overwrite නොකෙරේ.
    """
    try:
        if os.path.exists(file_path) and not overwrite:
            return f"⚠️ File දැනටමත් ඇත: {file_path}\n(overwrite=True set කරන්න overwrite කිරීමට)"
        os.makedirs(os.path.dirname(file_path), exist_ok=True) if os.path.dirname(file_path) else None
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        size = os.path.getsize(file_path)
        return f"✅ File ලියන ලදී: {file_path} ({size} bytes)"
    except Exception as e:
        return f"❌ File write error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 3: List Directory
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def list_directory(directory_path: str = ".") -> str:
    """
    Folder contents list කරයි.
    Use when user says: 'list files', 'folder contents', 'what files', 'dir'.
    """
    try:
        if not os.path.exists(directory_path):
            return f"❌ Folder නොමැත: {directory_path}"
        items = os.listdir(directory_path)
        dirs  = sorted([i for i in items if os.path.isdir(os.path.join(directory_path, i))])
        files = sorted([i for i in items if os.path.isfile(os.path.join(directory_path, i))])

        output = f"📂 DIRECTORY: {os.path.abspath(directory_path)}\n{'─'*45}\n"
        output += f"📁 Folders ({len(dirs)}):\n"
        for d in dirs:
            output += f"  📁 {d}/\n"
        output += f"\n📄 Files ({len(files)}):\n"
        for fname in files:
            fpath = os.path.join(directory_path, fname)
            size  = os.path.getsize(fpath)
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fpath)).strftime('%Y-%m-%d %H:%M')
            size_str = f"{size:,} B" if size < 1024 else (f"{size//1024} KB" if size < 1024*1024 else f"{size//1024//1024} MB")
            output += f"  📄 {fname:<35} {size_str:>10}  {mtime}\n"
        output += f"{'─'*45}\n"
        output += f"Total: {len(dirs)} folders, {len(files)} files"
        return output
    except Exception as e:
        return f"❌ Directory list error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 4: Search Files
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def search_files(directory: str, pattern: str, recursive: bool = True) -> str:
    """
    Files search කරයි (name pattern).
    Use when user says: 'find files', 'search files', 'file හොයන්න'.
    pattern examples: '*.py', '*.txt', 'report*', '*2024*'
    """
    try:
        if not os.path.exists(directory):
            return f"❌ Directory නොමැත: {directory}"
        search = os.path.join(directory, '**', pattern) if recursive else os.path.join(directory, pattern)
        found  = glob.glob(search, recursive=recursive)

        if not found:
            return f"🔍 '{pattern}' pattern හමු නොවීය in '{directory}'."

        output = f"🔍 SEARCH: '{pattern}' — {len(found)} FILES\n{'─'*45}\n"
        for fp in found[:30]:
            size     = os.path.getsize(fp)
            size_str = f"{size:,} B" if size < 1024 else f"{size//1024} KB"
            output  += f"  📄 {fp}\n     📏 {size_str}\n"
        if len(found) > 30:
            output += f"\n... and {len(found)-30} more files."
        return output
    except Exception as e:
        return f"❌ Search error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 5: Get File Info
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def get_file_info(file_path: str) -> str:
    """
    File metadata (size, dates, type) ලබාගනී.
    Use when user says: 'file info', 'file details', 'file size'.
    """
    try:
        if not os.path.exists(file_path):
            return f"❌ File නොමැත: {file_path}"
        stat     = os.stat(file_path)
        size     = stat.st_size
        size_str = f"{size:,} B" if size < 1024 else (f"{size//1024:,} KB" if size < 1024*1024 else f"{size//1024//1024:.1f} MB")
        created  = datetime.datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
        modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        ext      = os.path.splitext(file_path)[1] or '(no extension)'
        return (
            f"📄 FILE INFO\n{'═'*35}\n"
            f"  Name     : {os.path.basename(file_path)}\n"
            f"  Path     : {os.path.abspath(file_path)}\n"
            f"  Type     : {ext}\n"
            f"  Size     : {size_str}\n"
            f"  Created  : {created}\n"
            f"  Modified : {modified}\n"
            f"  Is Dir   : {'Yes' if os.path.isdir(file_path) else 'No'}\n"
        )
    except Exception as e:
        return f"❌ File info error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 6: Delete File
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def delete_file(file_path: str) -> str:
    """
    File delete කරයි.
    Use when user says: 'delete file', 'remove file', 'file delete කරන්න'.
    """
    try:
        if not os.path.exists(file_path):
            return f"❌ File නොමැත: {file_path}"
        name = os.path.basename(file_path)
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)
            return f"🗑️ Folder '{name}' delete කරන ලදී."
        else:
            os.remove(file_path)
            return f"🗑️ File '{name}' delete කරන ලදී."
    except Exception as e:
        return f"❌ Delete error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 7: Create Directory
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def create_directory(directory_path: str) -> str:
    """
    Folder/directory සාදයි.
    Use when user says: 'create folder', 'make directory', 'folder හදන්න'.
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return f"✅ Folder සාදන ලදී: {os.path.abspath(directory_path)}"
    except Exception as e:
        return f"❌ Directory create error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 8: Copy File
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def copy_file(source_path: str, destination_path: str) -> str:
    """
    File copy කරයි.
    Use when user says: 'copy file', 'duplicate file', 'file copy කරන්න'.
    """
    try:
        if not os.path.exists(source_path):
            return f"❌ Source file නොමැත: {source_path}"
        shutil.copy2(source_path, destination_path)
        size = os.path.getsize(destination_path)
        return f"✅ File copy කරන ලදී:\n  From: {source_path}\n  To  : {destination_path}\n  Size: {size:,} bytes"
    except Exception as e:
        return f"❌ Copy error: {e}"


if __name__ == "__main__":
    mcp.run(transport='stdio')
