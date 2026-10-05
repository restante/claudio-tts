"""End to end through the real CLI and detached worker, with the sound card faked out."""

import subprocess
import sys
import time

import pytest

from claudio_tts import procs


def _run(*args, env=None, **kw):
    return subprocess.run(
        [sys.executable, "-m", "claudio_tts", *args], capture_output=True, text=True, env=env, **kw
    )


def _wait(predicate, seconds=10.0):
    end = time.time() + seconds
    while time.time() < end:
        if predicate():
            return True
        time.sleep(0.05)
    return False


def _env(isolated_home, seconds="0"):
    import os

    env = dict(os.environ)
    env["CLAUDIO_TTS_FAKE_SECONDS"] = seconds
    return env


def test_speak_cleans_markdown_and_returns_immediately(isolated_home):
    log = isolated_home / "played.log"
    started = time.time()
    done = _run(
        "speak", "--session", "s1", "--volume", "4", "--speed", "0.8",
        input="**Hello** `code` world", env=_env(isolated_home),
    )  # fmt: skip
    assert done.returncode == 0, done.stderr
    assert time.time() - started < 5
    assert _wait(lambda: log.exists() and log.read_text().strip())
    pid, volume, speed, devices_spec, text = log.read_text().strip().split("\t")
    assert (volume, speed, text) == ("4", "0.8", "Hello world")


def test_a_new_reply_replaces_the_same_sessions_older_one(isolated_home):
    log = isolated_home / "played.log"
    env = _env(isolated_home, seconds="30")
    _run("speak", "--session", "s1", "--text", "first reply", env=env)
    assert _wait(lambda: log.exists() and "first reply" in log.read_text())
    first_worker = procs._file("s1")
    assert first_worker.exists()
    _run("speak", "--session", "s1", "--text", "second reply", env=env)
    assert _wait(lambda: "second reply" in log.read_text())
    _run("stop", "--session", "s1", env=env)


def test_stop_only_stops_its_own_session(isolated_home):
    log = isolated_home / "played.log"
    env = _env(isolated_home, seconds="30")
    _run("speak", "--session", "A", "--text", "from A", env=env)
    assert _wait(lambda: log.exists() and "from A" in log.read_text())
    _run("speak", "--session", "B", "--text", "from B", env=env)
    time.sleep(0.5)
    _run("stop", "--session", "B", env=env)
    import json

    record = json.loads(procs._file("A").read_text())
    assert procs._alive(record) is not None, "stopping B must not touch A"
    _run("stop", "--session", "A", env=env)


def test_sessions_take_turns(isolated_home):
    log = isolated_home / "played.log"
    env = _env(isolated_home, seconds="1.5")
    _run("speak", "--session", "A", "--text", "alpha", env=env)
    assert _wait(lambda: log.exists() and "alpha" in log.read_text())
    _run("speak", "--session", "B", "--text", "bravo", env=env)
    time.sleep(0.5)
    assert "bravo" not in log.read_text(), "B must wait while A holds the speaker"
    assert _wait(lambda: "bravo" in log.read_text(), seconds=10)


@pytest.mark.skipif(sys.platform == "win32", reason="posix pid semantics")
def test_stop_when_nothing_is_running_is_quiet(isolated_home):
    assert _run("stop", "--session", "nobody", env=_env(isolated_home)).returncode == 0
