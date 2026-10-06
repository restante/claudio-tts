import json
from importlib.metadata import EntryPoint

from claudio_tts import install_mod, player, sessionstate, sinks


class FakeSink:
    def __init__(self, local=True):
        self.local = local
        self.got = []
        self.closed = False

    def put(self, samples, rate):
        self.got.append((len(samples), rate))

    def close(self):
        self.closed = True


def _register(monkeypatch, name, factory):
    monkeypatch.setattr(sinks, "factories", lambda: {name: factory})


def _run(monkeypatch, spec, **extra):
    seen = {}

    async def fake_stream(text, voice, gain, outputs, speed, lang, add_ons=None):
        seen.update(outputs=outputs, add_ons=add_ons)

    monkeypatch.delenv("CLAUDIO_TTS_FAKE_PLAYER", raising=False)
    monkeypatch.setattr(player, "_stream", fake_stream)
    monkeypatch.setattr(player.devices, "outputs", lambda: [(3, "Speakers")])
    player.speak("hi", voice="af_sky", volume=5, speed=1, device_spec=spec, **extra)
    return seen


def test_add_on_output_follows_the_device_setting(monkeypatch):
    sink = FakeSink()
    _register(monkeypatch, "phone", lambda session: sink)
    assert _run(monkeypatch, "phone")["outputs"] == []  # asked for the add-on only
    assert _run(monkeypatch, "phone,speakers")["outputs"] == [3]  # both
    assert _run(monkeypatch, "speakers")["outputs"] == [3]  # a listening add-on still gets it
    assert _run(monkeypatch, "speakers")["add_ons"] == [sink]
    sink.local = False  # the add-on says the computer's speakers should be quiet
    assert _run(monkeypatch, "speakers")["outputs"] == []


def test_without_a_listener_speech_is_never_lost(monkeypatch):
    _register(monkeypatch, "phone", lambda session: None)
    assert _run(monkeypatch, "phone")["outputs"] == [None]  # fall back to the default output
    assert _run(monkeypatch, "speakers")["outputs"] == [3]
    assert _run(monkeypatch, "speakers")["add_ons"] == []


def test_a_broken_add_on_cannot_silence_speech(monkeypatch):
    def boom(session):
        raise RuntimeError("add-on bug")

    _register(monkeypatch, "phone", boom)
    assert sinks.open_all("s") == []
    assert _run(monkeypatch, "default")["outputs"] == [None]


def test_devices_lists_add_on_outputs(monkeypatch):
    def factory(session):
        return None

    factory.description = "your phone"
    _register(monkeypatch, "phone", factory)
    assert sinks.describe() == ["phone (your phone)"]


def test_entry_points_are_discovered(monkeypatch):
    entry = EntryPoint(name="phone", value="claudio_tts.sinks:describe", group=sinks.GROUP)
    monkeypatch.setattr(sinks, "entry_points", lambda group: [entry])
    assert list(sinks.factories()) == ["phone"]


def test_session_state_round_trip():
    assert sessionstate.read("s/1") == {}
    sessionstate.write("s/1", muted=True)
    sessionstate.write("s/1", other=1)
    assert sessionstate.read("s/1") == {"muted": True, "other": 1}
    sessionstate.clear("s/1")
    assert sessionstate.read("s/1") == {}


def test_install_mod_can_install_an_add_on_mod(tmp_path):
    src = tmp_path / "addon"
    (src / "hooks").mkdir(parents=True)
    (src / "hooks" / "hooks.json").write_text("{}")
    claude = tmp_path / "claude"
    install_mod.install("/py", claude_dir=claude, source=src, name="addon", python_var="ADDON_PY")
    settings = json.loads((claude / "settings.json").read_text())
    assert settings["env"]["ADDON_PY"] == "/py"
    assert settings["env"]["CLAUDE_CODE_PLUGIN_DIRS"] == str(claude / "mods" / "addon")
    install_mod.install("/py", claude_dir=claude, source=src)  # the tts mod beside it
    dirs = json.loads((claude / "settings.json").read_text())["env"]["CLAUDE_CODE_PLUGIN_DIRS"]
    assert str(claude / "mods" / "addon") in dirs and str(claude / "mods" / "claudio-tts") in dirs
    install_mod.uninstall(claude_dir=claude, name="addon", python_var="ADDON_PY")
    env = json.loads((claude / "settings.json").read_text())["env"]
    assert (
        "ADDON_PY" not in env
        and str(claude / "mods" / "addon") not in env["CLAUDE_CODE_PLUGIN_DIRS"]
    )
