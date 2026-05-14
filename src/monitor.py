"""
monitor.py — CYBER PROCESS MONITOR
========================================
Terminal-based Windows Task Manager with a  aesthetic background.
Features a styled ASCII header, animated startup sequence, color-coded
process table, system health bars, and CSV threat logging.
"""

import psutil
import time
import os
import csv
import sys
import re
from datetime import datetime

# ─────────────────────────────────────────────
# SYSTEM CONSTANTS
# ─────────────────────────────────────────────

TOTAL_MEMORY_BYTES: int = psutil.virtual_memory().total
NUM_LOGICAL_CORES:  int = psutil.cpu_count(logical=True)

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

LOG_DIR    = "logs"
LOG_FILE   = os.path.join(LOG_DIR, "process_log.csv")
CSV_HEADER = ["timestamp", "pid", "name", "cpu_pct", "mem_mb", "status", "reason"]

# ─────────────────────────────────────────────
# COLUMN WIDTHS
# ─────────────────────────────────────────────

W_PID    = 8
W_NAME   = 38
W_CPU    = 10
W_MEM    = 14
W_STATUS = 12
W_REASON = 10

# ─────────────────────────────────────────────
# ANSI CODES  — cyberpunk palette
#   Primary:  bright cyan   (borders, labels)
#   Safe:     bright green  (OK processes)
#   Warning:  bright yellow (WARN)
#   Danger:   bright red    (ALERT)
#   Neutral:  white/dim     (data values)
# ─────────────────────────────────────────────

RESET     = "\033[0m"
BOLD      = "\033[1m"
DIM       = "\033[2m"

FG_RED    = "\033[91m"
FG_GREEN  = "\033[92m"
FG_YELLOW = "\033[93m"
FG_CYAN   = "\033[96m"
FG_WHITE  = "\033[97m"
FG_DCYAN  = "\033[36m"   # dark cyan — borders & decorators

# ─────────────────────────────────────────────
# ASCII ART HEADER
# ─────────────────────────────────────────────

HEADER_ART = f"""{FG_CYAN}{BOLD}
  ██████╗██╗   ██╗██████╗ ███████╗██████╗
 ██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗
 ██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝
 ██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗
 ╚██████╗   ██║   ██████╔╝███████╗██║  ██║
  ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝{RESET}
{FG_DCYAN}  ╔══════════════════════════════════════════════════╗
  ║  {FG_CYAN}P R O C E S S   M O N I T O R   v2.0{FG_DCYAN}          ║
  ║  {DIM}{FG_WHITE}Real-time system surveillance & threat logging{FG_DCYAN}    ║
  ╚══════════════════════════════════════════════════╝{RESET}
"""

# ─────────────────────────────────────────────
# BOX-DRAWING HELPERS
# ─────────────────────────────────────────────

def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes to get the plain visible length."""
    return re.sub(r'\033\[[0-9;]*m', '', text)

def box_top(width: int = 100) -> str:
    return f"{FG_DCYAN}╔{'═' * (width - 2)}╗{RESET}"

def box_bot(width: int = 100) -> str:
    return f"{FG_DCYAN}╚{'═' * (width - 2)}╝{RESET}"

def box_row(content: str, width: int = 100) -> str:
    """Wrap a line in ║ borders, padding with spaces to fill width."""
    plain_len = len(strip_ansi(content))
    pad = max(0, width - 2 - plain_len)
    return f"{FG_DCYAN}║{RESET}{content}{' ' * pad}{FG_DCYAN}║{RESET}"

# ─────────────────────────────────────────────
# STARTUP ANIMATION
# ─────────────────────────────────────────────

def boot_sequence() -> None:
    """Animated boot sequence — runs once at startup."""
    os.system("cls" if os.name == "nt" else "clear")
    print(HEADER_ART)

    steps = [
        ("Initialising kernel interface      ", 0.20),
        ("Enumerating process table          ", 0.18),
        ("Loading CPU sampling engine        ", 0.18),
        ("Calibrating memory scanner         ", 0.15),
        ("Opening threat log stream          ", 0.15),
        ("All systems nominal — ONLINE       ", 0.10),
    ]

    for msg, delay in steps:
        sys.stdout.write(
            f"  {FG_DCYAN}[ {FG_YELLOW}LOADING{FG_DCYAN} ]{RESET}  {FG_WHITE}{msg}{RESET}"
        )
        sys.stdout.flush()
        time.sleep(delay)
        sys.stdout.write(
            f"\r  {FG_DCYAN}[  {FG_GREEN}  OK  {FG_DCYAN}  ]{RESET}  {FG_WHITE}{msg}{RESET}\n"
        )
        sys.stdout.flush()

    time.sleep(0.3)
    print(f"\n  {FG_CYAN}Pre-warming CPU samplers — standby 1 second …{RESET}\n")

# ─────────────────────────────────────────────
# COLORING HELPERS
# ─────────────────────────────────────────────

def color_status(s: str) -> str:
    if s == "ALERT":
        return f"{FG_RED}{BOLD}{'⚠  ALERT':<{W_STATUS}}{RESET}"
    if s == "WARN":
        return f"{FG_YELLOW}{'△  WARN':<{W_STATUS}}{RESET}"
    return f"{FG_GREEN}{'✓  OK':<{W_STATUS}}{RESET}"

def color_cpu(val: float) -> str:
    s = f"{val:.2f}%"
    if val > 15:
        return f"{FG_RED}{BOLD}{s:<{W_CPU}}{RESET}"
    if val > 5:
        return f"{FG_YELLOW}{s:<{W_CPU}}{RESET}"
    return f"{FG_GREEN}{s:<{W_CPU}}{RESET}"

def color_mem(val: float) -> str:
    s = f"{val:.1f}"
    if val > 500:
        return f"{FG_RED}{s:<{W_MEM}}{RESET}"
    if val > 200:
        return f"{FG_YELLOW}{s:<{W_MEM}}{RESET}"
    return f"{FG_CYAN}{s:<{W_MEM}}{RESET}"

# ─────────────────────────────────────────────
# STATUS & REASON
# ─────────────────────────────────────────────

def get_status(pct: float) -> str:
    if pct > 15: return "ALERT"
    if pct > 5:  return "WARN"
    return "OK"

def get_reason(cpu_s: str, mem_s: str) -> str:
    cf = cpu_s in ("ALERT", "WARN")
    mf = mem_s in ("ALERT", "WARN")
    if cf and mf: return "CPU+Mem"
    if cf:        return "CPU"
    if mf:        return "Memory"
    return "-"

# ─────────────────────────────────────────────
# PROCESS SAMPLING  (two-pass for accurate CPU)
# ─────────────────────────────────────────────

def prewarm_processes() -> list:
    """Pass 1: set cpu_percent baseline on every process."""
    procs = []
    for p in psutil.process_iter(["pid", "name", "memory_info"]):
        try:
            if p.pid == 0:
                continue
            p.cpu_percent(interval=None)
            procs.append(p)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
    return procs

def measure_processes(prewarm_list: list) -> list:
    """Pass 2 (after sleep): read actual CPU delta + memory."""
    records = []
    for p in prewarm_list:
        try:
            cpu_raw   = p.cpu_percent(interval=None)
            cpu_pct   = round(cpu_raw / NUM_LOGICAL_CORES, 2)

            mem_info  = p.memory_info()
            mem_bytes = mem_info.rss if mem_info else 0
            mem_mb    = round(mem_bytes / (1024 * 1024), 2)
            mem_pct   = (mem_bytes / TOTAL_MEMORY_BYTES) * 100

            cpu_status = get_status(cpu_pct)
            mem_status = get_status(mem_pct)
            overall    = (
                "ALERT" if (cpu_status == "ALERT" or mem_status == "ALERT") else
                "WARN"  if (cpu_status == "WARN"  or mem_status == "WARN")  else
                "OK"
            )

            name = (p.info.get("name") or "unknown")[:W_NAME]

            records.append({
                "pid":    p.pid,
                "name":   name,
                "cpu":    cpu_pct,
                "mem":    mem_mb,
                "status": overall,
                "reason": get_reason(cpu_status, mem_status),
            })
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
    return records

def get_processes() -> list:
    prewarm_list = prewarm_processes()
    time.sleep(1.0)                     # 1-second window — matches Task Manager
    return measure_processes(prewarm_list)

# ─────────────────────────────────────────────
# SYSTEM SUMMARY
# ─────────────────────────────────────────────

def get_system_summary() -> dict:
    vm = psutil.virtual_memory()
    return {
        "cpu_total":    psutil.cpu_percent(interval=None),
        "ram_used_gb":  vm.used  / (1024 ** 3),
        "ram_total_gb": vm.total / (1024 ** 3),
        "ram_pct":      vm.percent,
    }

def render_bar(pct: float, width: int = 24) -> str:
    """Segmented cyber-style progress bar."""
    filled = int(width * pct / 100)
    empty  = width - filled
    if pct > 80:
        color, fill = FG_RED, "█"
    elif pct > 50:
        color, fill = FG_YELLOW, "▓"
    else:
        color, fill = FG_GREEN, "▓"

    bar     = f"{color}{fill * filled}{FG_DCYAN}{'░' * empty}{RESET}"
    pct_str = f"{pct:5.1f}%"
    pct_col = (
        f"{FG_RED}{BOLD}{pct_str}{RESET}" if pct > 80 else
        f"{FG_YELLOW}{pct_str}{RESET}"    if pct > 50 else
        f"{FG_GREEN}{pct_str}{RESET}"
    )
    return f"{FG_DCYAN}[{RESET}{bar}{FG_DCYAN}]{RESET} {pct_col}"

# ─────────────────────────────────────────────
# DASHBOARD RENDERER
# ─────────────────────────────────────────────

def run_dashboard() -> None:
    processes = get_processes()
    summary   = get_system_summary()

    STATUS_ORDER = {"ALERT": 0, "WARN": 1, "OK": 2}
    processes.sort(key=lambda x: (STATUS_ORDER[x["status"]], -x["cpu"]))

    os.system("cls" if os.name == "nt" else "clear")

    # ── ASCII header ──────────────────────────────────────────
    print(HEADER_ART)

    # ── Stats panel ───────────────────────────────────────────
    total    = len(processes)
    alerts   = sum(1 for p in processes if p["status"] == "ALERT")
    warns    = sum(1 for p in processes if p["status"] == "WARN")
    ok_count = total - alerts - warns
    now      = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

    print(box_top(100))
    print(box_row(
        f"  {FG_DCYAN}TIMESTAMP :{RESET}  {FG_WHITE}{now}{RESET}"
        f"     {FG_DCYAN}|{RESET}"
        f"   {FG_DCYAN}PROCS :{RESET} {FG_WHITE}{total}{RESET}"
        f"   {FG_RED}⚠ {alerts}{RESET}"
        f"   {FG_YELLOW}△ {warns}{RESET}"
        f"   {FG_GREEN}✓ {ok_count}{RESET}"
        f"   {FG_DCYAN}|{RESET}   {FG_DCYAN}CORES :{RESET} {FG_WHITE}{NUM_LOGICAL_CORES}{RESET}"
    ))
    print(box_row(
        f"  {FG_DCYAN}CPU LOAD  :{RESET}  {render_bar(summary['cpu_total'])}"
    ))
    print(box_row(
        f"  {FG_DCYAN}MEMORY    :{RESET}  {render_bar(summary['ram_pct'])}"
        f"   {FG_DCYAN}{summary['ram_used_gb']:.1f} / {summary['ram_total_gb']:.1f} GB{RESET}"
    ))
    print(box_bot(100))

    # ── Column headers ────────────────────────────────────────
    print()
    print(
        f"  {FG_DCYAN}{BOLD}"
        f"{'PID':<{W_PID}}"
        f"{'PROCESS NAME':<{W_NAME + 2}}"
        f"{'CPU %':<{W_CPU}}"
        f"{'MEM (MB)':<{W_MEM}}"
        f"{'STATUS':<{W_STATUS}}"
        f"REASON"
        f"{RESET}"
    )
    print(f"  {FG_DCYAN}{'─' * 96}{RESET}")

    # ── Process rows ──────────────────────────────────────────
    for proc in processes:
        is_ok = proc["status"] == "OK"
        print(
            f"  "
            f"{DIM if is_ok else ''}"
            f"{FG_DCYAN}{proc['pid']:<{W_PID}}{RESET}"
            f"{FG_WHITE}{proc['name']:<{W_NAME + 2}}{RESET}"
            f"{color_cpu(proc['cpu'])}"
            f"{color_mem(proc['mem'])}"
            f"{color_status(proc['status'])}"
            f"{FG_DCYAN}{proc['reason']:<{W_REASON}}{RESET}"
            f"{RESET}"
        )

    # ── Footer ────────────────────────────────────────────────
    print(f"  {FG_DCYAN}{'─' * 96}{RESET}")
    print(
        f"  {FG_DCYAN}[{FG_GREEN} LOG {FG_DCYAN}]{RESET} {DIM}{FG_WHITE}{LOG_FILE}{RESET}"
        f"    {FG_DCYAN}[{FG_RED} CTRL+C {FG_DCYAN}]{RESET} {DIM}{FG_WHITE}Exit{RESET}"
        f"    {FG_DCYAN}[{FG_CYAN} AUTO {FG_DCYAN}]{RESET} {DIM}{FG_WHITE}Refresh ~1s{RESET}"
    )
    print()

    write_logs(processes)

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

def setup_logs() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="") as f:
            csv.writer(f).writerow(CSV_HEADER)

def write_logs(processes: list) -> None:
    timestamp = datetime.now().isoformat()
    flagged   = [p for p in processes if p["status"] in ("ALERT", "WARN")]
    if not flagged:
        return
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        for proc in flagged:
            writer.writerow([
                timestamp, proc["pid"], proc["name"],
                proc["cpu"], proc["mem"], proc["status"], proc["reason"],
            ])

# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    setup_logs()
    psutil.cpu_percent(interval=None)   # prime system-wide counter
    boot_sequence()

    while True:
        try:
            run_dashboard()
        except KeyboardInterrupt:
            os.system("cls" if os.name == "nt" else "clear")
            print(HEADER_ART)
            print(f"  {FG_DCYAN}[{FG_RED} SHUTDOWN {FG_DCYAN}]{RESET}  {FG_WHITE}Writing final log entry …{RESET}")
            write_logs(get_processes())
            print(f"  {FG_DCYAN}[{FG_GREEN}    OK    {FG_DCYAN}]{RESET}  {FG_WHITE}Log saved → {LOG_FILE}{RESET}")
            print(f"\n  {FG_CYAN}CYBER PROCESS MONITOR — SESSION ENDED{RESET}\n")
            break