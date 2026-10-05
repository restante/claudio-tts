"""Generate docs/index.html: the GitHub Pages site with an embedded player for every voice.

GitHub READMEs cannot embed an audio player, so the README links here. Run after
`scripts/make_samples.py --all`:   python scripts/make_player.py
"""

from __future__ import annotations

import html
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
SITE = "https://restante.github.io/claudio-tts"

LANGS = [
    ("a", "🇺🇸", "American English", "en-us"),
    ("b", "🇬🇧", "British English", "en-gb"),
    ("e", "🇪🇸", "Spanish", "es"),
    ("f", "🇫🇷", "French", "fr-fr"),
    ("h", "🇮🇳", "Hindi", "hi"),
    ("i", "🇮🇹", "Italian", "it"),
    ("j", "🇯🇵", "Japanese", "ja"),
    ("p", "🇧🇷", "Brazilian Portuguese", "pt-br"),
    ("z", "🇨🇳", "Mandarin Chinese", "cmn"),
]
STARS = {"af_heart", "af_bella"}

CSS = """
:root{--bg:#0d1117;--card:#161b22;--line:#30363d;--text:#e6edf3;--dim:#9198a1;--accent:#58e6c8;--violet:#b48cf5}
@media (prefers-color-scheme:light){:root{--bg:#fff;--card:#f6f8fa;--line:#d0d7de;--text:#1f2328;--dim:#59636e;--accent:#0a8f78;--violet:#7c4dd6}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:960px;margin:0 auto;padding:32px 20px 80px}
h1{font-size:2.4rem;margin:.2em 0 0}h1 span{background:linear-gradient(90deg,var(--accent),var(--violet));-webkit-background-clip:text;background-clip:text;color:transparent}
.tag{font-size:1.2rem;color:var(--accent);margin:.2em 0 1em}.lead{color:var(--dim);max-width:62ch}
.pills{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 8px}.pills span{border:1px solid var(--line);border-radius:999px;padding:3px 12px;font-size:.85rem;color:var(--dim)}
.cta{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0 30px}.cta a{padding:9px 16px;border-radius:8px;border:1px solid var(--line);color:var(--text);text-decoration:none;background:var(--card)}
.cta a.main{background:linear-gradient(90deg,var(--accent),var(--violet));color:#06120f;border:0;font-weight:600}
h2{margin:34px 0 4px;font-size:1.25rem}h2 small{color:var(--dim);font-weight:400;font-size:.85rem;margin-left:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:10px;margin-top:10px}
.voice{display:flex;align-items:center;gap:12px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 12px;position:relative;overflow:hidden}
.voice:target,.voice.playing{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent)}
.play{flex:none;width:42px;height:42px;border-radius:50%;border:0;cursor:pointer;background:var(--accent);color:#06120f;font-size:16px;display:grid;place-items:center}
.play:focus-visible{outline:3px solid var(--violet);outline-offset:2px}
.meta{min-width:0;flex:1}.name{font-family:ui-monospace,Menlo,Consolas,monospace;font-weight:600}.sub{color:var(--dim);font-size:.8rem}
.copy{border:1px solid var(--line);background:transparent;color:var(--dim);border-radius:6px;font:12px ui-monospace,Menlo,monospace;padding:3px 7px;cursor:pointer}
.copy:hover{color:var(--text);border-color:var(--accent)}
.bar{position:absolute;left:0;bottom:0;height:3px;width:0;background:var(--accent)}
.note{border-left:3px solid var(--violet);padding:6px 14px;color:var(--dim);margin:22px 0}
code{font-family:ui-monospace,Menlo,Consolas,monospace;background:var(--card);border:1px solid var(--line);border-radius:5px;padding:1px 6px}
pre{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;overflow:auto}
footer{margin-top:50px;color:var(--dim);font-size:.9rem}a{color:var(--accent)}
"""

JS = """
const audio = new Audio(); let current = null;
function reset(){ if(current){ current.row.classList.remove('playing'); current.btn.textContent='▶'; current.btn.setAttribute('aria-label','Play '+current.name); current.bar.style.width='0'; } current=null; }
function toggle(row){
  const btn=row.querySelector('.play'), bar=row.querySelector('.bar'), name=row.dataset.voice;
  if(current && current.row===row){ if(audio.paused){ audio.play(); btn.textContent='❚❚'; } else { audio.pause(); btn.textContent='▶'; } return; }
  reset(); audio.src='samples/'+name+'.mp3'; current={row,btn,bar,name};
  audio.play().then(()=>{ row.classList.add('playing'); btn.textContent='❚❚'; btn.setAttribute('aria-label','Pause '+name); }).catch(()=>{ reset(); });
}
audio.addEventListener('timeupdate',()=>{ if(current && audio.duration) current.bar.style.width=(100*audio.currentTime/audio.duration)+'%'; });
audio.addEventListener('ended',reset);
document.querySelectorAll('.voice').forEach(row=>{
  row.querySelector('.play').addEventListener('click',()=>toggle(row));
  row.querySelector('.copy').addEventListener('click',e=>{ const t='/tts voice '+row.dataset.voice; navigator.clipboard.writeText(t).then(()=>{ e.target.textContent='copied'; setTimeout(()=>e.target.textContent='copy command',1200); }); });
});
"""


def voice_row(name: str) -> str:
    star = " ⭐" if name in STARS else ""
    gender = "female" if name[1] == "f" else "male"
    return (
        f'<div class="voice" id="{name}" data-voice="{name}">'
        f'<button class="play" aria-label="Play {name}">▶</button>'
        f'<div class="meta"><div class="name">{name}{star}</div><div class="sub">{gender}</div></div>'
        f'<button class="copy" title="Copy the Claude Code command">copy command</button>'
        f'<div class="bar"></div></div>'
    )


def main() -> None:
    names = sorted(p.stem for p in (DOCS / "samples").glob("*.mp3"))
    sections = []
    for letter, flag, label, code in LANGS:
        group = [n for n in names if n[0] == letter]
        if not group:
            continue
        rows = "".join(voice_row(n) for n in group)
        sections.append(
            f"<h2>{flag} {html.escape(label)}<small>{len(group)} voices · <code>{code}</code></small></h2>"
            f'<div class="grid">{rows}</div>'
        )
    title = "claudio-tts: make Claude Code talk back, with Kokoro voices"
    desc = (
        "Listen to all Kokoro voices that claudio-tts can use to make Claude Code talk back. "
        "Local text-to-speech, no API key, no tokens, offline."
    )
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(desc)}">
<meta property="og:image" content="{SITE}/social-preview.png"><meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{SITE}/">
<style>{CSS}</style></head>
<body><main>
<h1>🔊 <span>claudio-tts</span></h1>
<p class="tag">Make Claude Code talk back.</p>
<p class="lead">Natural spoken replies for Claude Code, powered by the open-source Kokoro voice model and built on
Claude Code's mod system. No API key, no tokens, no bill, and your text never leaves your machine.
Press play on any voice below.</p>
<div class="pills"><span>No API key</span><span>0 extra tokens</span><span>Offline</span><span>{len(names)} voices</span><span>9 native languages</span><span>macOS · Windows (beta)</span></div>
<div class="cta"><a class="main" href="https://github.com/restante/claudio-tts#-install">Install</a>
<a href="https://github.com/restante/claudio-tts">GitHub</a>
<a href="https://github.com/restante/claudio-tts/issues/new?template=bug_report.yml">Report a bug</a>
<a href="https://github.com/restante/claudio-tts/blob/main/CONTRIBUTING.md">Contribute</a></div>
<div class="note">Use a voice in Claude Code with <code>/tts voice &lt;name&gt;</code>, for example
<code>/tts voice af_heart</code>. Samples are generated by Kokoro on a laptop, with the voice's own language.</div>
{"".join(sections)}
<h2>Any other voice, any other language</h2>
<p class="lead">These are the voices that ship with Kokoro, not a limit. Any Kokoro-compatible voice works: drop a
voice file in your <code>voices</code> folder, or point <code>CLAUDIO_TTS_MODEL</code> and
<code>CLAUDIO_TTS_VOICES</code> at another Kokoro model and voices pack. And a voice can read <em>any</em> of 140
languages with <code>/tts lang &lt;code&gt;</code> (with an accent where it has no native voice), for example
<code>/tts lang de</code> for German. Details in the
<a href="https://github.com/restante/claudio-tts/blob/main/docs/voices.md">voices guide</a>.</p>
<pre>/tts voice bf_emma
/tts speed 0.9
/tts lang de          # German through the current voice, with an accent
/tts lang auto        # back to the voice's own language</pre>
<footer>MIT licensed · Kokoro-82M by hexgrad (Apache-2.0) via kokoro-onnx ·
<a href="https://github.com/restante/claudio-tts">github.com/restante/claudio-tts</a></footer>
</main><script>{JS}</script></body></html>
"""
    (DOCS / "index.html").write_text(page, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    print(f"wrote docs/index.html with {len(names)} voices")


if __name__ == "__main__":
    main()
