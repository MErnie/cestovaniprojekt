"""Krok 3: generovani hlasu pres edge-tts + ASS titulky z casovych znacek.

ASS (misto SRT) s explicitnim PlayResX/Y = predvidatelna pozice a velikost
titulku na 1080x1920 (zadne libass preskalovani).
Funguje napric verzemi edge-tts.
"""
import asyncio
import edge_tts
import config

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,76,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,6,0,2,80,80,360,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


async def _synthesize(text: str, audio_path: str, ass_path: str):
    communicate = edge_tts.Communicate(text, config.VOICE)
    boundaries = []
    with open(audio_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                boundaries.append(chunk)

    events = []
    for b in boundaries:
        start = b["offset"] / 1e7
        end = (b["offset"] + b["duration"]) / 1e7
        word = b["text"].replace("\n", " ").strip()
        events.append(
            f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Default,,0,0,0,,{word}"
        )
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ASS_HEADER + "\n".join(events) + "\n")


def synthesize(text: str, audio_path: str, ass_path: str):
    asyncio.run(_synthesize(text, audio_path, ass_path))
