"""edge-tts hlas (zdarma, fallback) + ASS titulky z WordBoundary znacek.

Kdyz edge-tts nevrati casovani slov (WordBoundary), rozdelime slova rovnomerne
pres delku audia - titulky se tak zobrazi vzdy.
"""
import asyncio
import subprocess

import edge_tts
import config
from pipeline.subs import write_ass


def _audio_duration(path: str) -> float:
    try:
        out = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", path])
        return float(out.strip())
    except Exception:
        return 0.0


def _even_words(text: str, duration: float):
    words = text.split()
    if not words or duration <= 0:
        return []
    step = duration / len(words)
    return [(w, i * step, (i + 1) * step) for i, w in enumerate(words)]


async def _synthesize(text: str, audio_path: str, ass_path: str):
    communicate = edge_tts.Communicate(text, config.VOICE)
    words = []
    with open(audio_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 1e7
                end = (chunk["offset"] + chunk["duration"]) / 1e7
                words.append((chunk["text"], start, end))
    if not words:  # fallback: rovnomerne rozlozeni pres delku audia
        words = _even_words(text, _audio_duration(audio_path))
    write_ass(words, ass_path)


def synthesize(text: str, audio_path: str, ass_path: str):
    asyncio.run(_synthesize(text, audio_path, ass_path))
