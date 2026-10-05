"""Record a REAL Claude Code session (through tmux) and stitch it after the install scene.

It starts `claude` in a scratch folder, types real commands and one real prompt, and
snapshots the screen.
That uses your own Claude login and spends one short prompt. Nothing is faked. Needs tmux.

    python scripts/record_claude_demo.py PART1.cast OUT.cast
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from pathlib import Path

SESSION = "claudio-demo"
COLS, ROWS = 108, 30
CWD = Path("/tmp/claudio-demo-claude")
PROMPT = "In two sentences, what is a mutex?"
CLEAR = "\x1b[H\x1b[2J"


def tmux(*args: str) -> str:
    return subprocess.run(["tmux", *args], capture_output=True, text=True).stdout


def screen() -> str:
    return tmux("capture-pane", "-t", SESSION, "-p", "-e")


def press(*keys: str) -> None:
    tmux("send-keys", "-t", SESSION, *keys)


def type_text(text: str, delay: float = 0.06) -> None:
    for ch in text:
        tmux("send-keys", "-t", SESSION, "-l", ch)
        time.sleep(delay)


def card(lines: list[str]) -> str:
    pad = (ROWS - len(lines)) // 2
    body = "\r\n" * pad
    for i, text in enumerate(lines):
        color = "1;36" if i == 0 else "37"
        body += f"\x1b[{color}m{text.center(COLS).rstrip()}\x1b[0m\r\n\r\n"
    return CLEAR + body


def record(events: list[tuple[float, str]]) -> None:
    CWD.mkdir(parents=True, exist_ok=True)
    tmux("kill-session", "-t", SESSION)
    tmux(
        "new-session",
        "-d",
        "-s",
        SESSION,
        "-x",
        str(COLS),
        "-y",
        str(ROWS),
        "-c",
        str(CWD),
        "claude",
    )
    start, last, stop = time.time(), "", False

    def sample() -> None:
        nonlocal last
        while not stop:
            snap = screen()
            if snap != last:
                last = snap
                events.append((time.time() - start, CLEAR + snap.replace("\n", "\r\n")))
            time.sleep(0.15)

    sampler = threading.Thread(target=sample, daemon=True)
    # Wait for the trust prompt or the main screen, accept trust for the scratch folder once.
    time.sleep(5)
    if "trust this folder" in screen():
        press("Down", "Enter")
        time.sleep(4)
    sampler.start()
    time.sleep(2.2)
    type_text("/voi")
    time.sleep(2.2)  # the menu names "Toggle voice mode": Claude Code's own voice input
    press("C-u")
    time.sleep(0.4)
    type_text("/tts")
    time.sleep(1.8)
    press("C-u")
    time.sleep(0.4)
    type_text("/tts unmute")
    press("Enter")
    time.sleep(2.5)
    type_text("/tts voice af_heart")
    press("Enter")
    time.sleep(5)
    type_text(PROMPT)
    time.sleep(0.6)
    press("Enter")
    began = time.time()
    quiet_since, seen = time.time(), screen()
    while time.time() - began < 120:
        time.sleep(0.5)
        now = screen()
        if now != seen:
            seen, quiet_since = now, time.time()
        if (
            time.time() - began > 4
            and time.time() - quiet_since > 4
            and "esc to interrupt" not in now
        ):
            break
    time.sleep(7)  # let the spoken reply play
    stop = True
    sampler.join(timeout=2)
    tmux("kill-session", "-t", SESSION)


def assemble(part1: Path, out: Path, events: list[tuple[float, str]]) -> None:
    lines = part1.read_text(encoding="utf-8").splitlines()
    header = json.loads(lines[0])
    header["term"] = {**header.get("term", {}), "cols": COLS, "rows": ROWS}
    rows = [json.loads(line) for line in lines[1:]]
    cards = [
        (1.0, card(["Install", "one command: Python, dependencies, voice model and mod"])),
    ]
    out_rows: list[list] = []
    out_rows.append([0.0, "o", cards[0][1]])
    out_rows.append([2.2, "o", CLEAR])
    out_rows.extend(rows)
    out_rows.append(
        [
            0.5,
            "o",
            card(
                [
                    "Use it in Claude Code",
                    "Claude talks back. Claude's own /voice lets you talk to it.",
                ]
            ),
        ]
    )
    out_rows.append([2.6, "o", CLEAR])
    previous = 0.0
    for stamp, data in events:
        out_rows.append([max(0.03, stamp - previous), "o", data])
        previous = stamp
    out_rows.append([4.0, "o", card(["That's it.", "github.com/restante/claudio-tts"])])
    with out.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(header) + "\n")
        for row in out_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    part1, out = Path(sys.argv[1]), Path(sys.argv[2])
    events: list[tuple[float, str]] = []
    record(events)
    assemble(part1, out, events)
    print(f"recorded {len(events)} screen changes -> {out}")


if __name__ == "__main__":
    main()
