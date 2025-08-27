# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: Distribution Authorized.
# ------------------------------------------------------------------------------------
# Notes:
# - Auto start helper script for the application.
# - Use this to run the application and start the necessary services.
# - (i.e., frontend, backend, celery workers, etc.)
# ------------------------------------------------------------------------------------
# Imports
import os
import subprocess
import shlex
import platform
from pathlib import Path
from typing import Optional

# ------------------------------------------------------------------------------------
# Repo root detection

def looks_like_root(p: Path) -> bool:
    # Minimal, explicit markers to avoid false positives
    return (p / "backend").is_dir() and (p / "frontend").is_dir()

def find_repo_root(start: Path) -> Optional[Path]:
    # 1) Exact start
    if looks_like_root(start):
        return start
    # 2) Walk up
    for parent in [*start.parents]:
        if looks_like_root(parent):
            return parent
    return None

# Prefer an explicit override if provided
_env_root = os.environ.get("SYNEVYR_ROOT")
if _env_root:
    candidate = Path(_env_root).expanduser().resolve()
    ROOT_DIR = candidate if looks_like_root(candidate) else None
else:
    # Start from: CWD first (user said the first terminal is already in .../synevyr),
    # then the script's own location, in case it’s invoked from elsewhere.
    ROOT_DIR = find_repo_root(Path.cwd()) or find_repo_root(Path(__file__).resolve().parent)

if ROOT_DIR is None:
    raise SystemExit(
        "Unable to locate synevyr repo root. Start this script from the synevyr directory "
        "or set SYNEVYR_ROOT to the absolute path of the repo."
    )

# ------------------------------------------------------------------------------------
# Consts (derived from detected ROOT_DIR)
VENV_DIR = ROOT_DIR / ".synevyr_venv"
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
PYTHON_BIN = VENV_DIR / "bin" / "python"
ACTIVATE_SCRIPT = VENV_DIR / "bin" / "activate"

FRONTEND_PORT = "2000"
CELERY_APP = "celery_app.celery"

# ------------------------------------------------------------------------------------
# Functions
def mac_escape(s: str) -> str:
    # Escape for use inside AppleScript double-quoted string
    return s.replace("\\", "\\\\").replace('"', '\\"')

def open_terminal_mac(cwd: Path, command: str):
    """
    Opens a new Terminal window, cd's to `cwd`, and runs `command`.
    """
    full_cmd = f"cd {shlex.quote(str(cwd))} && {command}"
    osa = f'''
tell application "Terminal"
    activate
    do script "{mac_escape(full_cmd)}"
end tell
'''.strip()
    subprocess.run(["osascript", "-e", osa], check=True)

def start_backend():
    cmd = f"source {shlex.quote(str(ACTIVATE_SCRIPT))} && {shlex.quote(str(PYTHON_BIN))} run.py"
    open_terminal_mac(BACKEND_DIR, cmd)

def start_celery_worker():
    cmd = f"source {shlex.quote(str(ACTIVATE_SCRIPT))} && celery -A {CELERY_APP} worker --loglevel=INFO -E"
    open_terminal_mac(BACKEND_DIR, cmd)

def start_celery_beat():
    cmd = f"source {shlex.quote(str(ACTIVATE_SCRIPT))} && celery -A {CELERY_APP} beat --loglevel=INFO"
    open_terminal_mac(BACKEND_DIR, cmd)

def start_frontend():
    cmd = f"export PORT={FRONTEND_PORT} && npm run dev"
    open_terminal_mac(FRONTEND_DIR, cmd)

if __name__ == "__main__":
    if platform.system() != "Darwin":
        print("This autostart script only supports macOS.")
        exit(1)

    # Sanity checks to fail fast if paths are wrong
    missing = []
    for p in [BACKEND_DIR, FRONTEND_DIR, VENV_DIR, PYTHON_BIN, ACTIVATE_SCRIPT]:
        if not p.exists():
            missing.append(str(p))
    if missing:
        print("Missing required paths:")
        for m in missing:
            print(" -", m)
        print("Fix paths or set SYNEVYR_ROOT to the repo path.")
        exit(1)

    start_backend()
    start_frontend()
    start_celery_worker()
    start_celery_beat()
