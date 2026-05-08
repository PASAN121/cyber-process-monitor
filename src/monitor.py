import psutil #to monitor the precessor and memory status of the computer
import time #to get the current time and dat    e
import os #to get the current working directory and to create a log file if it doesn't exist

TotalMemory=psutil.virtual_memory().total
NumCores=psutil.cpu_count(logical=True) #get the number of cores 

def get_status(percentage):
    
    if percentage > 75:
        return "ALERT"
    elif percentage >50:
        return "WARN"
    else:
        return "OK"


#Get process data  
def get_processes():
    """Get running processes and store them as a list of dictionaries"""
    
    procs = []

    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
        try:
            info = p.info
            pid = info["pid"]


            # Skip System Idle Process (PID 0) to avoid 1000% CPU alerts

            if pid == 0:
                continue


            #memrory calculation


             # Memory in MB
            mem_bytes = info["memory_info"].rss if info["memory_info"] else 0
            mem_mb = mem_bytes / (1024 * 1024)

             #memory percentage
            mem_p=(mem_bytes/TotalMemory)*100
             #memory status
            mem_status=get_status(mem_p)

            #CPU calculation     
             # Normalize CPU: Divide by number of cores so max is 100%
            cpu_raw = info["cpu_percent(interval=None)"] or 0.0
            cpu_p =cpu_raw/NumCores
             #CPU status
            cpu_status=get_status(cpu_p)

            name=info["name"] or "unknown"
            
            #overall status is the worst of CPU and Memory
            overall_status = "ALERT"if (cpu_status == "ALERT" or mem_status == "ALERT") else ("WARN" if (cpu_status == "WARN" or mem_status == "WARN") else "OK")


    

            procs.append({
                "pid": pid,
                "name": name,
                "cpu": round(cpu_p, 2),
                "mem": round(mem_mb,2),
                "status": overall_status
            })

            

        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass  # skip protected or vanished processes

    return procs


def run_dashboard():
    processes = get_processes() #get the process data
    #sort the processes by status and CPU usage
    processes=sorted(processes, key=lambda x: (x["status"], x["cpu"]), reverse=True) 
   
    #clear the console for a fresh dashboard displa 
    os.system('cls' if os.name == 'nt' else 'clear')

    #header
    print(f"{'PID':<10}{'Name':<55}{'CPU%':<10}{'Mem(MB)':<15}{'Status':<10}")
    print("-" * 100)

    #display the process data
    for proc in processes:
        print(f"{proc['pid']:<10}{proc['name']:<55}{proc['cpu']:<10}{proc['mem']:<15}{proc['status']:<10}")
    
    print("\nPress Ctrl+C to exit.")
    datetime.datetime.sleep(5)  # Refresh every 5 seconds
if __name__ == "__main__":
    run_dashboard()