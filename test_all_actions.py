
import sys
import os
import time
sys.path.append(os.getcwd())

from main import handle_command

TEST_COMMANDS = [
    # System Actions
    "Minimize windows",
    "Open Notepad",
    "Close Notepad",
    "Open Calculator", 
    "Close Calculator",
    
    # Apps (Store/Standard)
    "Open Spotify",
    "Close Spotify",
    "Open WhatsApp",
    "Terminate WhatsApp",
    "Open Edge",
    "Close Edge",
    
    # File/Folder
    "Open Workspace",
    
    # Web
    "Open Google",
    
    # Project Core (Just to ensure no regression)
    "Help",
    "Status"
]

print("=== STARTING COMPREHENSIVE ACTION TEST ===")
print("Note: This will actually open/close apps on your screen.\n")

results = {}

for cmd in TEST_COMMANDS:
    print(f"\n[TESTING] Command: '{cmd}'")
    try:
        response = handle_command(cmd)
        print(f"[RESULT] {response}")
        results[cmd] = response
        
        # Give it a moment to open/close
        time.sleep(2)
        
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        results[cmd] = f"ERROR: {e}"

print("\n=== TEST SUMMARY ===")
for cmd, res in results.items():
    status = "???"
    if "Opening" in res or "Opened" in res or "Terminated" in res or "Minimized" in res or "health" in res or "help" in res:
        status = "PASS"
    elif "Error" in res or "Could not" in res or "did not understand" in res:
        status = "FAIL"
    else:
        status = "INFO"
        
    print(f"{status:5} | '{cmd}' -> {res}")
