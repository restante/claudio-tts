"""Stream Kokoro speech, sentence by sentence, to one, several or all output devices at once."""

from __future__ import annotations

import asyncio
import os
import queue
import sys
import threading
import time

from claudio_tts import devices, model, voices

MIN_SPEED, MAX_SPEED = 0.5, 1.5


class _Sink:
    """One output device fed from its own thread so a slow device never stalls the others."""

    def __init__(self, device: int | None, rate: int) -> None:
        import sounddevice as sd

        self.q: queue.Queue = queue.Queue()
        self.stream = None
        try:
            self.stream = sd.OutputStream(
                device=device, samplerate=rate, channels=1, dtype="float32"
            )
            self.stream.start()
        except Exception as error:  # device vanished or refuses the format
            print(f"claudio-tts: output {device} unavailable: {error}", file=sys.stderr)
            return
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self) -> None:
        while (block := self.q.get()) is not None:
            try:
                self.stream.write(block)
            except Exception:
                break

    def put(self, block) -> None:
        if self.stream is not None:
            self.q.put(block)

    def close(self) -> None:
        if self.stream is None:
            return
        self.q.put(None)
        self.thread.join()
        self.stream.stop()
        self.stream.close()


async def _stream(
    text: str, voice: str, gain: float, outputs: list[int | None], speed: float, lang: str
) -> None:
    from kokoro_onnx import Kokoro

    found = model.find()
    if found is None:
        raise RuntimeError("Kokoro model not installed; run `claudio-tts download-model`")
    kokoro = Kokoro(str(found[0]), str(found[1]))
    sinks: list[_Sink] | None = None
    async for samples, rate in kokoro.create_stream(
        text, voice=voices.resolve(voice), speed=speed, lang=lang
    ):
        if sinks is None:
            sinks = [_Sink(d, rate) for d in outputs]
        block = (samples * gain).astype("float32").reshape(-1, 1)
        for sink in sinks:
            sink.put(block)
    for sink in sinks or []:
        sink.close()


def speak(
    text: str,
    *,
    voice: str,
    volume: int,
    speed: float,
    device_spec: str | None,
    lang: str | None = None,
) -> None:
    """Speak `text`. Blocks until it has been played.

    `CLAUDIO_TTS_FAKE_PLAYER=<file>` swaps the audio for a log line in that file, so tests and CI
    can exercise everything around playback without a sound card.
    """
    fake = os.environ.get("CLAUDIO_TTS_FAKE_PLAYER")
    if fake:
        with open(fake, "a", encoding="utf-8") as log:
            log.write(f"{os.getpid()}\t{volume}\t{speed}\t{device_spec}\t{voice}\t{text}\n")
        time.sleep(float(os.environ.get("CLAUDIO_TTS_FAKE_SECONDS", "0")))
        return
    gain = max(1, min(10, volume)) / 10
    speed = max(MIN_SPEED, min(MAX_SPEED, speed))
    outputs = devices.pick(device_spec, devices.outputs())
    asyncio.run(_stream(text, voice, gain, outputs, speed, lang or voices.language(voice)))
