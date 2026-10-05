"""Install the Claude mod into Claude Code's config directory and register it in settings.json."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from claudio_tts.paths import claude_dir as default_claude_dir
from claudio_tts.paths import mod_source

MOD_NAME = "claudio-tts"
LEGACY_NAMES = ("kokoro-tts",)  # the pre-release name of this mod
PLUGIN_DIRS = "CLAUDE_CODE_PLUGIN_DIRS"
PYTHON_VAR = "CLAUDIO_TTS_PYTHON"


class SettingsError(RuntimeError):
    """settings.json exists but cannot be safely edited."""


def _norm(path: str) -> str:
    return os.path.normcase(os.path.normpath(path))


def _load(settings: Path) -> dict:
    if not settings.exists():
        return {}
    try:
        data = json.loads(settings.read_text(encoding="utf-8"))
    except ValueError as error:
        raise SettingsError(
            f"{settings} is not valid JSON ({error}); fix it and run again"
        ) from error
    if not isinstance(data, dict):
        raise SettingsError(f"{settings} must hold a JSON object")
    return data


def _save(settings: Path, data: dict, before: str | None) -> bool:
    """Write settings if they changed, keeping a one-time backup. Returns True if written."""
    after = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if before is not None and json.loads(before) == data:
        return False
    settings.parent.mkdir(parents=True, exist_ok=True)
    if before is not None:
        backup = settings.with_name(settings.name + ".claudio-tts.bak")
        if not backup.exists():
            backup.write_text(before, encoding="utf-8")
    settings.write_text(after, encoding="utf-8")
    return True


def _dirs(env: dict) -> list[str]:
    return [p for p in str(env.get(PLUGIN_DIRS, "")).split(os.pathsep) if p]


def install(
    python: str,
    claude_dir: Path | None = None,
    link: bool = False,
    source: Path | None = None,
) -> dict:
    """Copy (or link) the mod into `<claude>/mods/claudio-tts` and register it. Idempotent."""
    claude = claude_dir or default_claude_dir()
    source = source or mod_source()
    dest = claude / "mods" / MOD_NAME
    settings = claude / "settings.json"
    before = settings.read_text(encoding="utf-8") if settings.exists() else None
    data = _load(settings)  # fail before touching anything if settings are unusable

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink() or dest.is_file():
        dest.unlink()
    elif dest.exists():
        shutil.rmtree(dest)
    if link:
        dest.symlink_to(source, target_is_directory=True)
    else:
        shutil.copytree(source, dest, ignore=shutil.ignore_patterns("node_modules", "__pycache__"))

    env = data.setdefault("env", {})
    legacy = {_norm(str(claude / "mods" / name)) for name in LEGACY_NAMES}
    kept = [p for p in _dirs(env) if _norm(p) not in legacy and _norm(p) != _norm(str(dest))]
    env[PLUGIN_DIRS] = os.pathsep.join([*kept, str(dest)])
    env[PYTHON_VAR] = python
    changed = _save(settings, data, before)
    return {"mod": str(dest), "settings": str(settings), "changed": changed, "linked": link}


def uninstall(claude_dir: Path | None = None) -> dict:
    claude = claude_dir or default_claude_dir()
    dest = claude / "mods" / MOD_NAME
    settings = claude / "settings.json"
    before = settings.read_text(encoding="utf-8") if settings.exists() else None
    data = _load(settings)
    env = data.get("env", {})
    if isinstance(env, dict):
        kept = [p for p in _dirs(env) if _norm(p) != _norm(str(dest))]
        if kept:
            env[PLUGIN_DIRS] = os.pathsep.join(kept)
        else:
            env.pop(PLUGIN_DIRS, None)
        env.pop(PYTHON_VAR, None)
        if not env:
            data.pop("env", None)
    changed = _save(settings, data, before) if before is not None else False
    if dest.is_symlink() or dest.is_file():
        dest.unlink()
    elif dest.exists():
        shutil.rmtree(dest)
    return {"mod": str(dest), "settings": str(settings), "changed": changed}
