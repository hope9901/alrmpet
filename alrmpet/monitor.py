"""Process and screen session monitoring."""

import subprocess
import time
from dataclasses import dataclass
from typing import Optional

import psutil


@dataclass
class ProcessResult:
    """Result of a monitored process."""
    exit_code: int
    duration: float
    command: str
    stdout_tail: str = ""
    stderr_tail: str = ""


def run_passthrough(command_args: list) -> ProcessResult:
    """Run command with direct terminal I/O passthrough (like `time`).

    stdout/stderr go directly to the terminal. We only track
    exit code and duration — no output capture.
    """
    cmd_str = " ".join(command_args)
    start = time.time()

    proc = subprocess.Popen(command_args)
    proc.wait()

    return ProcessResult(
        exit_code=proc.returncode,
        duration=time.time() - start,
        command=cmd_str,
    )


def run_shell_passthrough(command_str: str) -> ProcessResult:
    """Run a shell command string with direct terminal passthrough."""
    start = time.time()

    proc = subprocess.Popen(command_str, shell=True)
    proc.wait()

    return ProcessResult(
        exit_code=proc.returncode,
        duration=time.time() - start,
        command=command_str,
    )


def watch_pid(pid: int, poll_interval: float = 2.0) -> ProcessResult:
    """Monitor an existing process by PID until it terminates."""
    try:
        proc = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return ProcessResult(exit_code=-1, duration=0,
                             command=f"PID {pid} (not found)")

    command = " ".join(proc.cmdline()) if proc.cmdline() else f"PID {pid}"
    start = time.time()

    try:
        while proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE:
            time.sleep(poll_interval)
    except psutil.NoSuchProcess:
        pass

    duration = time.time() - start
    try:
        exit_code = proc.wait(timeout=1)
    except (psutil.NoSuchProcess, psutil.TimeoutExpired):
        exit_code = 0

    return ProcessResult(exit_code=exit_code or 0, duration=duration,
                         command=command)


def get_process_stats(pid: int) -> Optional[dict]:
    """Get CPU and memory stats for a process."""
    try:
        proc = psutil.Process(pid)
        cpu = proc.cpu_percent(interval=0.1)
        mem_mb = proc.memory_info().rss / (1024 * 1024)
        return {"cpu": f"{cpu:.1f}%", "memory": f"{mem_mb:.1f} MB"}
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def _get_screen_child_pids(session_name: str) -> list:
    """Get PIDs of processes inside a screen session."""
    try:
        result = subprocess.run(
            ["screen", "-ls"], capture_output=True, text=True, timeout=5,
        )
        screen_pid = None
        for line in result.stdout.split("\n"):
            if session_name in line:
                parts = line.strip().split(".")
                if parts:
                    screen_pid = int(parts[0])
                    break
        if screen_pid is None:
            return []
        parent = psutil.Process(screen_pid)
        return [c.pid for c in parent.children(recursive=True) if c.is_running()]
    except (subprocess.TimeoutExpired, FileNotFoundError, psutil.NoSuchProcess,
            ValueError):
        return []


def watch_screen(session_name: str, poll_interval: float = 2.0) -> ProcessResult:
    """Monitor a screen session until all child processes finish."""
    start = time.time()
    command = f"screen:{session_name}"

    # Wait for session to appear
    for _ in range(5):
        if _get_screen_child_pids(session_name):
            break
        time.sleep(poll_interval)
    else:
        return ProcessResult(
            exit_code=-1, duration=0, command=command,
            stderr_tail=f"Screen session '{session_name}' not found.",
        )

    # Monitor until no children remain
    while _get_screen_child_pids(session_name):
        time.sleep(poll_interval)

    return ProcessResult(exit_code=0, duration=time.time() - start,
                         command=command)
