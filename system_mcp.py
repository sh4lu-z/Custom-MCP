import os
import platform
import subprocess
import datetime
import psutil
import GPUtil
import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Syntiox-System-Controller")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 1: System Stats
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def get_system_stats() -> str:
    """CPU, RAM, Disk, GPU, VRAM, Network stats ලබාදෙයි."""
    cpu    = psutil.cpu_percent(interval=1)
    ram    = psutil.virtual_memory()
    disk   = psutil.disk_usage('/')
    net    = psutil.net_io_counters()
    boot   = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.datetime.now() - boot

    gpus      = GPUtil.getGPUs()
    gpu_lines = ""
    if gpus:
        for g in gpus:
            gpu_lines += f"  🎮 GPU      : {g.name}\n"
            gpu_lines += f"  📊 GPU Load : {g.load*100:.1f}%\n"
            gpu_lines += f"  🧠 VRAM     : {g.memoryUsed:.0f} MB / {g.memoryTotal:.0f} MB\n"
            gpu_lines += f"  🌡️  GPU Temp : {g.temperature}°C\n"
    else:
        gpu_lines = "  🎮 GPU      : N/A\n"

    sent_mb = net.bytes_sent / 1024 / 1024
    recv_mb = net.bytes_recv / 1024 / 1024

    return (
        f"💻 SYSTEM STATS\n{'═'*35}\n"
        f"  🖥️  CPU     : {cpu}% ({psutil.cpu_count()} cores)\n"
        f"  🧠 RAM     : {ram.percent}% ({ram.used//1024//1024} MB / {ram.total//1024//1024} MB)\n"
        f"  💾 Disk    : {disk.percent}% ({disk.used//1024//1024//1024} GB / {disk.total//1024//1024//1024} GB)\n"
        f"{gpu_lines}"
        f"  🌐 Net ↑   : {sent_mb:.1f} MB sent\n"
        f"  🌐 Net ↓   : {recv_mb:.1f} MB received\n"
        f"  ⏱️  Uptime  : {str(uptime).split('.')[0]}\n"
        f"  🖥️  OS      : {platform.system()} {platform.release()}\n"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 2: Set Brightness
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def set_brightness(level: int) -> str:
    """Screen brightness 0-100 ලෙ සකසයි."""
    level = max(0, min(100, level))
    sbc.set_brightness(level)
    return f"☀️ Brightness {level}% ලෙ සකසන ලදී."


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 3: Set Volume
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def set_volume(level: int) -> str:
    """System volume 0-100 ලෙ සකසයි."""
    try:
        level   = max(0, min(100, level))
        scalar  = level / 100.0
        speakers = AudioUtilities.GetSpeakers()

        # pycaw නව versions AudioDevice wrapper return කරයි (_dev හරහා COM object ගනී)
        # පරාණ versions direct IMMDevice COM object return කරයි
        try:
            interface = speakers.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        except AttributeError:
            interface = speakers._dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)

        volume = interface.QueryInterface(IAudioEndpointVolume)
        volume.SetMasterVolumeLevelScalar(scalar, None)
        return f"🔊 Volume {level}% ලෙ සකසන ලදී."
    except Exception as e:
        return f"❌ Volume error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 4: List Running Processes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def list_running_processes(sort_by: str = "cpu", limit: int = 15) -> str:
    """
    Running processes list කරයි.
    sort_by: 'cpu' or 'memory'
    """
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
        try:
            procs.append(p.info)
        except Exception:
            pass

    key   = 'memory_percent' if sort_by == 'memory' else 'cpu_percent'
    procs = sorted(procs, key=lambda x: x.get(key, 0), reverse=True)[:limit]

    output = f"⚙️  TOP {limit} PROCESSES (by {sort_by.upper()})\n{'─'*45}\n"
    output += f"  {'PID':>6}  {'CPU%':>6}  {'MEM%':>6}  {'Name'}\n"
    output += f"  {'─'*6}  {'─'*6}  {'─'*6}  {'─'*25}\n"
    for p in procs:
        output += (
            f"  {p['pid']:>6}  {p.get('cpu_percent',0):>6.1f}  "
            f"{p.get('memory_percent',0):>6.1f}  {p.get('name','?')[:30]}\n"
        )
    return output


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 5: Kill Process
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def kill_process(process_name: str) -> str:
    """
    Process name ෙකන් process kill කරයි.
    Use when user says: 'kill process', 'close app', 'terminate program'.
    """
    killed = []
    errors = []
    for p in psutil.process_iter(['pid', 'name']):
        try:
            if process_name.lower() in p.info['name'].lower():
                p.kill()
                killed.append(f"{p.info['name']} (PID: {p.info['pid']})")
        except Exception as e:
            errors.append(str(e))

    if killed:
        return f"✅ Killed: {', '.join(killed)}"
    elif errors:
        return f"❌ Error killing '{process_name}': {'; '.join(errors)}"
    else:
        return f"⚠️ '{process_name}' process හමු නොවීය."


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 6: Battery Status
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def get_battery_status() -> str:
    """Battery level, charging status ලබාදෙයි."""
    batt = psutil.sensors_battery()
    if batt is None:
        return "🔌 Battery නොමැත (Desktop PC)."
    pct       = batt.percent
    plugged   = batt.power_plugged
    secs_left = batt.secsleft

    time_str = ""
    if secs_left != psutil.POWER_TIME_UNLIMITED and secs_left > 0:
        h, m = divmod(secs_left // 60, 60)
        time_str = f" (~{h}h {m}m remaining)"

    bar   = "█" * (pct // 10) + "░" * (10 - pct // 10)
    emoji = "🔌" if plugged else ("🔋" if pct > 20 else "🪫")
    return (
        f"{emoji} BATTERY STATUS\n{'─'*30}\n"
        f"  Level   : {pct:.0f}% [{bar}]\n"
        f"  Status  : {'⚡ Charging' if plugged else '🔋 On Battery'}\n"
        f"  Time    : {time_str or 'Calculating...'}\n"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 7: System Uptime
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def get_system_uptime() -> str:
    """System uptime සහ boot time ලබාදෙයි."""
    boot   = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.datetime.now() - boot
    h, rem = divmod(int(uptime.total_seconds()), 3600)
    m, s   = divmod(rem, 60)
    return (
        f"⏱️ SYSTEM UPTIME\n{'─'*30}\n"
        f"  Boot Time : {boot.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"  Uptime    : {h}h {m}m {s}s\n"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 8: Network Stats
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def get_network_stats() -> str:
    """Network interface stats ලබාදෙයි."""
    net   = psutil.net_io_counters(pernic=True)
    addrs = psutil.net_if_addrs()
    output = f"🌐 NETWORK STATS\n{'─'*40}\n"
    for nic, stats in net.items():
        if stats.bytes_sent == 0 and stats.bytes_recv == 0:
            continue
        sent_mb = stats.bytes_sent / 1024 / 1024
        recv_mb = stats.bytes_recv / 1024 / 1024
        ip      = next(
            (a.address for a in addrs.get(nic, []) if a.family.name == 'AF_INET'), 'N/A'
        )
        output += (
            f"  📡 {nic}\n"
            f"     IP  : {ip}\n"
            f"     ↑   : {sent_mb:.1f} MB  |  ↓ : {recv_mb:.1f} MB\n"
        )
    return output


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 9: Open Application
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def open_application(app_name: str) -> str:
    """
    Windows application open කරයි.
    Use when user says: 'open notepad', 'launch chrome', 'start calculator'.
    Examples: 'notepad', 'calc', 'chrome', 'explorer', 'mspaint', 'winword'
    """
    try:
        shortcuts = {
            'notepad'    : 'notepad.exe',
            'calculator' : 'calc.exe',
            'calc'       : 'calc.exe',
            'paint'      : 'mspaint.exe',
            'explorer'   : 'explorer.exe',
            'task manager': 'taskmgr.exe',
            'cmd'        : 'cmd.exe',
            'powershell' : 'powershell.exe',
            'chrome'     : 'chrome.exe',
            'edge'       : 'msedge.exe',
            'firefox'    : 'firefox.exe',
            'word'       : 'winword.exe',
            'excel'      : 'excel.exe',
            'powerpoint' : 'powerpnt.exe',
        }
        exe = shortcuts.get(app_name.lower(), app_name)
        subprocess.Popen(exe, shell=True)
        return f"✅ '{app_name}' open කරන ලදී."
    except Exception as e:
        return f"❌ '{app_name}' open කිරීමේ දෝෂයක්: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 10: Power Action (Shutdown/Restart/Sleep)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def system_power_action(action: str, delay_seconds: int = 30) -> str:
    """
    System shutdown / restart / sleep / cancel කරයි.
    action options: 'shutdown', 'restart', 'sleep', 'cancel'
    delay_seconds: seconds to wait before action (default 30)
    """
    cmds = {
        'shutdown': f'shutdown /s /t {delay_seconds}',
        'restart' : f'shutdown /r /t {delay_seconds}',
        'sleep'   : 'rundll32.exe powrprof.dll,SetSuspendState 0,1,0',
        'cancel'  : 'shutdown /a',
    }
    act = action.lower().strip()
    if act not in cmds:
        return f"❌ Invalid action. Use: {', '.join(cmds.keys())}"
    try:
        subprocess.run(cmds[act], shell=True, check=True)
        msgs = {
            'shutdown': f"🔴 PC shutdown {delay_seconds}s ලෙ scheduled.",
            'restart' : f"🔄 PC restart {delay_seconds}s ලෙ scheduled.",
            'sleep'   : "💤 PC sleep mode ලෙ.",
            'cancel'  : "✅ Shutdown/Restart cancel කරන ලදී.",
        }
        return msgs[act]
    except Exception as e:
        return f"❌ Power action error: {e}"


if __name__ == "__main__":
    mcp.run(transport='stdio')