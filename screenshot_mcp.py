import os
import datetime
import subprocess
from PIL import ImageGrab
import pyperclip
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Syntiox-Screenshot-Tool")

# Screenshots save කෙරෙන default folder
SCREENSHOT_DIR = os.path.join(os.path.expanduser("~"), "Pictures", "MCP_Screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def _timestamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 1: Full Screen Screenshot
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def take_screenshot(save_path: str = "") -> str:
    """
    Full screen screenshot ගනී.
    Use when user says: 'take screenshot', 'capture screen', 'screenshot'.
    save_path: optional custom path. Default: ~/Pictures/MCP_Screenshots/
    """
    try:
        img  = ImageGrab.grab()
        path = save_path or os.path.join(SCREENSHOT_DIR, f"screenshot_{_timestamp()}.png")
        img.save(path)
        size = os.path.getsize(path)
        return (
            f"📸 Screenshot ගන්නා ලදී!\n"
            f"  📁 Path : {path}\n"
            f"  📐 Size : {img.width}x{img.height} px\n"
            f"  💾 File : {size//1024} KB"
        )
    except Exception as e:
        return f"❌ Screenshot error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 2: Region Screenshot
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def take_region_screenshot(x: int, y: int, width: int, height: int, save_path: str = "") -> str:
    """
    Screen ලෙ specific region/area capture කරයි.
    Use when user says: 'capture region', 'screenshot part of screen', 'region screenshot'.
    x, y: top-left corner coordinates
    width, height: region dimensions in pixels
    """
    try:
        img  = ImageGrab.grab(bbox=(x, y, x + width, y + height))
        path = save_path or os.path.join(SCREENSHOT_DIR, f"region_{_timestamp()}.png")
        img.save(path)
        size = os.path.getsize(path)
        return (
            f"📸 Region screenshot ගන්නා ලදී!\n"
            f"  📐 Region : ({x}, {y}) → {width}x{height} px\n"
            f"  📁 Path   : {path}\n"
            f"  💾 File   : {size//1024} KB"
        )
    except Exception as e:
        return f"❌ Region screenshot error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 3: Screenshot to Clipboard
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def screenshot_to_clipboard() -> str:
    """
    Screenshot ගෙන clipboard ලෙ copy කරයි (Windows Snip-style).
    Use when user says: 'screenshot to clipboard', 'copy screenshot', 'screen grab'.
    """
    try:
        # Windows built-in snipping tool shortcut via PowerShell
        subprocess.run(
            ['powershell', '-command', 'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait("%{PRTSC}")'],
            capture_output=True, timeout=3
        )
        # Also save a file backup
        img  = ImageGrab.grab()
        path = os.path.join(SCREENSHOT_DIR, f"clipboard_{_timestamp()}.png")
        img.save(path)
        return (
            f"📸 Screenshot clipboard ලෙ copy කරන ලදී!\n"
            f"  📐 {img.width}x{img.height} px\n"
            f"  📁 Backup: {path}"
        )
    except Exception as e:
        return f"❌ Screenshot to clipboard error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 4: List Recent Screenshots
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def list_recent_screenshots(max_results: int = 10) -> str:
    """
    Recent screenshots list කරයි.
    Use when user says: 'show screenshots', 'list screenshots', 'recent captures'.
    """
    try:
        files = sorted(
            [f for f in os.listdir(SCREENSHOT_DIR) if f.endswith('.png')],
            reverse=True
        )[:max_results]

        if not files:
            return f"📸 Screenshots හමු නොවීය in {SCREENSHOT_DIR}"

        output = f"📸 RECENT SCREENSHOTS ({len(files)})\n{'─'*45}\n"
        for fname in files:
            fp   = os.path.join(SCREENSHOT_DIR, fname)
            size = os.path.getsize(fp) // 1024
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fp)).strftime('%Y-%m-%d %H:%M')
            output += f"  🖼️  {fname}\n     💾 {size} KB | 🕐 {mtime}\n"
        output += f"{'─'*45}\n📁 Folder: {SCREENSHOT_DIR}"
        return output
    except Exception as e:
        return f"❌ List screenshots error: {e}"


if __name__ == "__main__":
    mcp.run(transport='stdio')
