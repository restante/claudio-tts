import hashlib

from claudio_tts import model


def _spec(path, data: bytes, name="m.bin"):
    path.write_bytes(data)
    return model.ModelFile(name, hashlib.sha256(data).hexdigest(), len(data))


def test_verified_accepts_matching_file_only(tmp_path):
    spec = _spec(tmp_path / "m.bin", b"hello")
    assert model.verified(tmp_path / "m.bin", spec)
    (tmp_path / "m.bin").write_bytes(b"hellO")
    assert not model.verified(tmp_path / "m.bin", spec)
    assert not model.verified(tmp_path / "missing.bin", spec)


def test_ensure_reuses_verified_files_from_a_source_folder(tmp_path, monkeypatch):
    source = tmp_path / "src"
    source.mkdir()
    full = _spec(source / "full.onnx", b"model-bytes", "full.onnx")
    voices = _spec(source / "voices.bin", b"voice-bytes", "voices.bin")
    monkeypatch.setattr(model, "FULL", full)
    monkeypatch.setattr(model, "VOICES", voices)
    monkeypatch.setattr(
        model, "_download", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no download"))
    )
    found = model.ensure(source=source)
    assert found is not None and found[0].read_bytes() == b"model-bytes"
    assert model.find() == found


def test_find_is_none_when_nothing_installed():
    assert model.find() is None
