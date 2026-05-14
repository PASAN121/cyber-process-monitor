import psutil #to monitor the precessor and memory status of the computer
import time #to get the current time and dat    e
import os #to get the current working directory and to create a log file if it doesn't exist
import csv #to write the log file in csv format
from datetime import datetime #to get the current date and time for logging purposes

TotalMemory=psutil.virtual_memory().total
NumCores=psutil.cpu_count(logical=True) #get the number of cores 

#logging data

LogDir = "logs"
LogFile = os.path.join(LogDir, "process_log.csv")

#ANSI color codes for terminal output
R  = "\033[0m"
G  = "\033[92m"
Y  = "\033[93m"
RD = "\033[91m"
CY = "\033[96m"
BD = "\033[1m"

def color_status(s):
    if s== "ALERT": return f"{RD}{BD}{s:<10}{R}"
    if s == "WARN":  return f"{Y}{s:<10}{R}"
    return f"{G}{s:<10}{R}"

def color_cpu(val):
    if val > 15: return f"{RD}{val:<10}{R}"
    if val > 5:  return f"{Y}{val:<10}{R}"
    return f"{G}{val:<10}{R}"

def color_mem(val):
    if val > 15: return f"{RD}{val:<15}{R}"
    if val > 5:  return f"{Y}{val:<15}{R}"
    return f"{CY}{val:<15}{R}"

def get_status(percentage):
    
    if percentage > 15:
        return "ALERT"
    elif percentage >5:
        return "WARN"
    else:
        return "OK"
    #updatd to get correct what gives the saatus of the process based on the percentage of CPU and Memory usage
def get_reason(cpu_status, mem_status):
    if cpu_status == "ALERT" and mem_status == "ALERT":
        return "CPU+Mem"
    elif cpu_status == "ALERT":
        return "CPU"
    elif mem_status == "ALERT":
        return "Memory"
    elif cpu_status == "WARN" and mem_status == "WARN":
        return "CPU+Mem"
    elif cpu_status == "WARN":
        return "CPU"
    elif mem_status == "WARN":
        return "Memory"
    else:
        return "-"


#Get process data  
def get_processes():
    """Get running processes and store them as a list of dictionaries"""
    
    procs = []
    process=list(psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]))
    time.sleep(0.5)#allow cpu_percent to calculate over a short interval
    for p in process:

        try:
            cpu_raw = p.cpu_percent()
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
           
            cpu_p =cpu_raw/NumCores 
             #CPU status
            cpu_status=get_status(cpu_p)

            name=info["name"] or "unknown"
            
            #overall status is the worst of CPU and Memory
            overall_status = "ALERT"if (cpu_status == "ALERT" or mem_status == "ALERT") else ("WARN" if (cpu_status == "WARN" or mem_status == "WARN") else "OK")

            reason = get_reason(cpu_status, mem_status)

            procs.append({
                "pid": pid,
                "name": name,
                "cpu": round(cpu_p, 2),
                "mem": round(mem_mb,2),
                "status": overall_status,
                "reason":  reason
            })

            

        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass  # skip protected or vanished processes

    return procs


def run_dashboard():
    processes = get_processes() #get the process data
    write_logs(processes) #write the log data to the log file
    status_orders = {"ALERT": 0, "WARN": 1, "OK": 2} #define status order for sorting
    #sort the processes by status and CPU usage
    processes=sorted(processes, key=lambda x: (status_orders[x["status"]], -x["cpu"])) 
   
    #clear the console for a fresh dashboard displa 
    os.system('cls' if os.name == 'nt' else 'clear')

    #header
    print(f"{BD}{'PID':<10}{'Name':<55}{'CPU%':<10}{'Mem(MB)':<15}{'Status':<10}")
    print("-" * 110)
    #display the process data
    for proc in processes:
        print(
            f"{proc['pid']:<10}"
            f"{proc['name']:<55}"
            f"{color_cpu(proc['cpu'])}"
            f"{color_mem(proc['mem'])}"
            f"{color_status(proc['status'])}"
        )
    
    print("\nPress Ctrl+C to exit.")
    time.sleep(2)  # Refresh every 2 seconds

def setup_logs():
    os.makedirs(LogDir, exist_ok=True)
    if not os.path.exists(LogFile):
        with open(LogFile, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "pid", "name", "cpu", "mem", "status", "reason"])

def write_logs(processes):
    timestamp = datetime.now().isoformat()
    with open(LogFile, 'a', newline='') as f:
        writer = csv.writer(f)
        for proc in processes:
            if proc['status'] in ["ALERT", "WARN"]:
             writer.writerow([timestamp, proc['pid'], proc['name'], proc['cpu'], proc['mem'], proc['status'], proc['reason']])


if __name__ == "__main__":
    setup_logs() #setup the log file
    while True:
        try:
            run_dashboard()
        except KeyboardInterrupt:
            print("\nExiting dashboard.")
            write_logs(get_processes())  # Write logs before exiting
            break
            