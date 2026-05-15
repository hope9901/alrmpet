"""HTTP notification receiver - run on the remote machine to receive alerts.

Usage:
    alrmpet --listen 9922

This starts a simple HTTP server that receives notifications from alrmpet
running on other machines and displays them locally.
"""

import json
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

from .pet import show_completion_banner, format_duration


class _NotifyHandler(BaseHTTPRequestHandler):
    """Handle incoming notification POST requests."""

    def do_POST(self):
        if self.path != "/notify":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid JSON")
            return

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

        # Display the notification
        _display_notification(data)

    def log_message(self, fmt, *args):
        """Suppress default HTTP log noise."""
        pass


def _display_notification(data: dict):
    """Show received notification with pet banner + desktop + sound."""
    command = data.get("command", "unknown")
    exit_code = data.get("exit_code", -1)
    duration = data.get("duration", 0)
    success = data.get("success", False)
    timestamp = data.get("timestamp", "")

    print(f"\n{'='*50}")
    print(f"[alrmpet] Notification received! ({timestamp})")
    print(f"{'='*50}")

    show_completion_banner(
        success=success,
        command=command,
        duration=duration,
        exit_code=exit_code,
        character="codex",
    )

    if data.get("stdout_tail"):
        print(f"--- stdout ---\n{data['stdout_tail']}")
    if data.get("stderr_tail"):
        print(f"--- stderr ---\n{data['stderr_tail']}")

    # Try desktop notification
    status = "Completed" if success else "Failed"
    icon = "dialog-information" if success else "dialog-error"
    body = f"Command: {command[:100]}\nDuration: {format_duration(duration)}"
    try:
        subprocess.run(
            ["notify-send", "-i", icon, "-u", "critical",
             f"[Remote] alrmpet: {status}", body],
            timeout=5, capture_output=True,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Terminal bell
    print("\a", end="", flush=True)


def start_listener(port: int = 9922):
    """Start the HTTP notification listener server."""
    server = HTTPServer(("0.0.0.0", port), _NotifyHandler)
    print(f"[alrmpet] Listening for notifications on 0.0.0.0:{port}")
    print(f"[alrmpet] Other machines can notify this one with config:")
    print(f"  remote:")
    print(f"    enabled: true")
    print(f"    host: \"<this-machine-ip>\"")
    print(f"    port: {port}")
    print(f"\n[alrmpet] Waiting for notifications... (Ctrl+C to stop)\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[alrmpet] Listener stopped.")
        server.server_close()
