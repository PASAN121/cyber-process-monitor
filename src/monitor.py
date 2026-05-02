import psutil

'''
[x] Import psutil in Python
[x] Get list of running processes
[x] Print process name only
[x] Print PID + process name

learn out comes
process_iter() accepts ONE argument only (a list), not multiple strings

'''

# Full process objects (heavy)
def full_process_objects():
    for process in psutil.process_iter():
        print(process)


# Only process name
def process_names_only():
    for p in psutil.process_iter(['name']):
        print(p.info['name'])


# PID + Name (your goal)
def pid_and_name():
    for p in psutil.process_iter(['pid', 'name']):
        print(p.info)


full_process_objects()
process_names_only()
pid_and_name()