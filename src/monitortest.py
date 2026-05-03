"""
╔══════════════════════════════════════════════════════════════╗
║           CYBER PROCESS MONITOR — monitor.py                 ║
║           Steps 1-9 | psutil + SQLite + Logging              ║
╚══════════════════════════════════════════════════════════════╝

Requirements:
    pip install psutil

Run:
    python monitor.py
    python monitor.py --filter      # show CPU > 5% only
    python monitor.py --top5        # show top 5 CPU hogs
    python monitor.py --log-only    # just log, no live display
"""

import psutil
import sqlite3
import csv
import os
import sys
import time
import signal
import argparse
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# STEP 9: CONFIG & BANNER
# ─────────────────────────────────────────────────────────────

VERSION      = "1.0.0"
REFRESH_SEC  = 2          # how often to refresh
LOG_DIR      = "logs"
LOG_FILE     = os.path.join(LOG_DIR, "process_log.csv")
DB_FILE      = os.path.join(LOG_DIR, "process_monitor.db")
CPU_ALERT    = 15.0       # % threshold for HIGH CPU alert
MEM_ALERT    = 300.0      # MB threshold for HIGH MEM alert
TOP_N        = 5          # how many processes to show in top mode

# ANSI colour codes
R  = "\033[0m"            # reset
G  = "\033[92m"           # green
Y  = "\033[93m"           # yellow
RD = "\033[91m"           # red
CY = "\033[96m"           # cyan
BL = "\033[94m"           # blue
DM = "\033[2m"            # dim
BD = "\033[1m"            # bold

def banner():
    print(f"""
{CY}{BD}╔══════════════════════════════════════════════════════════════╗
║        ░█▀▀░█░█░█▀▄░█▀▀░█▀▄  ░█▄█░█▀█░█▀█░▀█▀░▀█▀░█▀█░█▀▄ ║
║        ░█░░░░█░░█▀▄░█▀▀░█▀▄  ░█░█░█░█░█░█░░█░░░█░░█░█░█▀▄ ║
║        ░▀▀▀░░▀░░▀▀░░▀▀▀░▀░▀  ░▀░▀░▀▀▀░▀░▀░▀▀▀░░▀░░▀▀▀░▀░▀ ║
║                   PROCESS MONITOR v{VERSION}                     ║
╚══════════════════════════════════════════════════════════════╝{R}
{DM}  [psutil] [SQLite] [CSV Logging] [Alert Engine] [Analysis]{R}
""")

# ─────────────────────────────────────────────────────────────
# STEP 6: LOGGING SETUP
# ─────────────────────────────────────────────────────────────

def setup_logs():
    """Create logs/ folder and CSV file with headers if needed."""
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "pid", "name", "cpu_pct", "mem_mb", "status"])
    print(f"{G}[LOG]{R}  Log file  : {LOG_FILE}")

def write_log(rows):
    """Append a list of process dicts to the CSV log."""
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        for r in rows:
            writer.writerow([
                r["ts"], r["pid"], r["name"],
                f"{r['cpu']:.1f}", f"{r['mem']:.1f}", r["status"]
            ])

# ─────────────────────────────────────────────────────────────
# STEP 7: SQLITE DATABASE
# ─────────────────────────────────────────────────────────────

def setup_db():
    """Create SQLite DB and processes table."""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS processes (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT    NOT NULL,
            pid       INTEGER NOT NULL,
            name      TEXT    NOT NULL,
            cpu_pct   REAL    NOT NULL,
            mem_mb    REAL    NOT NULL,
            status    TEXT    NOT NULL
        )
    """)
    conn.commit()
    print(f"{G}[DB]{R}   Database  : {DB_FILE}")
    return conn

def insert_db(conn, rows):
    """Insert process rows into SQLite."""
    conn.executemany(
        "INSERT INTO processes (timestamp,pid,name,cpu_pct,mem_mb,status) VALUES (?,?,?,?,?,?)",
        [(r["ts"], r["pid"], r["name"], r["cpu"], r["mem"], r["status"]) for r in rows]
    )
    conn.commit()

def query_db(conn, limit=10):
    """Retrieve recent records from the DB."""
    cur = conn.execute(
        "SELECT timestamp,pid,name,cpu_pct,mem_mb,status FROM processes ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    return cur.fetchall()

# ─────────────────────────────────────────────────────────────
# STEP 3: COLLECT PROCESS DATA
# ─────────────────────────────────────────────────────────────

def get_processes():
    """
    Return list of dicts with pid, name, cpu%, mem MB.
    Handles AccessDenied and NoSuchProcess gracefully (Step 3).
    """
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
        try:
            info = p.info
            mem_mb = (info["memory_info"].rss / 1024 / 1024) if info["memory_info"] else 0.0
            cpu    = info["cpu_percent"] or 0.0
            name   = info["name"] or "unknown"
            procs.append({
                "pid":  info["pid"],
                "name": name,
                "cpu":  cpu,
                "mem":  mem_mb,
            })
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass   # silently skip inaccessible processes
    return procs

# ─────────────────────────────────────────────────────────────
# STEP 8: ALERT ENGINE
# ─────────────────────────────────────────────────────────────

def get_status(cpu, mem):
    """Return status label based on thresholds."""
    if cpu > CPU_ALERT or mem > MEM_ALERT:
        return "ALERT"
    if cpu > 5.0 or mem > 100.0:
        return "WARN"
    return "OK"

def check_alerts(procs):
    """Print alert messages for high-CPU / high-MEM processes."""
    flagged = [p for p in procs if p["status"] == "ALERT"]
    for p in flagged:
        reasons = []
        if p["cpu"] > CPU_ALERT:
            reasons.append(f"CPU {p['cpu']:.1f}% > {CPU_ALERT}%")
        if p["mem"] > MEM_ALERT:
            reasons.append(f"MEM {p['mem']:.1f}MB > {MEM_ALERT}MB")
        print(f"  {RD}[ALERT]{R} {BD}{p['name']}{R} (PID {p['pid']}) — {', '.join(reasons)}")
    return flagged

# ─────────────────────────────────────────────────────────────
# STEP 3+9: OUTPUT FORMATTING
# ─────────────────────────────────────────────────────────────

COL_WIDTHS = {"pid": 7, "name": 26, "cpu": 9, "mem": 12, "status": 8}

def colour_cpu(val):
    if val > CPU_ALERT: return f"{RD}{val:>7.1f}%{R}"
    if val > 5.0:       return f"{Y}{val:>7.1f}%{R}"
    return f"{G}{val:>7.1f}%{R}"

def colour_mem(val):
    if val > MEM_ALERT: return f"{RD}{val:>9.1f}MB{R}"
    if val > 100.0:     return f"{Y}{val:>9.1f}MB{R}"
    return f"{CY}{val:>9.1f}MB{R}"

def colour_status(s):
    if s == "ALERT": return f"{RD}{BD}{s:<7}{R}"
    if s == "WARN":  return f"{Y}{s:<7}{R}"
    return f"{G}{s:<7}{R}"

def print_header():
    print(f"\n{BD}{CY}{'PID':>7}  {'PROCESS NAME':<26}  {'CPU %':>8}  {'MEMORY':>11}  STATUS{R}")
    print(f"{DM}{'─'*7}  {'─'*26}  {'─'*8}  {'─'*11}  {'─'*7}{R}")

def print_row(p):
    pid    = f"{p['pid']:>7}"
    name   = f"{p['name'][:26]:<26}"
    cpu    = colour_cpu(p["cpu"])
    mem    = colour_mem(p["mem"])
    status = colour_status(p["status"])
    print(f"{BL}{pid}{R}  {name}  {cpu}  {mem}  {status}")

def print_footer(procs, tick, elapsed):
    total_cpu = sum(p["cpu"] for p in procs)
    total_mem = sum(p["mem"] for p in procs)
    alerts    = sum(1 for p in procs if p["status"] == "ALERT")
    h = int(elapsed // 3600)
    m = int((elapsed % 3600) // 60)
    s = int(elapsed % 60)
    print(f"\n{DM}{'─'*64}{R}")
    print(
        f"  {DM}Processes: {CY}{len(procs)}{R}  "
        f"Total CPU: {colour_cpu(total_cpu)}  "
        f"Total MEM: {colour_mem(total_mem)}  "
        f"Alerts: {RD if alerts else G}{alerts}{R}  "
        f"Tick: {DM}#{tick}{R}  "
        f"Uptime: {DM}{h:02d}:{m:02d}:{s:02d}{R}"
    )
    print(f"  {DM}Log: {LOG_FILE}  DB: {DB_FILE}{R}")

# ─────────────────────────────────────────────────────────────
# STEP 8: SIMPLE ANALYSIS
# ─────────────────────────────────────────────────────────────

def print_analysis(procs):
    if not procs:
        return
    by_cpu = sorted(procs, key=lambda p: p["cpu"], reverse=True)
    top    = by_cpu[0]
    avg_cpu = sum(p["cpu"] for p in procs) / len(procs)
    avg_mem = sum(p["mem"] for p in procs) / len(procs)
    print(f"\n{BD}{CY}  ── ANALYSIS ──────────────────────────────────{R}")
    print(f"  Top CPU hog : {BD}{top['name']}{R} (PID {top['pid']}) at {colour_cpu(top['cpu'])}")
    print(f"  Avg CPU/proc: {colour_cpu(avg_cpu)}")
    print(f"  Avg MEM/proc: {colour_mem(avg_mem)}")
    alerts = [p for p in procs if p["status"] == "ALERT"]
    if alerts:
        print(f"\n{RD}  ── ALERTS ────────────────────────────────────{R}")
        check_alerts(procs)
    else:
        print(f"\n{G}  ── ALERTS ──── All clear, no anomalies ───────{R}")

# ─────────────────────────────────────────────────────────────
# STEP 4: FILTERING
# ─────────────────────────────────────────────────────────────

def apply_filter(procs, mode):
    """Filter/sort processes based on CLI mode."""
    sorted_procs = sorted(procs, key=lambda p: p["cpu"], reverse=True)
    if mode == "filter":
        return [p for p in sorted_procs if p["cpu"] > 5.0]
    if mode == "top5":
        return sorted_procs[:TOP_N]
    return sorted_procs   # default: all, sorted by CPU

# ─────────────────────────────────────────────────────────────
# STEP 5: MAIN MONITORING LOOP
# ─────────────────────────────────────────────────────────────

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def run(args, conn):
    tick      = 0
    start     = time.time()
    mode      = "filter" if args.filter else ("top5" if args.top5 else "all")

    print(f"{G}[MONITOR]{R} Starting... press {BD}Ctrl+C{R} to stop.\n")
    time.sleep(0.5)

    # First call to cpu_percent seeds the baseline (returns 0.0)
    psutil.cpu_percent(interval=None)
    for p in psutil.process_iter(["cpu_percent"]):
        try: p.cpu_percent(interval=None)
        except: pass

    while True:
        time.sleep(REFRESH_SEC)
        tick += 1
        elapsed = time.time() - start
        now     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Collect
        raw   = get_processes()
        for p in raw:
            p["status"] = get_status(p["cpu"], p["mem"])
            p["ts"]     = now

        # Filter/sort for display
        display = apply_filter(raw, mode)

        # Persist top 10 by CPU to log + DB each tick
        top10 = sorted(raw, key=lambda p: p["cpu"], reverse=True)[:10]
        write_log(top10)
        insert_db(conn, top10)

        if not args.log_only:
            clear_screen()
            banner()
            mode_label = {"filter": "CPU > 5%", "top5": f"Top {TOP_N}", "all": "All Processes"}[mode]
            ts_line = f"{DM}  {now}  |  Mode: {CY}{mode_label}{R}"
            print(ts_line)
            print_header()
            for p in display:
                print_row(p)
            print_footer(raw, tick, elapsed)
            print_analysis(raw)
        else:
            print(f"{DM}[{now}]{R} Tick #{tick} — logged {len(top10)} processes.", flush=True)

# ─────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Cyber Process Monitor — real-time system process tracker"
    )
    parser.add_argument("--filter",   action="store_true", help="Show only processes with CPU > 5%%")
    parser.add_argument("--top5",     action="store_true", help="Show only top 5 CPU processes")
    parser.add_argument("--log-only", action="store_true", help="Log without live display")
    return parser.parse_args()

def graceful_exit(sig, frame):
    print(f"\n\n{Y}[EXIT]{R} Monitor stopped. Logs saved to {BD}{LOG_DIR}/{R}\n")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, graceful_exit)
    args = parse_args()
    banner()
    setup_logs()
    conn = setup_db()
    print()
    run(args, conn)