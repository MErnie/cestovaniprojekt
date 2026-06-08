"""Uprava textu pro overlay: odstraneni emoji, zalomeni na sirku, vypocet velikosti fontu,
aby se text vzdy vesel na obrazovku (zadne orezavani)."""
import re

# povolene znaky: pismena (vc. ceske diakritiky), cislice, mezera, bezna interpunkce
_ALLOWED = re.compile(r"[0-9A-Za-zÀ-ž  %.,!?:\-+\n]")


def strip_emoji(text: str) -> str:
    return "".join(ch for ch in text if _ALLOWED.match(ch))


def _wrap_line(line: str, max_chars: int) -> list:
    words = line.split()
    lines, cur = [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > max_chars:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


def prepare_overlay(text: str, max_chars: int = 14):
    """Vrati (vycisteny_zalomeny_text, fontsize). Zarucuje, ze se vejde na sirku."""
    text = strip_emoji(text).strip()
    out_lines = []
    for raw in text.split("\n"):
        out_lines.extend(_wrap_line(raw, max_chars) or [""])
    out_lines = [l for l in out_lines if l != ""] or [""]
    wrapped = "\n".join(out_lines)

    longest = max((len(l) for l in out_lines), default=1)
    # sirka pisma tucneho sans ~ 0.58 * fontsize; budget ~960 px
    fontsize = int(960 / (0.58 * max(longest, 1)))
    fontsize = max(46, min(96, fontsize))
    return wrapped, fontsize
