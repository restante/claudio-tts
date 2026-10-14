import wave

import pytest

from claudio_tts import audiobook, cli

BOOK = "Intro words here.\n\n# One\nFirst chapter text.\n\n# Two\nSecond chapter text.\n"


def book(tmp_path, text=BOOK, name="book.md"):
    f = tmp_path / name
    f.write_text(text, encoding="utf-8")
    return f


def test_split_on_markdown_headings():
    chapters = audiobook.split_chapters(BOOK)
    assert [c.title for c in chapters] == ["Introduction", "One", "Two"]
    assert chapters[1].text == "First chapter text."


def test_split_on_chapter_lines():
    chapters = audiobook.split_chapters("Chapter 1\nHello.\nChapter 2\nBye.")
    assert [c.title for c in chapters] == ["Chapter 1", "Chapter 2"]


def test_heading_inside_code_fence_is_not_a_chapter():
    text = "# Real\nbody\n```\n# not a chapter\n```\nmore"
    assert [c.title for c in audiobook.split_chapters(text)] == ["Real"]


def test_no_headings_falls_back_to_paragraph_chunks():
    paragraph = "word " * 400  # ~2000 chars
    chapters = audiobook.split_chapters("\n\n".join([paragraph] * 4))
    assert len(chapters) == 4 or len(chapters) == 2
    assert all(c.title.startswith("Part ") for c in chapters)
    assert all(len(c.text) <= audiobook.CHUNK_CHARS + len(paragraph) for c in chapters)


def test_build_writes_one_wav_per_chapter(tmp_path):
    out = tmp_path / "out"
    result = audiobook.build(book(tmp_path), out, voice="af_sky")
    assert result == out
    names = sorted(p.name for p in out.glob("*.wav"))
    assert names == ["01-introduction.wav", "02-one.wav", "03-two.wav"]
    with wave.open(str(out / "02-one.wav")) as w:
        assert w.getnchannels() == 1 and w.getframerate() == audiobook.SAMPLE_RATE
    assert not list(out.glob("*.part"))


def test_resume_skips_finished_chapters_and_force_redoes(tmp_path, capsys):
    out = tmp_path / "out"
    src = book(tmp_path)
    audiobook.build(src, out, voice="af_sky")
    first = out / "02-one.wav"
    first.write_bytes(first.read_bytes())  # untouched marker below
    mtime = first.stat().st_mtime_ns
    capsys.readouterr()
    audiobook.build(src, out, voice="af_sky")
    assert "already done" in capsys.readouterr().err
    assert first.stat().st_mtime_ns == mtime
    audiobook.build(src, out, voice="af_sky", force=True)
    assert first.stat().st_mtime_ns != mtime


def test_dry_run_writes_nothing(tmp_path, capsys):
    out = tmp_path / "out"
    assert audiobook.build(book(tmp_path), out, voice="af_sky", dry_run=True) is None
    assert not out.exists()
    assert "3 chapters" in capsys.readouterr().out


def test_empty_and_missing_files_are_clear_errors(tmp_path):
    with pytest.raises(audiobook.AudiobookError, match="no text"):
        audiobook.build(book(tmp_path, "  \n"), voice="af_sky")
    with pytest.raises(audiobook.AudiobookError, match="not found"):
        audiobook.build(tmp_path / "nope.txt", voice="af_sky")


def test_m4b_without_ffmpeg_keeps_wavs_and_says_so(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(audiobook.shutil, "which", lambda name: None)
    out = tmp_path / "out"
    result = audiobook.build(book(tmp_path), out, fmt="m4b", voice="af_sky")
    assert result == out and len(list(out.glob("*.wav"))) == 3
    assert "ffmpeg not found" in capsys.readouterr().err


def test_ffmetadata_has_chapter_marks():
    meta = audiobook.ffmetadata(["A", "B=1"], [1.5, 2.0])
    assert "START=0\nEND=1500\ntitle=A" in meta
    assert "START=1500\nEND=3500\ntitle=B\\=1" in meta


def test_cli_reports_error_and_exit_code(tmp_path, capsys):
    assert cli.main(["audiobook", str(tmp_path / "missing.txt")]) == 1
    assert "file not found" in capsys.readouterr().err


def test_cli_prints_output_folder(tmp_path, capsys):
    out = tmp_path / "o"
    assert cli.main(["audiobook", str(book(tmp_path)), "-o", str(out)]) == 0
    assert capsys.readouterr().out.strip() == str(out)
