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

def open_url(url: str) -> str:
    webbrowser.open(url)
    return f"Opened URL: {url}"
