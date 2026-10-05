"""Turn a Claude reply (markdown) into plain text that sounds right when spoken."""

from __future__ import annotations

import html
import re
import unicodedata

import mistune

_parse = mistune.create_markdown(renderer="ast", plugins=["strikethrough", "table"])

_URL = re.compile(r"https?://\S+")
_COMMENT = re.compile(r"<!--.*?-->", re.S)
_SPACES = re.compile(r"[ \t]+")
_BLANKS = re.compile(r"\n{3,}")
_EMOJI = re.compile("[\U0001f300-\U0001faff\U00002600-\U000027bf\U0001f000-\U0001f2ff️‍]+")


def _inline(nodes: list[dict]) -> str:
    out: list[str] = []
    for node in nodes:
        kind = node["type"]
        if kind == "text":
            out.append(node["raw"])
        elif kind in ("strong", "emphasis", "strikethrough", "link"):
            out.append(_inline(node.get("children", [])))
        elif kind == "image":
            out.append(_inline(node.get("children", [])))
        elif kind in ("softbreak", "linebreak"):
            out.append(" ")
        # codespan, inline_html: dropped on purpose
    return "".join(out)


def _block(nodes: list[dict]) -> list[str]:
    lines: list[str] = []
    for node in nodes:
        kind = node["type"]
        if kind in ("paragraph", "block_text"):
            lines.append(_inline(node.get("children", [])).strip())
        elif kind == "heading":
            text = _inline(node.get("children", [])).strip()
            lines.append(text if text.endswith((".", "!", "?", ":")) else text + ".")
        elif kind in ("list", "block_quote"):
            lines.extend(_block(node.get("children", [])))
        elif kind == "list_item":
            lines.extend(_block(node.get("children", [])))
        elif kind == "table":
            for part in node.get("children", []):
                for row in part.get("children", []):
                    cells = [
                        _inline(c.get("children", [])).strip() for c in row.get("children", [])
                    ]
                    lines.append(", ".join(c for c in cells if c) + ".")
        # block_code, thematic_break, block_html: dropped on purpose
    return lines


def clean(text: str) -> str:
    """Plain, speakable text. Code blocks and inline code are dropped, links keep their label."""
    text = _COMMENT.sub("", text)
    lines = _block(_parse(text))
    out = "\n".join(line for line in lines if line)
    out = html.unescape(out)
    out = _URL.sub("link", out)
    out = _EMOJI.sub("", out)
    out = unicodedata.normalize("NFKC", out)
    out = _SPACES.sub(" ", out)
    out = _BLANKS.sub("\n\n", out)
    return out.strip()
