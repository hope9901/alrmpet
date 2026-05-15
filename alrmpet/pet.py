"""Terminal pet animation - Codex-style colored ASCII companions."""

import sys
import time
import threading
from enum import Enum
from typing import Optional

# -- ANSI color codes -----------------------------------------------------------
RST = "\033[0m"
BOLD = "\033[1m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
ORANGE = "\033[38;5;208m"
GRAY = "\033[90m"
WHITE = "\033[97m"
MAGENTA = "\033[95m"
DIM = "\033[2m"


class PetState(Enum):
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    WAITING = "waiting"


def _c(color, text):
    """Colorize text with ANSI codes."""
    return f"{color}{text}{RST}"


# -- Codex-style character definitions ------------------------------------------
# Inspired by Codex pets: Codex(blue), Dewey(orange duck), Fireball(red),
# Rocky(gray), Seedy(green). Multiple frames create working animation.

CHARACTERS = {
    "codex": {
        "color": BLUE,
        PetState.RUNNING: [
            [_c(BLUE, "  .----."),   _c(BLUE, " /") + _c(CYAN, " >  >") + _c(BLUE, " \\"),  _c(BLUE, " |") + _c(CYAN, " === ") + _c(BLUE, "|"),   _c(BLUE, "  '----'"),   _c(DIM, "  /|  |\\") + _c(YELLOW, "  ~ coding")],
            [_c(BLUE, "  .----."),   _c(BLUE, " /") + _c(CYAN, " >  >") + _c(BLUE, " \\"),  _c(BLUE, " |") + _c(CYAN, " === ") + _c(BLUE, "|"),   _c(BLUE, "  '----'"),   _c(DIM, "  \\|  |/") + _c(YELLOW, "  ~ coding.")],
            [_c(BLUE, "  .----."),   _c(BLUE, " /") + _c(CYAN, " -  -") + _c(BLUE, " \\"),  _c(BLUE, " |") + _c(CYAN, " === ") + _c(BLUE, "|"),   _c(BLUE, "  '----'"),   _c(DIM, "  /|  |\\") + _c(YELLOW, "  ~ coding..")],
            [_c(BLUE, "  .----."),   _c(BLUE, " /") + _c(CYAN, " >  >") + _c(BLUE, " \\"),  _c(BLUE, " |") + _c(CYAN, " === ") + _c(BLUE, "|"),   _c(BLUE, "  '----'"),   _c(DIM, "  \\|  |/") + _c(YELLOW, "  ~ coding...")],
        ],
        PetState.SUCCESS: [
            [_c(BLUE, "  .----."),   _c(BLUE, " /") + _c(GREEN, " ^  ^") + _c(BLUE, " \\"),  _c(BLUE, " |") + _c(GREEN, " \\__/") + _c(BLUE, " |"),  _c(BLUE, "  '----'"),   _c(GREEN, " \\(^o^)/  Done!")],
            [_c(BLUE, "  .----."),   _c(BLUE, " /") + _c(GREEN, " *  *") + _c(BLUE, " \\"),  _c(BLUE, " |") + _c(GREEN, " \\__/") + _c(BLUE, " |"),  _c(BLUE, "  '----'"),   _c(GREEN, "  (^o^)   Done!")],
        ],
        PetState.ERROR: [
            [_c(BLUE, "  .----."),   _c(BLUE, " /") + _c(RED, " x  x") + _c(BLUE, " \\"),   _c(BLUE, " |") + _c(RED, " --- ") + _c(BLUE, "|"),   _c(BLUE, "  '----'"),   _c(RED, "  (T_T)   Fail!")],
        ],
        PetState.WAITING: [
            [_c(BLUE, "  .----."),   _c(BLUE, " /") + _c(DIM, " o  o") + _c(BLUE, " \\"),   _c(BLUE, " |") + _c(DIM, " --- ") + _c(BLUE, "|"),   _c(BLUE, "  '----'"),   _c(DIM, "  /|  |\\   zzZ")],
            [_c(BLUE, "  .----."),   _c(BLUE, " /") + _c(DIM, " -  -") + _c(BLUE, " \\"),   _c(BLUE, " |") + _c(DIM, " --- ") + _c(BLUE, "|"),   _c(BLUE, "  '----'"),   _c(DIM, "  /|  |\\  zZzZ")],
        ],
    },
    "dewey": {
        "color": ORANGE,
        PetState.RUNNING: [
            [_c(ORANGE, "   __"),     _c(ORANGE, " >(") + _c(YELLOW, "oo") + _c(ORANGE, ")>"),  _c(ORANGE, "  (  )_"),    _c(ORANGE, "   ^^  ") + _c(YELLOW, " ~ quack")],
            [_c(ORANGE, "   __"),     _c(ORANGE, " >(") + _c(YELLOW, "--") + _c(ORANGE, ")>"),  _c(ORANGE, "  (  )_"),    _c(ORANGE, "   ^^  ") + _c(YELLOW, " ~ quack.")],
            [_c(ORANGE, "   __"),     _c(ORANGE, " <(") + _c(YELLOW, "oo") + _c(ORANGE, ")<"),  _c(ORANGE, "  _(  )"),    _c(ORANGE, "   ^^  ") + _c(YELLOW, " ~ quack..")],
            [_c(ORANGE, "   __"),     _c(ORANGE, " <(") + _c(YELLOW, "--") + _c(ORANGE, ")<"),  _c(ORANGE, "  _(  )"),    _c(ORANGE, "   ^^  ") + _c(YELLOW, " ~ quack...")],
        ],
        PetState.SUCCESS: [
            [_c(ORANGE, "   __"),     _c(ORANGE, " <(") + _c(GREEN, "^^") + _c(ORANGE, ")>"),  _c(ORANGE, " \\(  )/"),   _c(ORANGE, "   ^^  ") + _c(GREEN, " QUACK!!")],
        ],
        PetState.ERROR: [
            [_c(ORANGE, "   __"),     _c(ORANGE, "  (") + _c(RED, ";;") + _c(ORANGE, ")"),    _c(ORANGE, "  (  )_"),    _c(ORANGE, "   ^^  ") + _c(RED, " quack...")],
        ],
        PetState.WAITING: [
            [_c(ORANGE, "   __"),     _c(ORANGE, "  (") + _c(DIM, "oo") + _c(ORANGE, ")"),    _c(ORANGE, "  (  )_"),    _c(DIM, "   ^^   zzZ")],
        ],
    },
    "fireball": {
        "color": RED,
        PetState.RUNNING: [
            [_c(YELLOW, "  )\\/)"),   _c(RED, "  (") + _c(YELLOW, "* *") + _c(RED, ")"),    _c(RED, "  /^^^\\"),    _c(RED, " {_____}") + _c(YELLOW, " ~ burn!")],
            [_c(YELLOW, "  (/\\("),   _c(RED, "  (") + _c(YELLOW, "o o") + _c(RED, ")"),    _c(RED, "  /^^^\\"),    _c(RED, " {_____}") + _c(YELLOW, " ~ burn!.")],
            [_c(YELLOW, "  )\\/)"),   _c(RED, "  (") + _c(YELLOW, "* *") + _c(RED, ")"),    _c(RED, "  /^^^\\"),    _c(RED, " {_____}") + _c(YELLOW, " ~ burn!..")],
            [_c(YELLOW, "  (/\\("),   _c(RED, "  (") + _c(YELLOW, "- -") + _c(RED, ")"),    _c(RED, "  /^^^\\"),    _c(RED, " {_____}") + _c(YELLOW, " ~ burn!...")],
        ],
        PetState.SUCCESS: [
            [_c(YELLOW, " \\)\\/)/ "),  _c(RED, "  (") + _c(GREEN, "^ ^") + _c(RED, ")"),   _c(RED, "  /\\~/\\"),   _c(RED, " {_____}") + _c(GREEN, " FIRE!!")],
        ],
        PetState.ERROR: [
            [_c(DIM, "   ..."),     _c(RED, "  (") + _c(DIM, "x x") + _c(RED, ")"),     _c(RED, "  /---\\"),    _c(RED, " {_____}") + _c(DIM, " poof..")],
        ],
        PetState.WAITING: [
            [_c(DIM, "   ~"),       _c(RED, "  (") + _c(DIM, "- -") + _c(RED, ")"),     _c(RED, "  /^^^\\"),    _c(RED, " {_____}") + _c(DIM, " zzZ")],
        ],
    },
    "rocky": {
        "color": GRAY,
        PetState.RUNNING: [
            [_c(GRAY, "  ___"),     _c(GRAY, " [") + _c(WHITE, "-.-") + _c(GRAY, "]"),    _c(GRAY, " /===\\"),    _c(GRAY, " |___|") + _c(WHITE, "  ~ grind")],
            [_c(GRAY, "  ___"),     _c(GRAY, " [") + _c(WHITE, "o.o") + _c(GRAY, "]"),    _c(GRAY, " /===\\"),    _c(GRAY, " |___|") + _c(WHITE, "  ~ grind.")],
            [_c(GRAY, "  ___"),     _c(GRAY, " [") + _c(WHITE, "-.-") + _c(GRAY, "]"),    _c(GRAY, " /===\\"),    _c(GRAY, " |___|") + _c(WHITE, "  ~ grind..")],
            [_c(GRAY, "  ___"),     _c(GRAY, " [") + _c(WHITE, "o.o") + _c(GRAY, "]"),    _c(GRAY, " /===\\"),    _c(GRAY, " |___|") + _c(WHITE, "  ~ grind...")],
        ],
        PetState.SUCCESS: [
            [_c(GRAY, "  ___"),     _c(GRAY, " [") + _c(GREEN, "^.^") + _c(GRAY, "]"),   _c(GRAY, " /===\\"),    _c(GRAY, " |___|") + _c(GREEN, "  ROCK!")],
        ],
        PetState.ERROR: [
            [_c(GRAY, "  ___"),     _c(GRAY, " [") + _c(RED, "x.x") + _c(GRAY, "]"),    _c(GRAY, " /===\\"),    _c(GRAY, " |___|") + _c(RED, "  crack..")],
        ],
        PetState.WAITING: [
            [_c(GRAY, "  ___"),     _c(GRAY, " [") + _c(DIM, "-.o") + _c(GRAY, "]"),    _c(GRAY, " /===\\"),    _c(GRAY, " |___|") + _c(DIM, "  zzZ")],
        ],
    },
    "seedy": {
        "color": GREEN,
        PetState.RUNNING: [
            [_c(GREEN, "  \\|/"),    _c(GREEN, "  (") + _c(YELLOW, "o.o") + _c(GREEN, ")"),   _c(GREEN, "  .|."),     _c(GREEN, " _/|\\_") + _c(YELLOW, "  ~ grow")],
            [_c(GREEN, "  /|\\"),    _c(GREEN, "  (") + _c(YELLOW, "-.o") + _c(GREEN, ")"),   _c(GREEN, "  .|."),     _c(GREEN, " _/|\\_") + _c(YELLOW, "  ~ grow.")],
            [_c(GREEN, "  \\|/"),    _c(GREEN, "  (") + _c(YELLOW, "o.-") + _c(GREEN, ")"),   _c(GREEN, "  .|."),     _c(GREEN, " _/|\\_") + _c(YELLOW, "  ~ grow..")],
            [_c(GREEN, "  /|\\"),    _c(GREEN, "  (") + _c(YELLOW, "o.o") + _c(GREEN, ")"),   _c(GREEN, "  .|."),     _c(GREEN, " _/|\\_") + _c(YELLOW, "  ~ grow...")],
        ],
        PetState.SUCCESS: [
            [_c(GREEN, " \\\\|//"),   _c(GREEN, "  (") + _c(YELLOW, "^.^") + _c(GREEN, ")"),  _c(GREEN, "  \\|/"),    _c(GREEN, " _/|\\_") + _c(GREEN, "  BLOOM!")],
        ],
        PetState.ERROR: [
            [_c(DIM, "   ."),       _c(GREEN, "  (") + _c(RED, "x.x") + _c(GREEN, ")"),    _c(GREEN, "  .|."),     _c(GREEN, " _/|\\_") + _c(RED, "  wilt..")],
        ],
        PetState.WAITING: [
            [_c(DIM, "   ~"),       _c(GREEN, "  (") + _c(DIM, "-.~") + _c(GREEN, ")"),    _c(GREEN, "  .|."),     _c(GREEN, " _/|\\_") + _c(DIM, "  zzZ")],
        ],
    },
}

# Backward compat aliases
CHARACTERS["cat"] = CHARACTERS["codex"]
CHARACTERS["dog"] = CHARACTERS["dewey"]
CHARACTERS["robot"] = CHARACTERS["rocky"]
CHARACTERS["bird"] = CHARACTERS["seedy"]


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    m, s = divmod(int(seconds), 60)
    if m < 60:
        return f"{m}m {s}s"
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s"


def _strip_ansi(text: str) -> int:
    """Get visible length of text (excluding ANSI codes)."""
    import re
    return len(re.sub(r'\033\[[0-9;]*m', '', text))


class TerminalPet:
    """Animated terminal pet showing process status with ANSI colors."""

    def __init__(self, character: str = "codex", show_stats: bool = True):
        self.char_name = character
        self.frames = CHARACTERS.get(character, CHARACTERS["codex"])
        self.color = self.frames.get("color", BLUE)
        self.show_stats = show_stats
        self.state = PetState.WAITING
        self.frame_idx = 0
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._start_time = time.time()
        self._stats: dict = {}
        self._prev_lines = 0

    def _render(self) -> list:
        with self._lock:
            sf = self.frames.get(self.state, self.frames[PetState.WAITING])
            frame = sf[self.frame_idx % len(sf)]

        elapsed = time.time() - self._start_time
        c = self.color
        labels = {
            PetState.RUNNING: f"{c}[~]{RST} Running...",
            PetState.SUCCESS: f"{GREEN}[v]{RST} Completed!",
            PetState.ERROR:   f"{RED}[x]{RST} Failed!",
            PetState.WAITING: f"{DIM}[z]{RST} Waiting...",
        }

        W = 36
        border = f"  {c}+{'-' * W}+{RST}"
        lines = ["", border]
        for row in frame:
            pad = W - 2 - _strip_ansi(row)
            lines.append(f"  {c}|{RST} {row}{' ' * max(pad, 0)} {c}|{RST}")
        lines.append(border)
        lbl = labels[self.state]
        pad = W - 2 - _strip_ansi(lbl)
        lines.append(f"  {c}|{RST} {lbl}{' ' * max(pad, 0)} {c}|{RST}")
        dur = f"Time: {format_duration(elapsed)}"
        lines.append(f"  {c}|{RST} {dur:<{W - 2}} {c}|{RST}")
        if self.show_stats and self._stats:
            cpu_s = f"CPU: {self._stats.get('cpu', 'N/A')}"
            mem_s = f"MEM: {self._stats.get('memory', 'N/A')}"
            lines.append(f"  {c}|{RST} {cpu_s:<{W - 2}} {c}|{RST}")
            lines.append(f"  {c}|{RST} {mem_s:<{W - 2}} {c}|{RST}")
        lines.append(border)
        lines.append("")
        return lines

    def _loop(self):
        while self._running:
            lines = self._render()
            if self._prev_lines:
                sys.stderr.write(f"\033[{self._prev_lines}A\033[J")
            sys.stderr.write("\n".join(lines) + "\n")
            sys.stderr.flush()
            self._prev_lines = len(lines)
            with self._lock:
                sf = self.frames.get(self.state, self.frames[PetState.WAITING])
                self.frame_idx = (self.frame_idx + 1) % len(sf)
            time.sleep(0.6)

    def start(self):
        self._running = True
        self._start_time = time.time()
        self.state = PetState.RUNNING
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self, success: bool = True):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        self.state = PetState.SUCCESS if success else PetState.ERROR
        if self._prev_lines:
            sys.stderr.write(f"\033[{self._prev_lines}A\033[J")
        lines = self._render()
        sys.stderr.write("\n".join(lines) + "\n")
        sys.stderr.flush()

    def update_stats(self, cpu: str, memory: str):
        with self._lock:
            self._stats = {"cpu": cpu, "memory": memory}


def show_completion_banner(success: bool, command: str, duration: float,
                           exit_code: int, character: str = "codex"):
    frames = CHARACTERS.get(character, CHARACTERS["codex"])
    c = frames.get("color", BLUE)
    state = PetState.SUCCESS if success else PetState.ERROR
    frame = frames[state][0]
    status = f"{GREEN}SUCCESS{RST}" if success else f"{RED}FAILED{RST}"
    cmd_d = command if len(command) <= 28 else command[:25] + "..."

    W = 40
    border = f"  {c}+{'=' * W}+{RST}"
    sep = f"  {c}+{'-' * W}+{RST}"
    sys.stderr.write("\n")
    sys.stderr.write(border + "\n")
    sys.stderr.write(f"  {c}|{RST}  [{status}] Process finished{' ' * 10}{c}|{RST}\n")
    sys.stderr.write(sep + "\n")
    for row in frame:
        pad = W - 2 - _strip_ansi(row)
        sys.stderr.write(f"  {c}|{RST} {row}{' ' * max(pad, 0)} {c}|{RST}\n")
    sys.stderr.write(sep + "\n")
    sys.stderr.write(f"  {c}|{RST}  CMD:  {cmd_d:<{W - 9}}{c}|{RST}\n")
    sys.stderr.write(f"  {c}|{RST}  Time: {format_duration(duration):<{W - 9}}{c}|{RST}\n")
    sys.stderr.write(f"  {c}|{RST}  Exit: {exit_code:<{W - 9}}{c}|{RST}\n")
    sys.stderr.write(border + "\n\n")
    sys.stderr.flush()
