"""Where claudio-tts keeps its files, per operating system."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def data_dir() -> Path:
    """Install root: venv, models and state. `CLAUDIO_TTS_HOME` overrides it."""
    override = os.environ.get("CLAUDIO_TTS_HOME")
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "claudio-tts"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "claudio-tts"
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "claudio-tts"


def model_dir() -> Path:
    return data_dir() / "models"


def state_dir() -> Path:
    path = data_dir() / "state"
    path.mkdir(parents=True, exist_ok=True)
    return path


def claude_dir() -> Path:
    """Claude Code's config directory (`CLAUDE_CONFIG_DIR`, else `~/.claude`)."""
    override = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(override).expanduser() if override else Path.home() / ".claude"


def mod_source() -> Path:
    """The Claude mod shipped inside this package."""
    return Path(__file__).parent / "mod"
