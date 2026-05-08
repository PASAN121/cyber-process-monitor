import psutil

def get_processes():
    """Get running processes and store them as a list of dictionaries"""
    
    procs = []

    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
        try:
            info = p.info

            mem_mb = (info["memory_info"].rss / 1024 / 1024) if info["memory_info"] else 0.0
            cpu = info["cpu_percent"] or 0.0
            name = info["name"] or "unknown"

            procs.append({
                "pid": info["pid"],
                "name": name,
                "cpu": cpu,
                "mem": mem_mb,
            })

        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass  # skip protected or vanished processes

    return procs

total_ram = psutil.virtual_memory().total / (1024**3)
cpu_cores = psutil.cpu_count(logical=True)

