"""Turn a text file into an audiobook: one WAV per chapter, optionally packed into m4b or mp3.

A batch job, unlike live speech: no playback, no ducking, no speak lock. Finished chapters are
kept, so an interrupted run picks up where it stopped.
"""

from __future__ import annotations

import asyncio
import os
import re
import shutil
import subprocess
import sys
import time
import wave
from dataclasses import dataclass
from pathlib import Path

from claudio_tts import markdown, model, voices
from claudio_tts.player import MAX_SPEED, MIN_SPEED

CHUNK_CHARS = 3000  # fallback chapter size when the text has no headings
CHARS_PER_SECOND = 15  # rough speaking rate at speed 1.0, for estimates and the fake synthesiser
SAMPLE_RATE = 24000
MARKDOWN_SUFFIXES = {".md", ".markdown"}
FORMATS = ("wav", "mp3", "m4b")

_HEADING = re.compile(
    r"^(?:#{1,3}\s+(?P<md>\S.*?)\s*#*|(?P<word>(?:chapter|capitolo|kapitel|chapitre|cap[ií]tulo)"
    r"\s+[\w.]+\b.*?))\s*$",
    re.IGNORECASE,
)


class AudiobookError(Exception):
    """A problem the person can fix (bad file, missing model); the message says how."""


@dataclass
class Chapter:
    title: str
    text: str

    @property
    def seconds(self) -> float:
        return len(self.text) / CHARS_PER_SECOND


def split_chapters(text: str) -> list[Chapter]:
    """Split on markdown headings or "Chapter N" lines; without any, on paragraph-bounded chunks."""
    text = text.replace("\r\n", "\n").strip()
    chapters: list[Chapter] = []
    title, body = "Introduction", []

    def flush() -> None:
        joined = "\n".join(body).strip()
        if joined:
            chapters.append(Chapter(title, joined))

    found = False
    in_fence = False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        match = None if in_fence else _HEADING.match(line.strip())
        if match:
            found = True
            flush()
            title, body = (match.group("md") or match.group("word")).strip(), []
        else:
            body.append(line)
    flush()
    if found:
        return chapters
    return _chunks(text)


def _chunks(text: str) -> list[Chapter]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) > CHUNK_CHARS:
            chunks.append(current)
            current = ""
        current = f"{current}\n\n{paragraph}" if current else paragraph
    if current:
        chunks.append(current)
    return [Chapter(f"Part {i}", c) for i, c in enumerate(chunks, 1)]


def spoken(chapter: Chapter, is_markdown: bool, *, announce: bool = True) -> str:
    body = markdown.clean(chapter.text) if is_markdown else chapter.text
    if (
        announce
        and chapter.title not in ("Introduction",)
        and not chapter.title.startswith("Part ")
    ):
        return f"{chapter.title}.\n\n{body}"
    return body


def slug(title: str) -> str:
    cleaned = re.sub(r"[^\w]+", "-", title, flags=re.UNICODE).strip("-").lower()
    return cleaned[:40].strip("-") or "part"


def chapter_path(outdir: Path, index: int, chapter: Chapter) -> Path:
    return outdir / f"{index:02d}-{slug(chapter.title)}.wav"


def _synthesise(text: str, voice: str, speed: float, lang: str):
    """Return (float32 samples, rate). `CLAUDIO_TTS_FAKE_PLAYER` set: silence, no model needed."""
    import numpy as np

    if os.environ.get("CLAUDIO_TTS_FAKE_PLAYER"):
        seconds = max(0.1, len(text) / CHARS_PER_SECOND / speed)
        return np.zeros(int(seconds * SAMPLE_RATE), dtype="float32"), SAMPLE_RATE

    from kokoro_onnx import Kokoro

    found = model.find()
    if found is None:
        raise AudiobookError("Kokoro model not installed; run `claudio-tts download-model`")
    kokoro = Kokoro(str(found[0]), str(found[1]))

    async def collect():
        parts, rates = [], []
        async for samples, sample_rate in kokoro.create_stream(
            text, voice=voices.resolve(voice), speed=speed, lang=lang
        ):
            parts.append(samples)
            rates.append(sample_rate)
        return parts, (rates[-1] if rates else SAMPLE_RATE)

    parts, rate = asyncio.run(collect())
    if not parts:
        raise AudiobookError("Kokoro produced no audio for this chapter")
    return np.concatenate(parts).astype("float32"), rate


def write_wav(path: Path, samples, rate: int) -> None:
    """Write 16-bit mono WAV through a .part file, so a half-written chapter is never mistaken
    for a finished one."""
    import numpy as np

    pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype("<i2")
    part = path.with_name(path.name + ".part")
    with wave.open(str(part), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(pcm.tobytes())
    os.replace(part, path)


def wav_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as src:
        return src.getnframes() / src.getframerate()


def ffmetadata(titles: list[str], durations: list[float]) -> str:
    """ffmpeg chapter metadata, so m4b players show a chapter list."""
    lines = [";FFMETADATA1"]
    start = 0
    for title, seconds in zip(titles, durations, strict=True):
        end = start + int(seconds * 1000)
        safe = re.sub(r"([=;#\\])", r"\\\1", title)
        lines += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={start}", f"END={end}", f"title={safe}"]
        start = end
    return "\n".join(lines) + "\n"


def package(outdir: Path, stem: str, fmt: str, files: list[Path], titles: list[str]) -> Path | None:
    """Join the chapter WAVs into one m4b/mp3 with ffmpeg. None (and a hint) if ffmpeg is absent."""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        print(
            f"claudio-tts: ffmpeg not found, so no .{fmt}; the chapter WAV files are ready."
            " Install ffmpeg (macOS: brew install ffmpeg) and run again to pack them.",
            file=sys.stderr,
        )
        return None
    listing = outdir / ".concat.txt"
    meta = outdir / ".chapters.ffmeta"
    target = outdir / f"{stem}.{fmt}"
    listing.write_text(
        "".join("file '{}'\n".format(f.name.replace("'", "'\\''")) for f in files), encoding="utf-8"
    )
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing)]
    if fmt == "m4b":
        meta.write_text(ffmetadata(titles, [wav_seconds(f) for f in files]), encoding="utf-8")
        cmd += ["-i", str(meta), "-map_metadata", "1", "-c:a", "aac", "-b:a", "64k"]
    else:
        cmd += ["-c:a", "libmp3lame", "-q:a", "4"]
    cmd.append(str(target))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as error:
        raise AudiobookError(
            f"ffmpeg failed (exit {error.returncode}); the WAV files are kept"
        ) from error
    finally:
        listing.unlink(missing_ok=True)
        meta.unlink(missing_ok=True)
    return target


def build(
    source: Path,
    outdir: Path | None = None,
    *,
    fmt: str = "wav",
    voice: str,
    speed: float = 1.0,
    lang: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> Path | None:
    if fmt not in FORMATS:
        raise AudiobookError(f"unknown format {fmt!r}; choose from {', '.join(FORMATS)}")
    try:
        text = source.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise AudiobookError(f"file not found: {source}") from error
    except (UnicodeDecodeError, OSError) as error:
        raise AudiobookError(f"cannot read {source} as UTF-8 text: {error}") from error
    chapters = split_chapters(text)
    if not chapters:
        raise AudiobookError(f"{source} has no text to read")

    is_md = source.suffix.lower() in MARKDOWN_SUFFIXES
    speed = max(MIN_SPEED, min(MAX_SPEED, speed))
    outdir = outdir or source.with_name(f"{source.stem}-audiobook")
    plan = [spoken(c, is_md) for c in chapters]

    if dry_run:
        total = 0.0
        for i, (chapter, said) in enumerate(zip(chapters, plan, strict=True), 1):
            seconds = len(said) / CHARS_PER_SECOND / speed
            total += seconds
            print(f"{i:>3}  {chapter_path(outdir, i, chapter).name:<46} ~{seconds / 60:5.1f} min")
        print(f"{len(chapters)} chapters, about {total / 3600:.1f} h of audio")
        return None

    outdir.mkdir(parents=True, exist_ok=True)
    lang = lang or voices.language(voice)
    files: list[Path] = []
    started = time.time()
    for i, (chapter, said) in enumerate(zip(chapters, plan, strict=True), 1):
        path = chapter_path(outdir, i, chapter)
        files.append(path)
        label = f"[{i}/{len(chapters)}] {chapter.title}"
        if path.exists() and not force:
            print(f"{label}: already done, skipping", file=sys.stderr)
            continue
        samples, rate = _synthesise(said, voice, speed, lang)
        write_wav(path, samples, rate)
        print(f"{label}: done ({time.time() - started:.0f}s elapsed)", file=sys.stderr)

    if fmt != "wav":
        packed = package(outdir, source.stem, fmt, files, [c.title for c in chapters])
        if packed is not None:
            return packed
    return outdir
