"""Configuration management for alrmpet."""

import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List

CONFIG_SEARCH_PATHS = [
    Path.home() / ".config" / "alrmpet" / "config.yaml",
    Path.home() / ".alrmpet.yaml",
    Path.cwd() / "alrmpet.yaml",
]


@dataclass
class EmailConfig:
    enabled: bool = False
    smtp_server: str = ""
    smtp_port: int = 587
    use_tls: bool = True
    username: str = ""
    password: str = ""
    from_addr: str = ""
    to_addrs: List[str] = field(default_factory=list)


@dataclass
class WebhookConfig:
    enabled: bool = False
    url: str = ""
    platform: str = "discord"


@dataclass
class NtfyConfig:
    """ntfy.sh push notification config."""
    enabled: bool = False
    topic: str = ""
    server: str = "https://ntfy.sh"


@dataclass
class RemoteConfig:
    """Direct HTTP push to a remote listener."""
    enabled: bool = False
    host: str = ""
    port: int = 9922


@dataclass
class PetConfig:
    enabled: bool = True
    character: str = "codex"
    show_stats: bool = True


@dataclass
class NotificationConfig:
    email: EmailConfig = field(default_factory=EmailConfig)
    webhook: WebhookConfig = field(default_factory=WebhookConfig)
    ntfy: NtfyConfig = field(default_factory=NtfyConfig)
    remote: RemoteConfig = field(default_factory=RemoteConfig)
    pet: PetConfig = field(default_factory=PetConfig)
    desktop: bool = True
    sound: bool = True


@dataclass
class AppConfig:
    notification: NotificationConfig = field(default_factory=NotificationConfig)
    poll_interval: float = 2.0
    tail_lines: int = 20


def _build(cls, data: dict):
    valid = {f.name for f in cls.__dataclass_fields__.values()}
    return cls(**{k: v for k, v in data.items() if k in valid})


def load_config(config_path: Optional[str] = None) -> AppConfig:
    paths = [Path(config_path)] if config_path else CONFIG_SEARCH_PATHS
    for p in paths:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return _parse_config(data)
    return AppConfig()


def _parse_config(data: dict) -> AppConfig:
    nd = data.get("notification", {})
    notification = NotificationConfig(
        email=_build(EmailConfig, nd.get("email", {})),
        webhook=_build(WebhookConfig, nd.get("webhook", {})),
        ntfy=_build(NtfyConfig, nd.get("ntfy", {})),
        remote=_build(RemoteConfig, nd.get("remote", {})),
        pet=_build(PetConfig, nd.get("pet", {})),
        desktop=nd.get("desktop", True),
        sound=nd.get("sound", True),
    )
    return AppConfig(
        notification=notification,
        poll_interval=data.get("poll_interval", 2.0),
        tail_lines=data.get("tail_lines", 20),
    )


CONFIG_TEMPLATE = """\
# alrmpet configuration
notification:
  email:
    enabled: false
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    use_tls: true
    username: "your-email@gmail.com"
    password: "your-app-password"
    from_addr: "your-email@gmail.com"
    to_addrs:
      - "recipient@example.com"

  webhook:
    enabled: false
    url: "https://discord.com/api/webhooks/your-webhook-url"
    platform: "discord"

  # ntfy.sh - free push notifications (phone/browser/desktop)
  ntfy:
    enabled: false
    topic: "my-alrmpet-alerts"
    server: "https://ntfy.sh"

  # Direct HTTP push to remote machine
  # Run 'alrmpet --listen 9922' on the remote machine first
  remote:
    enabled: false
    host: "192.168.1.100"
    port: 9922

  pet:
    enabled: true
    character: "codex"  # codex, dewey, fireball, rocky, seedy
    show_stats: true

  desktop: true
  sound: true

poll_interval: 2.0
tail_lines: 20
"""
