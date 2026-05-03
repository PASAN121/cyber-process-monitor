"""
╔══════════════════════════════════════════╗
║        CYBER PROCESS MONITOR            ║
║   Terminal-based Task Manager in Python ║
╚══════════════════════════════════════════╝

Author  : Senior Python Systems Engineer
Library : psutil (process & system utilities)
Run with: python cyber_process_monitor.py
Stop with: Ctrl+C
"""

import psutil   # The core library for reading OS-level process data
import time     # Used to pause between refresh cycles
import os       # Used to clear the terminal screen on each refresh


# ─────────────────────────────────────────────
# STEP 1: Define column layout constants
# ─────────────────────────────────────────────
# Fixed widths keep columns aligned even when process names vary in length.
# Think of these as the "ruler" for your table layout.

COL_PID  = 8    # Width for the PID column
COL_NAME = 30   # Width for the process name column
COL_CPU  = 10   # Width for CPU% column
COL_MEM  = 12   # Width for memory column

REFRESH_INTERVAL = 2  # Seconds between each screen refresh


# ─────────────────────────────────────────────
# STEP 2: Build and print the table header
# ─────────────────────────────────────────────
# The header is printed once at the top of each refresh cycle.
# ljust() left-aligns text within a fixed-width field — this is what
# makes PID, NAME, CPU%, MEM(MB) all line up consistently.

def print_header():
    separator = "─" * (COL_PID + COL_NAME + COL_CPU + COL_MEM + 6)

    print(separator)
    print(
        "PID".ljust(COL_PID) +
        "NAME".ljust(COL_NAME) +
        "CPU%".ljust(COL_CPU) +
        "MEM(MB)".ljust(COL_MEM)
    )
    print(separator)


# ─────────────────────────────────────────────
# STEP 3: Collect data from all running processes
# ─────────────────────────────────────────────
# psutil.process_iter() walks every process the OS is currently running.
# We pass the attributes we need upfront — this is faster than fetching
# them one by one (fewer OS-level system calls).
#
# Why wrap in try/except?
#   - NoSuchProcess : a process can die BETWEEN the time we listed it
#                     and the time we try to read it. This is very common.
#   - AccessDenied  : some system/kernel processes block user-space reads.
#   - We simply skip both — no crash, no noise.

def collect_processes():
    processes = []

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            pid  = proc.info['pid']
            name = proc.info['name'] or "Unknown"

            # cpu_percent(interval=0.1) blocks for 100ms per process to
            # measure actual CPU activity over a short sample window.
            # Without an interval, it returns 0.0 on the first call.
            cpu  = proc.cpu_percent(interval=0.1)

            # memory_info().rss = Resident Set Size — the actual RAM
            # the process is using right now (not swapped out).
            # Dividing by 1024² converts bytes → megabytes.
            mem  = proc.memory_info().rss / (1024 * 1024)

            processes.append({
                'pid' : pid,
                'name': name,
                'cpu' : cpu,
                'mem' : mem
            })

        except psutil.NoSuchProcess:
            # Process exited between iteration and data fetch — skip silently
            continue

        except psutil.AccessDenied:
            # OS blocked our read (e.g., kernel threads) — skip silently
            continue

        except Exception:
            # Catch-all safety net for any unexpected OS-level errors
            continue

    return processes


# ─────────────────────────────────────────────
# STEP 4: Sort and display processes as a table
# ─────────────────────────────────────────────
# Sorting by CPU% (descending) puts the most active processes at the top —
# just like Windows Task Manager's default "CPU" sort.
#
# round(value, 2) keeps numbers clean: 0.12345... → 0.12
# str(value).ljust(width) pads the number string to fixed column width.

def display_processes(processes):
    # Sort by CPU usage, highest first
    sorted_procs = sorted(processes, key=lambda p: p['cpu'], reverse=True)

    print_header()

    for p in sorted_procs:
        pid_str  = str(p['pid']).ljust(COL_PID)
        name_str = p['name'][:COL_NAME - 1].ljust(COL_NAME)  # Truncate long names
        cpu_str  = str(round(p['cpu'], 2)).ljust(COL_CPU)
        mem_str  = str(round(p['mem'], 2)).ljust(COL_MEM)

        print(pid_str + name_str + cpu_str + mem_str)

    print()
    total = psutil.virtual_memory()
    used_gb  = round(total.used  / (1024 ** 3), 2)
    total_gb = round(total.total / (1024 ** 3), 2)
    cpu_total = psutil.cpu_percent(interval=None)

    print(f"  System CPU : {cpu_total}%   |   RAM Used: {used_gb} GB / {total_gb} GB")
    print(f"  Processes  : {len(processes)} running")
    print(f"  Refreshing every {REFRESH_INTERVAL}s  |  Press Ctrl+C to stop")


# ─────────────────────────────────────────────
# STEP 5: Main loop — the "heartbeat" of the monitor
# ─────────────────────────────────────────────
# os.system('clear') wipes the terminal before each redraw so it feels
# like a live dashboard, not a scrolling log.
#
# KeyboardInterrupt is raised when you press Ctrl+C — we catch it cleanly
# so the program exits with a friendly message instead of a traceback.

def main():
    print("\n  Starting Cyber Process Monitor...")
    time.sleep(0.5)  # Brief pause before first render

    try:
        while True:
            os.system('clear')  # Use 'cls' on Windows if needed

            print("""
  ██████╗██╗   ██╗██████╗ ███████╗██████╗     ███╗   ███╗ ██████╗ ███╗   ██╗
 ██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗    ████╗ ████║██╔═══██╗████╗  ██║
 ██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝    ██╔████╔██║██║   ██║██╔██╗ ██║
 ██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗    ██║╚██╔╝██║██║   ██║██║╚██╗██║
 ╚██████╗   ██║   ██████╔╝███████╗██║  ██║    ██║ ╚═╝ ██║╚██████╔╝██║ ╚████║
  ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝    ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
            """)

            processes = collect_processes()
            display_processes(processes)

            time.sleep(REFRESH_INTERVAL)

    except KeyboardInterrupt:
        print("\n\n  Monitor stopped. Goodbye.\n")


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
# This guard ensures the monitor only runs when executed directly,
# not when imported as a module by another script.

if __name__ == "__main__":
    main()