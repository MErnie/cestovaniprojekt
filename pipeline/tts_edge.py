"""edge-tts hlas (zdarma, fallback) + ASS titulky z WordBoundary znacek."""
import asyncio
import edge_tts
import config
from pipeline.subs import write_ass


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
    write_ass(words, ass_path)


def synthesize(text: str, audio_path: str, ass_path: str):
    asyncio.run(_synthesize(text, audio_path, ass_path))
