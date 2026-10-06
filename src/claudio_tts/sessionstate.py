"""A small per-session state file that add-ons (such as claudio-vibecode) can read.

The mod writes it whenever the session's mute switch changes; nothing here is needed to speak.
"""

from __future__ import annotations

import json
import re

from claudio_tts.paths import state_dir

_SAFE = re.compile(r"[^A-Za-z0-9_.-]")


def _file(session: str):
    folder = state_dir() / "sessions"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{_SAFE.sub('_', session) or 'default'}.json"


def read(session: str) -> dict:
    try:
        data = json.loads(_file(session).read_text())
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write(session: str, **values: object) -> None:
    data = read(session)
    data.update(values)
    _file(session).write_text(json.dumps(data))


def clear(session: str) -> None:
    _file(session).unlink(missing_ok=True)
