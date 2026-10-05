"""Lower music while Claude speaks, then put it back. macOS only (Apple Music, Spotify) for now."""

from __future__ import annotations

import json
import os
import subprocess
import sys

from claudio_tts.paths import state_dir

APPS = ("Music", "Spotify")
MIN_VOLUME = 5


def enabled() -> bool:
    return (
        sys.platform == "darwin" and os.environ.get("AUDIO_DUCK_ENABLED", "true").lower() == "true"
    )


def _level() -> int:
    try:
        return max(0, min(100, int(os.environ.get("DUCK_LEVEL", "5"))))
    except ValueError:
        return 5


def _osascript(script: str) -> str | None:
    try:
        done = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, timeout=3, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def _running(app: str) -> bool:
    return _osascript(f'application "{app}" is running') == "true"


def _get(app: str) -> int | None:
    out = _osascript(f'tell application "{app}" to get sound volume')
    return int(out) if out and out.lstrip("-").isdigit() else None


def _set(app: str, volume: int) -> None:
    _osascript(f'tell application "{app}" to set sound volume to {int(volume)}')


def ducked_ratio(volume: int, level: int) -> int:
    """The volume to duck to: `level` percent of the original, never below the floor."""
    return max(MIN_VOLUME, volume * level // 100) if volume > MIN_VOLUME else volume


def duck() -> None:
    if not enabled():
        return
    saved = state_dir() / "duck.json"
    if saved.exists():  # already ducked by another session; restore() will undo it once
        return
    original: dict[str, int] = {}
    for app in APPS:
        if _running(app) and (volume := _get(app)) is not None:
            original[app] = volume
            _set(app, ducked_ratio(volume, _level()))
    if original:
        saved.write_text(json.dumps(original))


def restore() -> None:
    if not enabled():
        return
    saved = state_dir() / "duck.json"
    try:
        original = json.loads(saved.read_text())
    except (OSError, ValueError):
        return
    for app, volume in original.items():
        if _running(app):
            _set(app, volume)
    saved.unlink(missing_ok=True)
