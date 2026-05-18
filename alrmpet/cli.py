"""CLI entry point for alrmpet - works like Linux `time` command.

Usage:
    alrmpet sleep 10                       # Run command, notify on finish
    alrmpet python train.py --epochs 100   # Flags after command go to command
    alrmpet --character dog -- make build   # Use -- to separate alrmpet flags
    alrmpet --watch-pid 12345              # Watch existing process
    alrmpet --watch-screen my_session      # Watch screen session
    alrmpet --init                         # Create config file
    alrmpet --test                         # Test notifications
"""

import sys
import threading

from . import __version__
from .config import load_config, CONFIG_TEMPLATE
from .monitor import run_passthrough, watch_pid, watch_screen, get_process_stats
from .notifier import send_all
from .pet import TerminalPet, show_completion_banner

# -- Flags that alrmpet recognises (everything else is part of the command) --

FLAGS_NO_ARG = {
    "--init", "--test", "--no-pet", "--no-email",
    "--no-desktop", "--no-sound", "--no-webhook",
    "--no-ntfy", "--no-remote",
    "-V", "--version", "-h", "--help",
}
FLAGS_WITH_ARG = {
    "--character", "-c", "--config", "--to",
    "--watch-pid", "--watch-screen", "--listen",
}


def _parse_argv(argv: list) -> tuple:
    """Split argv into (our_opts dict, command list).

    Parsing stops at the first unrecognised token or at `--`.
    This lets `alrmpet python script.py --epochs 100` work naturally
    without argparse trying to consume `--epochs`.
    """
    opts = {
        "config": None,
        "character": None,
        "to": None,
        "no_pet": False,
        "no_email": False,
        "no_desktop": False,
        "no_sound": False,
        "no_webhook": False,
        "no_ntfy": False,
        "no_remote": False,
        "watch_pid": None,
        "watch_screen": None,
        "listen": None,
        "init": False,
        "test": False,
        "help": False,
        "version": False,
    }
    command = []
    i = 0

    while i < len(argv):
        arg = argv[i]

        if arg == "--":
            command = argv[i + 1:]
            break

        if arg in FLAGS_NO_ARG:
            key = arg.lstrip("-").replace("-", "_")
            opts[key] = True
            i += 1
            continue

        if arg in FLAGS_WITH_ARG:
            key = arg.lstrip("-").replace("-", "_")
            if i + 1 >= len(argv):
                print(f"[alrmpet] Error: {arg} requires a value")
                sys.exit(1)
            opts[key] = argv[i + 1]
            i += 2
            continue

        # Unrecognised token -> start of the command
        command = argv[i:]
        break

    return opts, command


HELP_TEXT = f"""\
alrmpet v{__version__} - Prefix any command to get notified when it finishes.

Usage:
  alrmpet COMMAND [ARGS...]              Run command, notify on completion
  alrmpet [OPTIONS] -- COMMAND [ARGS...] Use -- to separate alrmpet options
  alrmpet --watch-pid PID               Watch running process by PID
  alrmpet --watch-screen NAME           Watch screen session
  alrmpet --listen PORT                 Start notification listener (receiver)
  alrmpet --init                        Create config file
  alrmpet --test                        Test notifications

Options:
  --to NAMES          Email recipients (initials, comma-separated, or 'all')
  --character NAME    Pet: codex, dewey, fireball, rocky, seedy
  --no-pet            Disable pet animation
  --no-email          Disable email
  --no-desktop        Disable desktop notification
  --no-sound          Disable terminal bell
  --no-webhook        Disable webhook
  --no-ntfy           Disable ntfy.sh push
  --no-remote         Disable remote HTTP push
  -c, --config PATH   Config file path
  -V, --version       Show version
  -h, --help          Show this help

Email recipients:
  Config recipients:  {{hyg: "h@gmail.com", kjw: "k@univ.kr"}}
  --to hyg            Send to hyg only
  --to hyg,kjw        Send to hyg and kjw
  --to all            Send to all recipients
  (no --to)           No email sent

Remote notification:
  Sender:   set remote.host/port in config.yaml
  Receiver: alrmpet --listen 9922
  ntfy.sh:  set ntfy.topic in config.yaml, install ntfy app on phone

Examples:
  alrmpet --to hyg sleep 10
  alrmpet --to all python train.py --epochs 100
  alrmpet --to hyg,kjw --character fireball -- bash long_job.sh
  alrmpet --watch-pid 12345
  alrmpet --listen 9922
"""


def _apply_overrides(config, opts):
    """Apply CLI flag overrides to the loaded config."""
    if opts["no_email"]:
        config.notification.email.enabled = False
    if opts["no_desktop"]:
        config.notification.desktop = False
    if opts["no_sound"]:
        config.notification.sound = False
    if opts["no_webhook"]:
        config.notification.webhook.enabled = False
    if opts["no_ntfy"]:
        config.notification.ntfy.enabled = False
    if opts["no_remote"]:
        config.notification.remote.enabled = False
    if opts["no_pet"]:
        config.notification.pet.enabled = False
    if opts["character"]:
        config.notification.pet.character = opts["character"]

    # Resolve --to: initials -> email addresses
    ec = config.notification.email
    if opts["to"]:
        if opts["to"] == "all":
            ec.to_addrs = list(ec.recipients.values())
        else:
            names = [n.strip() for n in opts["to"].split(",")]
            resolved = []
            for name in names:
                if name in ec.recipients:
                    resolved.append(ec.recipients[name])
                else:
                    print(f"[alrmpet] Warning: unknown recipient '{name}'")
                    print(f"[alrmpet] Available: {', '.join(ec.recipients.keys())}")
            ec.to_addrs = resolved
        if not ec.to_addrs:
            ec.enabled = False
    else:
        # No --to specified: disable email
        ec.enabled = False


def _run_with_pet(monitor_fn, config, pid_for_stats=None, animate=True):
    """Core orchestration: monitor -> notify.

    animate=True:  show pet animation during execution (for watch modes)
    animate=False: no animation during execution, banner after (for run mode)
    """
    pet_cfg = config.notification.pet
    pet = None

    # Only animate during execution for watch modes (no command output to clash)
    if pet_cfg.enabled and animate:
        pet = TerminalPet(character=pet_cfg.character, show_stats=pet_cfg.show_stats)
        pet.start()

    # Stats updater (only for PID watch mode)
    stats_stop = threading.Event()
    if pet and pid_for_stats:
        def _update():
            while not stats_stop.is_set():
                s = get_process_stats(pid_for_stats)
                if s:
                    pet.update_stats(s["cpu"], s["memory"])
                stats_stop.wait(config.poll_interval)
        threading.Thread(target=_update, daemon=True).start()

    try:
        result = monitor_fn()
    except KeyboardInterrupt:
        if pet:
            pet.stop(success=False)
        print("\n[alrmpet] Interrupted.", file=sys.stderr)
        sys.exit(130)
    finally:
        stats_stop.set()

    success = result.exit_code == 0
    if pet:
        pet.stop(success=success)
    elif pet_cfg.enabled:
        # Run mode: show completion banner after command finishes
        show_completion_banner(
            success=success, command=result.command,
            duration=result.duration, exit_code=result.exit_code,
            character=pet_cfg.character,
        )

    send_all(result, config)
    return result


# -- Subcommand handlers -------------------------------------------------------

def _handle_init(opts):
    from pathlib import Path
    target = Path.home() / ".config" / "alrmpet" / "config.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        print(f"[alrmpet] Config already exists: {target}")
        print("[alrmpet] Delete it first if you want to regenerate.")
        return
    target.write_text(CONFIG_TEMPLATE, encoding="utf-8")
    print(f"[alrmpet] Config created: {target}")
    print("[alrmpet] Edit it to set up email, webhook, etc.")


def _handle_test(opts):
    from .monitor import ProcessResult
    config = load_config(opts["config"])
    _apply_overrides(config, opts)

    print("[alrmpet] Sending test notification...")
    test_result = ProcessResult(
        exit_code=0, duration=42.5, command="test-notification",
        stdout_tail="This is a test from alrmpet.",
    )
    send_all(test_result, config)
    show_completion_banner(
        success=True, command="test-notification",
        duration=42.5, exit_code=0,
        character=config.notification.pet.character,
    )
    print("[alrmpet] Test complete!")


def _handle_watch_pid(opts):
    pid = int(opts["watch_pid"])
    config = load_config(opts["config"])
    _apply_overrides(config, opts)

    print(f"[alrmpet] Watching PID {pid}...", file=sys.stderr)
    result = _run_with_pet(
        lambda: watch_pid(pid, config.poll_interval),
        config, pid_for_stats=pid,
    )
    sys.exit(result.exit_code)


def _handle_watch_screen(opts):
    name = opts["watch_screen"]
    config = load_config(opts["config"])
    _apply_overrides(config, opts)

    print(f"[alrmpet] Watching screen '{name}'...", file=sys.stderr)
    result = _run_with_pet(
        lambda: watch_screen(name, config.poll_interval),
        config,
    )
    sys.exit(result.exit_code)


def _handle_run(opts, command):
    if not command:
        print("[alrmpet] Error: no command specified.")
        print("  Usage: alrmpet COMMAND [ARGS...]")
        print("  Run 'alrmpet --help' for more info.")
        sys.exit(1)

    config = load_config(opts["config"])
    _apply_overrides(config, opts)

    cmd_str = " ".join(command)
    print(f"[alrmpet] Running: {cmd_str}", file=sys.stderr)

    result = _run_with_pet(lambda: run_passthrough(command), config, animate=False)
    sys.exit(result.exit_code)


# -- Main entry point -----------------------------------------------------------

def main():
    opts, command = _parse_argv(sys.argv[1:])

    if opts["help"]:
        print(HELP_TEXT)
        return
    if opts["version"]:
        print(f"alrmpet {__version__}")
        return
    if opts["init"]:
        return _handle_init(opts)
    if opts["test"]:
        return _handle_test(opts)
    if opts["listen"]:
        from .receiver import start_listener
        start_listener(int(opts["listen"]))
        return
    if opts["watch_pid"]:
        return _handle_watch_pid(opts)
    if opts["watch_screen"]:
        return _handle_watch_screen(opts)

    _handle_run(opts, command)


if __name__ == "__main__":
    main()
