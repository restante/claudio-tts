"""Extra audio outputs supplied by add-on packages (claudio-vibecode's phone, for example).

An add-on registers a factory under the `claudio_tts.sinks` entry-point group. The entry-point
name is the output's name (what a person puts in `/tts device`). The factory is called once per
utterance as `factory(session)` and returns a sink, or None when it has nothing to play on:

    sink.local   bool: keep the computer's own speakers playing too
    sink.put(samples, rate)   one sentence of mono float32 audio, full level
    sink.close()              the utterance is over
"""

from __future__ import annotations

from collections.abc import Callable
from importlib.metadata import entry_points

GROUP = "claudio_tts.sinks"


def factories() -> dict[str, Callable]:
    found: dict[str, Callable] = {}
    for entry in entry_points(group=GROUP):
        try:
            found[entry.name] = entry.load()
        except Exception:  # a broken add-on must never silence speech
            continue
    return found


def open_all(session: str) -> list:
    opened = []
    for name, factory in factories().items():
        try:
            sink = factory(session)
        except Exception:
            sink = None
        if sink is not None:
            sink.name = getattr(sink, "name", name)
            opened.append(sink)
    return opened


def describe() -> list[str]:
    """One `name (description)` line per installed add-on output, for `claudio-tts devices`."""
    return [
        f"{name} ({getattr(factory, 'description', 'extra output')})"
        for name, factory in factories().items()
    ]
