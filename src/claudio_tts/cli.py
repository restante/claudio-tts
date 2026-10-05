"""The `claudio-tts` command line. The Claude mod is a thin shim over `speak` and `stop`."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

from claudio_tts import (
    __version__,
    devices,
    duck,
    install_mod,
    markdown,
    model,
    paths,
    player,
    procs,
)
from claudio_tts.locks import SpeakLock

DEFAULT_VOICE = "af_sky"


def _spawn_worker(args: list[str]) -> subprocess.Popen:
    """Start a detached `_worker` that outlives this process (and the hook that called it)."""
    log = open(paths.state_dir() / "worker.log", "ab")  # noqa: SIM115 - handed to the child
    kwargs: dict = {"stdin": subprocess.DEVNULL, "stdout": log, "stderr": log}
    if sys.platform == "win32":
        kwargs["creationflags"] = (
            subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NEW_PROCESS_GROUP
            | subprocess.CREATE_NO_WINDOW
        )
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen([sys.executable, "-m", "claudio_tts", "_worker", *args], **kwargs)


def cmd_speak(a: argparse.Namespace) -> int:
    text = markdown.clean(sys.stdin.read() if a.text is None else a.text)
    stopped = procs.stop(a.session)  # a new reply replaces this session's older one
    if stopped:
        time.sleep(0.2)
    if not text:
        return 0
    texts = paths.state_dir() / "texts"
    texts.mkdir(exist_ok=True)
    path = texts / f"{uuid.uuid4().hex}.txt"
    path.write_text(text, encoding="utf-8")
    worker = _spawn_worker(
        [
            "--session", a.session, "--text-file", str(path), "--volume", str(a.volume),
            "--speed", str(a.speed), "--devices", a.devices, "--voice", a.voice,
        ]
    )  # fmt: skip
    procs.register(a.session, worker.pid)
    return 0


def cmd_worker(a: argparse.Namespace) -> int:
    text_file = Path(a.text_file)
    try:
        text = text_file.read_text(encoding="utf-8")
    finally:
        text_file.unlink(missing_ok=True)
    duck.duck()
    try:
        with SpeakLock(paths.state_dir() / "speak.lock"):  # one speaker at a time, all sessions
            player.speak(text, voice=a.voice, volume=a.volume, speed=a.speed, device_spec=a.devices)
    finally:
        procs.clear(a.session)
        if not procs.others_speaking(a.session):
            duck.restore()
    return 0


def cmd_stop(a: argparse.Namespace) -> int:
    procs.stop(a.session)
    if not procs.others_speaking(a.session):
        duck.restore()
    return 0


def cmd_say(a: argparse.Namespace) -> int:
    player.speak(
        markdown.clean(a.text), voice=a.voice, volume=a.volume, speed=a.speed, device_spec=a.devices
    )
    return 0


def cmd_devices(a: argparse.Namespace) -> int:
    kind = "input" if a.inputs else "output"
    default = devices.default_index(kind)
    for index, name in devices.inputs() if a.inputs else devices.outputs():
        print(f"{name}{' (default)' if index == default else ''}")
    return 0


def cmd_download_model(a: argparse.Namespace) -> int:
    model.ensure(lite=a.lite, source=Path(a.source) if a.source else None)
    print("Model ready:", paths.model_dir())
    return 0


def cmd_install_mod(a: argparse.Namespace) -> int:
    try:
        result = install_mod.install(
            python=a.python or sys.executable,
            claude_dir=Path(a.claude_dir) if a.claude_dir else None,
            link=a.link,
        )
    except install_mod.SettingsError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Mod installed at {result['mod']}" + (" (linked)" if result["linked"] else ""))
    print(
        f"Registered in {result['settings']}"
        + ("" if result["changed"] else " (already up to date)")
    )
    return 0


def cmd_uninstall_mod(a: argparse.Namespace) -> int:
    try:
        result = install_mod.uninstall(Path(a.claude_dir) if a.claude_dir else None)
    except install_mod.SettingsError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Removed {result['mod']} and its settings entries")
    return 0


def cmd_doctor(a: argparse.Namespace) -> int:
    failed = False

    def check(ok: bool, label: str, hint: str = "", critical: bool = True) -> None:
        nonlocal failed
        print(
            f"  {'ok  ' if ok else 'FAIL' if critical else 'warn'}  {label}"
            + ("" if ok else f"  -> {hint}")
        )
        failed = failed or (not ok and critical)

    print(f"claudio-tts {__version__} on {sys.platform}, Python {sys.version.split()[0]}")
    check(model.find() is not None, "Kokoro model installed and verified",
          "run: claudio-tts download-model")  # fmt: skip
    try:
        outputs = devices.outputs()
        check(
            bool(outputs), f"{len(outputs)} audio output device(s) found", "no sound card detected"
        )
    except Exception as error:  # PortAudio missing or broken
        check(False, "audio backend loads", str(error))
    try:
        import espeakng_loader  # noqa: F401

        check(True, "speech phonemizer (espeak-ng) bundled")
    except ImportError as error:
        check(False, "speech phonemizer (espeak-ng) bundled", str(error))
    check(shutil.which("claude") is not None, "Claude Code (`claude`) found on PATH",
          "install Claude Code first: https://claude.com/claude-code", critical=False)  # fmt: skip
    mod = paths.claude_dir() / "mods" / install_mod.MOD_NAME
    check(mod.exists(), f"mod installed at {mod}", "run: claudio-tts install-mod", critical=False)
    if a.speak and not failed:
        print("  speaking a test phrase...")
        player.speak(
            "Claudio T T S is working.", voice=DEFAULT_VOICE, volume=7, speed=1.0, device_spec=None
        )
    print("All good." if not failed else "Some checks failed.")
    return 1 if failed else 0


def _add_voice_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--volume", type=int, default=10, choices=range(1, 11), metavar="1-10")
    p.add_argument("--speed", type=float, default=1.0)
    p.add_argument("--devices", default="default", help='"airpods,speakers", "all" or "default"')
    p.add_argument("--voice", default=os.environ.get("KOKORO_VOICE", DEFAULT_VOICE))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claudio-tts", description="Spoken replies for Claude Code."
    )
    parser.add_argument("--version", action="version", version=f"claudio-tts {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("speak", help="speak text from stdin as this session (returns at once)")
    p.add_argument("--session", required=True)
    p.add_argument("--text", help="speak this instead of reading stdin")
    _add_voice_args(p)
    p.set_defaults(func=cmd_speak)

    p = sub.add_parser("_worker")
    p.add_argument("--session", required=True)
    p.add_argument("--text-file", required=True)
    _add_voice_args(p)
    p.set_defaults(func=cmd_worker)

    p = sub.add_parser("stop", help="stop this session's speech")
    p.add_argument("--session", required=True)
    p.set_defaults(func=cmd_stop)

    p = sub.add_parser("say", help="speak text now and wait (for testing)")
    p.add_argument("text")
    _add_voice_args(p)
    p.set_defaults(func=cmd_say)

    p = sub.add_parser("devices", help="list audio devices")
    p.add_argument("--inputs", action="store_true")
    p.set_defaults(func=cmd_devices)

    p = sub.add_parser("download-model", help="download and verify the Kokoro model")
    p.add_argument(
        "--lite", action="store_true", help="smaller int8 model (92 MB instead of 326 MB)"
    )
    p.add_argument("--source", help="reuse verified model files from this folder")
    p.set_defaults(func=cmd_download_model)

    p = sub.add_parser("install-mod", help="install the Claude mod and register it")
    p.add_argument("--python", help="interpreter the mod should call (default: this one)")
    p.add_argument("--claude-dir", help="Claude config dir (default: ~/.claude)")
    p.add_argument("--link", action="store_true", help="symlink instead of copy (for development)")
    p.set_defaults(func=cmd_install_mod)

    p = sub.add_parser("uninstall-mod", help="remove the Claude mod and its settings entries")
    p.add_argument("--claude-dir")
    p.set_defaults(func=cmd_uninstall_mod)

    p = sub.add_parser("doctor", help="check the installation")
    p.add_argument("--speak", action="store_true", help="also speak a test phrase")
    p.set_defaults(func=cmd_doctor)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)
