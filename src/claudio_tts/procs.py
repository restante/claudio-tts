"""Per-session worker bookkeeping: find a session's speech process and stop it, and only it."""

from __future__ import annotations

import json
import re
from pathlib import Path

import psutil

from claudio_tts.paths import state_dir

_SAFE = re.compile(r"[^A-Za-z0-9_.-]")


def _dir() -> Path:
    path = state_dir() / "workers"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _file(session: str) -> Path:
    return _dir() / f"{_SAFE.sub('_', session) or 'default'}.json"


def register(session: str, pid: int) -> None:
    """Record `pid` as this session's worker (its start time guards against pid reuse)."""
    created = psutil.Process(pid).create_time()
    _file(session).write_text(json.dumps({"pid": pid, "created": created}))


def _alive(record: dict) -> psutil.Process | None:
    try:
        proc = psutil.Process(record["pid"])
        if abs(proc.create_time() - record["created"]) < 1 and proc.is_running():
            return proc
    except (psutil.Error, KeyError, TypeError):
        pass
    return None


def _kill_tree(proc: psutil.Process) -> None:
    family = proc.children(recursive=True) + [proc]
    for p in family:
        try:
            p.terminate()
        except psutil.Error:
            pass
    _, alive = psutil.wait_procs(family, timeout=1.0)
    for p in alive:
        try:
            p.kill()
        except psutil.Error:
            pass


def stop(session: str) -> bool:
    """Stop this session's speech. Returns True if a worker was running."""
    path = _file(session)
    try:
        record = json.loads(path.read_text())
    except (OSError, ValueError):
        return False
    proc = _alive(record)
    path.unlink(missing_ok=True)
    if proc is None:
        return False
    _kill_tree(proc)
    return True


def stop_all() -> int:
    """Stop every session's worker (used before an update). Returns how many were running."""
    count = 0
    for path in _dir().glob("*.json"):
        try:
            record = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        path.unlink(missing_ok=True)
        proc = _alive(record)
        if proc is not None:
            _kill_tree(proc)
            count += 1
    return count


def clear(session: str) -> None:
    _file(session).unlink(missing_ok=True)


def others_speaking(session: str) -> bool:
    """True if any other session still has a live worker."""
    mine = _file(session).name
    for path in _dir().glob("*.json"):
        if path.name == mine:
            continue
        try:
            record = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        if _alive(record) is not None:
            return True
        path.unlink(missing_ok=True)
    return False
