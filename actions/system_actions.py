import os
import subprocess
import webbrowser

def minimize_all_windows() -> str:
    # Uses Windows shell command to minimize all
    subprocess.run(["powershell", "-Command", "(New-Object -ComObject Shell.Application).MinimizeAll()"], capture_output=True)
    return "Minimized all windows."

def open_notes() -> str:
    # Notepad is guaranteed on Windows
    subprocess.Popen(["notepad.exe"])
    return "Opened Notes (Notepad)."

def open_word() -> str:
    # Uses default Word association if installed
    subprocess.Popen(["cmd", "/c", "start", "winword"], shell=True)
    return "Opened Microsoft Word."

def open_excel() -> str:
    subprocess.Popen(["cmd", "/c", "start", "excel"], shell=True)
    return "Opened Microsoft Excel."


def open_folder(path: str) -> str:
    os.startfile(path)
    return f"Opened folder: {path}"

def open_whatsapp() -> str:
    subprocess.Popen(["cmd", "/c", "start", "whatsapp"], shell=True)
    return "Opened WhatsApp."

def open_spotify() -> str:
    subprocess.Popen(["cmd", "/c", "start", "spotify"], shell=True)
    return "Opened Spotify."

def open_url(url: str) -> str:
    webbrowser.open(url)
    return f"Opened URL: {url}"

def play_music() -> str:
    # Simulate media key press for Play/Pause
    # This might require pynput or similar, but for hackathon demo we can try a simple shell command 
    # or just open default music player.
    # A safe bet is opening Spotify or a music url if we want to avoid extra deps.
    # But user asked for "Play/pause". Without `pynput`, we can't easily simulate media keys in pure python stdlib safely.
    # Let's try to just open Spotify/Music app as a "Play" action.
    try:
        subprocess.Popen(["start", "spotify:"], shell=True) 
        return "Opening Music Player..."
    except:
        return "Could not open music player."

# App Mapping for specific protocols or executables
APP_LAUNCH_MAP = {
    # Store Apps (Reliable AppIDs from user scan)
    "whatsapp": "shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App",
    "spotify": "shell:AppsFolder\\SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify",
    
    # Standard Apps
    "calculator": "calc",
    "notepad": "notepad",
    "chrome": "chrome",
    "edge": "msedge",
    "settings": "ms-settings:",
    "store": "ms-windows-store:",
    "vscode": "code",
    "word": "winword",
    "excel": "excel"
}

# Process names for taskkill
APP_KILL_MAP = {
    "whatsapp": ["WhatsApp.exe", "WhatsAppNative.exe"],
    "spotify": ["Spotify.exe"],
    "calculator": ["CalculatorApp.exe", "calc.exe"],
    "notepad": ["notepad.exe"],
    "chrome": ["chrome.exe"],
    "edge": ["msedge.exe"],
    "word": ["WINWORD.EXE"],
    "excel": ["EXCEL.EXE"],
    "vscode": ["Code.exe"],
    "opera": ["opera.exe"]
}

def open_application(app_name: str) -> str:
    # Strip common punctuation that might come from voice input (.,!?)
    key = app_name.lower().strip(" .?!,")
    print(f"[DEBUG] Opening app: '{key}'")
    
    # Check map first
    if key in APP_LAUNCH_MAP:
        try:
            cmd = f"start {APP_LAUNCH_MAP[key]}"
            print(f"[DEBUG] Executing: {cmd}")
            subprocess.Popen(cmd, shell=True)
            return f"Opening {app_name}..."
        except Exception as e:
            return f"Error opening {app_name}: {e}"
            
    # Fallback: Try generic start. 
    # Safe way: start "" "command"
    try:
        cmd = f'start "" "{key}"'
        print(f"[DEBUG] Executing fallback: {cmd}")
        subprocess.Popen(cmd, shell=True)
        return f"Attempting to launch {app_name}..."
    except Exception as e:
        return f"Could not find application: {app_name}"

def close_application(app_name: str) -> str:
    # Strip common punctuation that might come from voice input (.,!?)
    key = app_name.lower().strip(" .?!,")
    print(f"[DEBUG] Closing app: '{key}'")
    
    targets = APP_KILL_MAP.get(key, [f"{key}.exe", key])
    
    success_count = 0
    errors = []
    
    for proc_name in targets:
        print(f"[DEBUG] Trying to kill: {proc_name}")
        try:
            result = subprocess.run(["taskkill", "/F", "/IM", proc_name], capture_output=True, text=True)
            print(f"[DEBUG] Taskkill result: {result.stdout.strip()} {result.stderr.strip()}")
            
            if result.returncode == 0:
                success_count += 1
            else:
                errors.append(result.stderr.strip())
        except Exception as e:
            errors.append(str(e))
            
    if success_count > 0:
        return f"Terminated {app_name}."
    elif any("not found" not in e for e in errors if e):
        # If we had a real error
        return f"Failed to close {app_name}. Error: {errors[0]}"
    else:
        return f"{app_name} is not running."
