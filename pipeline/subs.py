"""Sdilene generovani ASS titulku pro vsechny TTS providery.

Styl: chunky karaoke - slova ve skupinach po ~3, aktivni slovo se rozsviti
(zlute) jak ho hlas vyslovuje (ASS \\k). Velke, tucne, vystredene, silny obrys.
"""

WORDS_PER_PHRASE = 3

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,90,&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,7,3,2,90,90,430,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
# PrimaryColour = zlute (vyslovene), SecondaryColour = bile (jeste nevysloveno)


def ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def _group(words, size):
    return [words[i:i + size] for i in range(0, len(words), size)]


def write_ass(words, ass_path: str):
    """words: list of (text, start_s, end_s). Vytvori karaoke fraze."""
    words = [(str(t).replace("\n", " ").strip(), s, e) for t, s, e in words if str(t).strip()]
    events = []
    for phrase in _group(words, WORDS_PER_PHRASE):
        start = phrase[0][1]
        end = phrase[-1][2]
        if end <= start:
            end = start + 0.4
        parts = []
        for w, s, e in phrase:
            k = max(int(round((e - s) * 100)), 1)   # centisekundy
            parts.append(f"{{\\k{k}}}{w}")
        text = " ".join(parts)
        events.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Default,,0,0,0,,{text}")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ASS_HEADER + "\n".join(events) + "\n")
