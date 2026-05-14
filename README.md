# 🖥️ Cyber Process Monitor

A terminal-based Windows process monitor built in Python — inspired by Windows Task Manager but with a cyberpunk aesthetic, accurate CPU sampling, and automatic threat logging.

```
  ██████╗██╗   ██╗██████╗ ███████╗██████╗
 ██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗
 ██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝
 ██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗
 ╚██████╗   ██║   ██████╔╝███████╗██║  ██║
  ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝
  P R O C E S S   M O N I T O R   v2.0
```

---

## Features

- **Animated boot sequence** — system initialisation animation on startup
- **Real-time process table** — PID, name, CPU%, memory (MB), status, reason
- **Accurate CPU measurement** — two-pass sampling matches Windows Task Manager values
- **Color-coded status** — ✓ OK (green), △ WARN (yellow), ⚠ ALERT (red)
- **System health bars** — live CPU load and RAM usage bars at the top
- **Auto-sorted** — ALERT processes first, then WARN, then OK, all by CPU descending
- **CSV threat logging** — WARN and ALERT processes logged automatically to `logs/process_log.csv`
- **Runs as standalone .exe** — no Python needed on target machine

---

## Requirements

- Python 3.8+
- Windows (tested on Windows 10/11)
- Terminal with ANSI color support (Windows Terminal recommended)

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/PASAN121/cyber-process-monitor.git
cd cyber-process-monitor

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python src/monitor.py
```

---

## Build standalone .exe

```bash
pip install pyinstaller
python -m PyInstaller --onefile --console --hidden-import=psutil src/monitor.py
```

The executable will be at `dist/monitor.exe`.

---

## Project Structure

```
cyber-process-monitor/
├── src/
│   └── monitor.py          # main application
├── logs/                   # auto-created at runtime (gitignored)
│   └── process_log.csv     # WARN/ALERT threat log
├── requirements.txt        # Python dependencies
├── README.md               # this file
└── .gitignore
```

---

## Status Thresholds

| Status | CPU % | Memory % |
|--------|-------|----------|
| ✓ OK   | ≤ 5%  | ≤ 5%     |
| △ WARN | 5–15% | 5–15%    |
| ⚠ ALERT | > 15% | > 15%  |

---

## Controls

| Key | Action |
|-----|--------|
| `Ctrl+C` | Exit (writes final log entry before closing) |

---

## Log Format

WARN and ALERT processes are automatically appended to `logs/process_log.csv`:

```
timestamp,pid,name,cpu_pct,mem_mb,status,reason
2026-05-14T13:30:00,3360,MemCompression,0.0,910.6,WARN,Memory
```

---

## How CPU is calculated

Raw `psutil` values are divided by the number of logical cores to match Windows Task Manager's 0–100% scale. A two-pass sampling approach with a 1-second window is used for accuracy, identical to Task Manager's sampling interval.

---

## Built with

- [`psutil`](https://github.com/giampaolo/psutil) — cross-platform system monitoring
- Python standard library (`csv`, `os`, `sys`, `re`, `time`, `datetime`)
