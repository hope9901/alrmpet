"""Notification dispatching - email, webhook, ntfy, remote push, desktop, sound."""

import smtplib
import subprocess
import json
import urllib.request
import urllib.error
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from .config import AppConfig
from .monitor import ProcessResult
from .pet import format_duration


def send_all(result: ProcessResult, config: AppConfig):
    """Dispatch notifications through all enabled channels."""
    channels = [
        (config.notification.email.enabled, _send_email),
        (config.notification.webhook.enabled, _send_webhook),
        (config.notification.ntfy.enabled, _send_ntfy),
        (config.notification.remote.enabled, _send_remote),
        (config.notification.desktop, _send_desktop),
        (config.notification.sound, _send_sound),
    ]
    for enabled, fn in channels:
        if enabled:
            try:
                fn(result, config)
            except Exception as e:
                print(f"[alrmpet] {fn.__name__} error: {e}")


def _result_to_dict(result: ProcessResult) -> dict:
    """Serialize ProcessResult to dict for JSON transport."""
    return {
        "command": result.command,
        "exit_code": result.exit_code,
        "duration": result.duration,
        "duration_str": format_duration(result.duration),
        "success": result.exit_code == 0,
        "stdout_tail": result.stdout_tail,
        "stderr_tail": result.stderr_tail,
        "timestamp": datetime.now().isoformat(),
    }


# -- Email ---------------------------------------------------------------------

def _send_email(result: ProcessResult, config: AppConfig):
    ec = config.notification.email
    if not ec.smtp_server or not ec.to_addrs:
        print("[alrmpet] Email not configured. Skipping.")
        return

    status = "SUCCESS" if result.exit_code == 0 else f"FAILED (exit {result.exit_code})"
    subject = f"[alrmpet] {status}: {result.command[:50]}"
    body = (
        f"Process Completion Report\n"
        f"========================\n"
        f"Command:   {result.command}\n"
        f"Status:    {status}\n"
        f"Exit Code: {result.exit_code}\n"
        f"Duration:  {format_duration(result.duration)}\n"
        f"Time:      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )
    if result.stdout_tail:
        body += f"\n--- stdout (tail) ---\n{result.stdout_tail}\n"
    if result.stderr_tail:
        body += f"\n--- stderr (tail) ---\n{result.stderr_tail}\n"

    msg = MIMEMultipart()
    msg["From"] = ec.from_addr or ec.username
    msg["To"] = ", ".join(ec.to_addrs)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    server = smtplib.SMTP(ec.smtp_server, ec.smtp_port)
    if ec.use_tls:
        server.ehlo()
        server.starttls()
    if ec.username and ec.password:
        server.login(ec.username, ec.password)
    server.sendmail(ec.from_addr or ec.username, ec.to_addrs, msg.as_string())
    server.quit()
    print(f"[alrmpet] Email sent -> {', '.join(ec.to_addrs)}")


# -- Webhook (Discord / Slack) -------------------------------------------------

def _send_webhook(result: ProcessResult, config: AppConfig):
    wh = config.notification.webhook
    if not wh.url:
        return
    try:
        import requests
    except ImportError:
        print("[alrmpet] 'requests' not installed. Skipping webhook.")
        return

    status = "SUCCESS" if result.exit_code == 0 else "FAILED"
    if wh.platform == "discord":
        color = 0x2ECC71 if result.exit_code == 0 else 0xE74C3C
        payload = {"embeds": [{
            "title": f"[alrmpet] {status}",
            "color": color,
            "fields": [
                {"name": "Command", "value": f"`{result.command[:200]}`", "inline": False},
                {"name": "Exit Code", "value": str(result.exit_code), "inline": True},
                {"name": "Duration", "value": format_duration(result.duration), "inline": True},
            ],
        }]}
    else:
        emoji = ":white_check_mark:" if result.exit_code == 0 else ":x:"
        payload = {"text": f"{emoji} *[alrmpet] {status}*\n`{result.command[:200]}`"}

    resp = requests.post(wh.url, json=payload, timeout=10)
    print(f"[alrmpet] Webhook sent ({wh.platform}) HTTP {resp.status_code}")


# -- ntfy.sh (push notification to phone/browser/desktop) ----------------------

def _send_ntfy(result: ProcessResult, config: AppConfig):
    """Send push notification via ntfy.sh - works on phone, browser, desktop."""
    ntfy = config.notification.ntfy
    if not ntfy.topic:
        print("[alrmpet] ntfy topic not set. Skipping.")
        return

    status = "SUCCESS" if result.exit_code == 0 else "FAILED"
    url = f"{ntfy.server}/{ntfy.topic}"
    title = f"[alrmpet] {status}"
    body = (
        f"Command: {result.command[:200]}\n"
        f"Exit Code: {result.exit_code}\n"
        f"Duration: {format_duration(result.duration)}"
    )
    tags = "white_check_mark" if result.exit_code == 0 else "x"
    priority = "default" if result.exit_code == 0 else "high"

    req = urllib.request.Request(url, data=body.encode("utf-8"), method="POST")
    req.add_header("Title", title)
    req.add_header("Tags", tags)
    req.add_header("Priority", priority)

    try:
        resp = urllib.request.urlopen(req, timeout=10)
        print(f"[alrmpet] ntfy sent -> {ntfy.topic} (HTTP {resp.status})")
    except urllib.error.URLError as e:
        print(f"[alrmpet] ntfy failed: {e}")


# -- Remote HTTP push (direct to IP:port) --------------------------------------

def _send_remote(result: ProcessResult, config: AppConfig):
    """Send notification to a remote alrmpet listener via HTTP POST."""
    remote = config.notification.remote
    if not remote.host:
        print("[alrmpet] Remote host not set. Skipping.")
        return

    url = f"http://{remote.host}:{remote.port}/notify"
    payload = json.dumps(_result_to_dict(result)).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")

    try:
        resp = urllib.request.urlopen(req, timeout=10)
        print(f"[alrmpet] Remote push sent -> {remote.host}:{remote.port} (HTTP {resp.status})")
    except urllib.error.URLError as e:
        print(f"[alrmpet] Remote push failed: {e}")


# -- Desktop notification (notify-send, Linux) ---------------------------------

def _send_desktop(result: ProcessResult, _config: AppConfig = None):
    status = "Completed" if result.exit_code == 0 else "Failed"
    icon = "dialog-information" if result.exit_code == 0 else "dialog-error"
    body = f"Command: {result.command[:100]}\nDuration: {format_duration(result.duration)}"
    try:
        subprocess.run(
            ["notify-send", "-i", icon, "-u", "normal", f"alrmpet: {status}", body],
            timeout=5, capture_output=True,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


# -- Sound (terminal bell) -----------------------------------------------------

def _send_sound(result: ProcessResult, _config: AppConfig = None):
    print("\a", end="", flush=True)
