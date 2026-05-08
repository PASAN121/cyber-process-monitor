import psutil #to monitor the precessor and memory status of the computer

TotalMemory=psutil.virtual_memory().total
NumCores=psutil.cpu_count() #get the number of cores 



#Get process data  
def get_processes():
    """Get running processes and store them as a list of dictionaries"""
    
    procs = []

    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
        try:
            info = p.info

             # Memory in MB
            mem_bytes = info["memory_info"].rss if info["memory_info"] else 0
            mem_mb = mem_bytes / (1024 * 1024)


            #memory status

            mem_status=get_status(mem_bytes/TotalMemory)


            # Normalize CPU: Divide by number of cores so max is 100%
            cpu = (info["cpu_percent"] or 0.0)/NumCores

            #CPU status

            cpu_status=

            

            name=info["name"] or "unknown"


            procs.append({
                "pid": info["pid"],
                "name": name,
                "cpu": cpu,
                "mem": mem_mb,
            })

            

        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass  # skip protected or vanished processes

    return procs


def get_status(current_val,total_val):
    percentage=(current_val/total_val) * 100

    if percentage > 75:
        return "ALERT"
    elif percentage >50:
        return "WARN"
    else:
        return "OK"

