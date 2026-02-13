import subprocess
from typing import Tuple

def git_init() -> Tuple[bool, str]:
    p = subprocess.run(["git", "init"], capture_output=True, text=True)
    return (p.returncode == 0, p.stdout or p.stderr)

def git_commit(message: str) -> Tuple[bool, str]:
    subprocess.run(["git", "add", "."], capture_output=True, text=True)
    p = subprocess.run(["git", "commit", "-m", message], capture_output=True, text=True)
    return (p.returncode == 0, p.stdout or p.stderr)

def git_push() -> Tuple[bool, str]:
    p = subprocess.run(["git", "push"], capture_output=True, text=True)
    return (p.returncode == 0, p.stdout or p.stderr)
