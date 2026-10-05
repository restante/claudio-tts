"""Render docs/social-preview.png (1280x640), the image GitHub shows when the repo is shared.

GitHub only accepts it through the web UI: Settings > General > Social preview > Upload.
Needs Pillow (`pip install pillow`). Fonts are taken from macOS; adjust FONT_* on other systems.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 640
OUT = Path(__file__).resolve().parent.parent / "docs" / "social-preview.png"
FONT_BOLD = "/System/Library/Fonts/Helvetica.ttc"
FONT_MONO = "/System/Library/Fonts/Menlo.ttc"


def font(path: str, size: int, index: int = 0) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size, index=index)


def gradient() -> Image.Image:
    top, bottom = (13, 17, 28), (30, 20, 60)
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        row = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        for x in range(W):
            px[x, y] = row
    return img


def waves(draw: ImageDraw.ImageDraw) -> None:
    """A row of rounded bars shaped like a voice waveform, fading from teal to violet."""
    n, x0, base = 46, 80, 508
    for i in range(n):
        env = math.sin(math.pi * i / (n - 1)) ** 1.4
        h = 18 + 130 * env * (0.55 + 0.45 * math.sin(i * 0.9) ** 2)
        t = i / (n - 1)
        color = (int(56 + 150 * t), int(220 - 110 * t), int(200 + 40 * t))
        x = x0 + i * 25
        draw.rounded_rectangle([x, base - h / 2, x + 14, base + h / 2], radius=7, fill=color)


def main() -> None:
    img = gradient()
    draw = ImageDraw.Draw(img)
    waves(draw)
    draw.text((80, 92), "claudio-tts", font=font(FONT_BOLD, 120, 1), fill=(255, 255, 255))
    draw.text(
        (84, 238), "Make Claude Code talk back.", font=font(FONT_BOLD, 54, 0), fill=(150, 235, 220)
    )
    draw.text(
        (84, 316),
        "Local text-to-speech for Claude Code, built on Claude Code mods.",
        font=font(FONT_BOLD, 30, 0),
        fill=(190, 195, 215),
    )
    x = 84
    for label in ("No API key", "0 extra tokens", "Offline", "54 voices", "9 languages"):
        f = font(FONT_MONO, 26, 0)
        w = draw.textlength(label, font=f) + 36
        draw.rounded_rectangle([x, 388, x + w, 436], radius=24, outline=(120, 130, 190), width=2)
        draw.text((x + 18, 396), label, font=f, fill=(225, 228, 245))
        x += w + 14
    draw.text(
        (84, 590),
        "github.com/restante/claudio-tts",
        font=font(FONT_MONO, 26, 0),
        fill=(130, 140, 180),
    )
    img.save(OUT, optimize=True)
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
