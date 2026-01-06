#!/usr/bin/env python3
import os
import sys
import time
import socket
import signal
import subprocess
from pathlib import Path

# Project root = parent of backend/ (AutocadPDFconvert)
ROOT_DIR = Path(__file__).resolve().parent.parent

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# If dwg_plot_api.py is inside backend/, use this:
APP = os.getenv("APP", "backend.main:app")  # FastAPI app

# If dwg_plot_api.py is at ROOT_DIR instead, change to:
# APP = os.getenv("APP", "dwg_plot_api:app")

WORKERS = int(os.getenv("WORKERS", "1"))
EXTRA = os.getenv("UVICORN_EXTRA", "")
CHECK_HOSTS = [os.getenv("CHECK_HOST", "127.0.0.1"), "localhost"]

# Run uvicorn from project root
CWD = ROOT_DIR
PIDFILE = ROOT_DIR / "uvicorn_backend_main.pid"
LOGFILE = ROOT_DIR / "uvicorn_backend_main.log"


def is_listening(hosts=CHECK_HOSTS, port=PORT, timeout=0.25) -> bool:
    """Check if something is already listening on HOST:PORT."""
    for h in hosts:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                if s.connect_ex((h, port)) == 0:
                    return True
        except Exception:
            continue
    return False


def read_pid():
    try:
        return int(PIDFILE.read_text().strip())
    except Exception:
        return None


def is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def _build_cmd():
    """Build the uvicorn command (uvicorn backend.dwg_plot_api:app ...)."""

    # Prefer venv if it exists (Windows or Linux)
    venv_win = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
    venv_unix = ROOT_DIR / ".venv" / "bin" / "python3"

    if venv_win.exists():
        python_bin = str(venv_win)
    elif venv_unix.exists():
        python_bin = str(venv_unix)
    else:
        python_bin = sys.executable

    cmd = [
        python_bin,
        "-m",
        "uvicorn",
        APP,
        "--host",
        HOST,
        "--port",
        str(PORT),
        "--workers",
        str(WORKERS),
        "--proxy-headers",
        "--forwarded-allow-ips",
        "*",
        "--log-level",
        "info",
    ]
    if EXTRA.strip():
        cmd.extend(EXTRA.split())
    return cmd


def start():
    """Start uvicorn if not already running."""
    if is_listening():
        print(f"[launcher] FastAPI already listening on {HOST}:{PORT}")
        return 0

    pid = read_pid()
    if pid and not is_alive(pid):
        PIDFILE.unlink(missing_ok=True)

    LOGFILE.parent.mkdir(parents=True, exist_ok=True)
    log_f = open(LOGFILE, "ab", buffering=0)

    cmd = _build_cmd()
    print(f"[launcher] Starting: {' '.join(cmd)}")

    env = os.environ.copy()
    # ensure ROOT_DIR is on PYTHONPATH so 'backend' is importable
    env["PYTHONPATH"] = str(ROOT_DIR) + (
        os.pathsep + env["PYTHONPATH"] if "PYTHONPATH" in env else ""
    )

    proc = subprocess.Popen(
        cmd,
        cwd=str(CWD),  # run uvicorn from project root
        env=env,
        stdout=log_f,
        stderr=subprocess.STDOUT,
        start_new_session=True,  # detach
    )
    PIDFILE.write_text(str(proc.pid))

    # Wait for uvicorn to open the port
    for _ in range(80):
        if is_listening():
            print(f"[launcher] Started (pid {proc.pid}) on {HOST}:{PORT}")
            return 0
        time.sleep(0.1)

    # If not ready, show last part of log to debug
    try:
        tail = LOGFILE.read_bytes()[-2000:].decode("utf-8", "ignore")
    except Exception:
        tail = "<no log>"
    print("WARN: server did not become ready.\n--- LOG TAIL ---\n" + tail)
    return 1


def stop(timeout=5):
    """Stop uvicorn if running."""
    pid = read_pid()
    if not pid:
        print("[launcher] Stopped (no pidfile).")
        return 0

    if not is_alive(pid):
        PIDFILE.unlink(missing_ok=True)
        print("[launcher] Stopped (stale pidfile).")
        return 0

    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        PIDFILE.unlink(missing_ok=True)
        print("[launcher] Stopped.")
        return 0

    t0 = time.time()
    while time.time() - t0 < timeout:
        if not is_alive(pid):
            PIDFILE.unlink(missing_ok=True)
            print("[launcher] Stopped.")
            return 0
        time.sleep(0.2)

    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    PIDFILE.unlink(missing_ok=True)
    print("[launcher] Force-stopped.")
    return 0


def restart():
    stop()
    return start()


def status():
    pid = read_pid()
    if pid and is_alive(pid):
        print(f"[launcher] Running (pid {pid}) on {HOST}:{PORT}")
        return 0
    print("[launcher] Not running")
    return 3


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "start"
    if cmd == "start":
        sys.exit(start())
    elif cmd == "stop":
        sys.exit(stop())
    elif cmd == "restart":
        sys.exit(restart())
    elif cmd == "status":
        sys.exit(status())
    else:
        print("Usage: python backend/launcher.py [start|stop|restart|status]")
        sys.exit(1)


if __name__ == "__main__":
    main()
