"""One speaker at a time across every session: a cross-platform exclusive file lock."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    import msvcrt

    def _try_lock(fd: int) -> bool:
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            return True
        except OSError:
            return False

    def _unlock(fd: int) -> None:
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)

else:
    import fcntl

    def _try_lock(fd: int) -> bool:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError:
            return False

    def _unlock(fd: int) -> None:
        fcntl.flock(fd, fcntl.LOCK_UN)


class SpeakLock:
    """Blocks in `__enter__` until no other process holds the lock. The OS frees it if we die."""

    def __init__(self, path: Path, poll: float = 0.1) -> None:
        self.path = path
        self.poll = poll
        self._fd: int | None = None

    def __enter__(self) -> SpeakLock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fd = os.open(self.path, os.O_RDWR | os.O_CREAT)
        if os.fstat(self._fd).st_size == 0:
            os.write(self._fd, b"x")  # msvcrt needs a byte to lock
        while not _try_lock(self._fd):
            time.sleep(self.poll)
        return self

    def __exit__(self, *_exc: object) -> None:
        if self._fd is not None:
            try:
                _unlock(self._fd)
            finally:
                os.close(self._fd)
                self._fd = None
