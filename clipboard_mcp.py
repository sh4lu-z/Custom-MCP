import pyperclip
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Syntiox-Clipboard-Tool")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 1: Read Clipboard
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def get_clipboard() -> str:
    """
    Clipboard ලෙ ඇති text ලබාගනී.
    Use when user says: 'clipboard', 'what did I copy', 'paste content', 'clipboard read කරන්න'.
    """
    try:
        text = pyperclip.paste()
        if not text:
            return "📋 Clipboard හිස් (empty)."
        preview = text[:500] + ("..." if len(text) > 500 else "")
        return (
            f"📋 CLIPBOARD CONTENT\n{'─'*35}\n"
            f"{preview}\n"
            f"{'─'*35}\n"
            f"📏 Total chars: {len(text)}"
        )
    except Exception as e:
        return f"❌ Clipboard read error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 2: Write to Clipboard
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def set_clipboard(text: str) -> str:
    """
    Text clipboard ලෙ copy කරයි.
    Use when user says: 'copy to clipboard', 'set clipboard', 'clipboard ලෙ දාන්න'.
    """
    try:
        pyperclip.copy(text)
        preview = text[:100] + ("..." if len(text) > 100 else "")
        return f"✅ Clipboard ලෙ copy කරන ලදී: '{preview}'"
    except Exception as e:
        return f"❌ Clipboard write error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 3: Clear Clipboard
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def clear_clipboard() -> str:
    """
    Clipboard clear කරයි.
    Use when user says: 'clear clipboard', 'empty clipboard'.
    """
    try:
        pyperclip.copy("")
        return "🧹 Clipboard clear කරන ලදී."
    except Exception as e:
        return f"❌ Clipboard clear error: {e}"


if __name__ == "__main__":
    mcp.run(transport='stdio')
