import threading
import time

from claudio_tts.locks import SpeakLock


def test_second_holder_waits_for_the_first(tmp_path):
    path = tmp_path / "speak.lock"
    events: list[str] = []

    def second():
        with SpeakLock(path, poll=0.01):
            events.append("second")

    with SpeakLock(path, poll=0.01):
        thread = threading.Thread(target=second)
        thread.start()
        time.sleep(0.15)
        events.append("first-done")
    thread.join(timeout=3)
    assert events == ["first-done", "second"]


def test_lock_is_reusable(tmp_path):
    path = tmp_path / "speak.lock"
    for _ in range(3):
        with SpeakLock(path):
            pass
