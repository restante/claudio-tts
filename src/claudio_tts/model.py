"""Fetch and verify the Kokoro model files."""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from claudio_tts.paths import model_dir

RELEASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"


@dataclass(frozen=True)
class ModelFile:
    name: str
    sha256: str
    size: int

    @property
    def url(self) -> str:
        return f"{RELEASE}/{self.name}"


FULL = ModelFile(
    "kokoro-v1.0.onnx",
    "7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5",
    325_532_387,
)
LITE = ModelFile(
    "kokoro-v1.0.int8.onnx",
    "6e742170d309016e5891a994e1ce1559c702a2ccd0075e67ef7157974f6406cb",
    92_361_271,
)
VOICES = ModelFile(
    "voices-v1.0.bin",
    "bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d",
    28_214_398,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verified(path: Path, spec: ModelFile) -> bool:
    return path.is_file() and path.stat().st_size == spec.size and sha256(path) == spec.sha256


def override() -> tuple[Path, Path] | None:
    """A model and voices file chosen with CLAUDIO_TTS_MODEL and CLAUDIO_TTS_VOICES (both required).

    This is how to use any other Kokoro-compatible model or voices pack. Not checksum-verified:
    you picked the files, so you vouch for them.
    """
    model_path, voices_path = (
        os.environ.get("CLAUDIO_TTS_MODEL"),
        os.environ.get("CLAUDIO_TTS_VOICES"),
    )
    if model_path and voices_path:
        pair = (Path(model_path).expanduser(), Path(voices_path).expanduser())
        if pair[0].is_file() and pair[1].is_file():
            return pair
    return None


def find() -> tuple[Path, Path] | None:
    """(model, voices) to use: an override if set, else a verified pair (full model beats lite)."""
    chosen = override()
    if chosen is not None:
        return chosen
    voices = model_dir() / VOICES.name
    if not verified(voices, VOICES):
        return None
    for spec in (FULL, LITE):
        candidate = model_dir() / spec.name
        if verified(candidate, spec):
            return candidate, voices
    return None


def _download(spec: ModelFile, target: Path) -> None:
    part = target.with_suffix(target.suffix + ".part")
    with urllib.request.urlopen(spec.url, timeout=60) as response, part.open("wb") as out:
        total = int(response.headers.get("Content-Length") or spec.size)
        done, last = 0, -1
        while block := response.read(1 << 20):
            out.write(block)
            done += len(block)
            percent = done * 100 // total
            if percent // 5 != last // 5:
                last = percent
                print(f"  {spec.name}: {percent}%", file=sys.stderr, flush=True)
    part.replace(target)


def ensure(lite: bool = False, source: Path | None = None) -> tuple[Path, Path]:
    """Make sure the model and voices are present and verified.

    Reuses verified files from `source` instead of downloading when given.
    """
    model_dir().mkdir(parents=True, exist_ok=True)
    for spec in (LITE if lite else FULL, VOICES):
        target = model_dir() / spec.name
        if verified(target, spec):
            continue
        local = source / spec.name if source else None
        if local and verified(local, spec):
            shutil.copyfile(local, target)
            continue
        print(f"Downloading {spec.name} ({spec.size // 1_000_000} MB)...", file=sys.stderr)
        _download(spec, target)
        if not verified(target, spec):
            target.unlink(missing_ok=True)
            raise RuntimeError(f"{spec.name} failed its checksum; try again or report an issue")
    found = find()
    if found is None:
        raise RuntimeError("model files are missing after download")
    return found
