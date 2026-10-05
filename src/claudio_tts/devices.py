"""Audio device listing and matching."""

from __future__ import annotations

from collections.abc import Sequence

VIRTUAL = ("teams", "zoom", "aggregate", "multi-output", "blackhole", "loopback", "virtual")

Device = tuple[int, str]  # (index, name)


def _query(kind: str) -> list[Device]:
    import sounddevice as sd

    channels = "max_output_channels" if kind == "output" else "max_input_channels"
    return [(i, d["name"]) for i, d in enumerate(sd.query_devices()) if d[channels] > 0]


def outputs() -> list[Device]:
    return _query("output")


def inputs() -> list[Device]:
    return _query("input")


def default_index(kind: str) -> int | None:
    import sounddevice as sd

    value = sd.default.device[1 if kind == "output" else 0]
    return value if isinstance(value, int) and value >= 0 else None


def normalise(spec: str | None) -> str:
    """Lower-case, drop the "(default)" label that listings add, trim."""
    return (spec or "default").lower().replace("(default)", "").strip()


def pick(spec: str | None, devices: Sequence[Device]) -> list[int | None]:
    """Device indexes for `spec` ("airpods,speakers", "all" or "default").

    `[None]` means the default output.

    Unmatched names are ignored; if nothing matches, fall back to the default output so speech is
    never lost because a device was unplugged.
    """
    spec = normalise(spec)
    if spec in ("", "default"):
        return [None]
    if spec == "all":
        chosen = [i for i, name in devices if not any(v in name.lower() for v in VIRTUAL)]
    else:
        chosen = []
        for part in (p.strip() for p in spec.split(",")):
            for i, name in devices:
                if part and part in name.lower() and i not in chosen:
                    chosen.append(i)
    return chosen or [None]
