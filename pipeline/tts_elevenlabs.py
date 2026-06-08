"""ElevenLabs hlas (realisticky) + ASS titulky z character-level timestampu."""
import base64
import requests
import config
from pipeline.subs import write_ass

API = "https://api.elevenlabs.io/v1/text-to-speech/{vid}/with-timestamps"


def _words_from_alignment(alignment: dict):
    chars = alignment["characters"]
    starts = alignment["character_start_times_seconds"]
    ends = alignment["character_end_times_seconds"]
    words = []
    cur, w_start, w_end = "", None, None
    for ch, s, e in zip(chars, starts, ends):
        if ch.isspace():
            if cur:
                words.append((cur, w_start, w_end))
                cur, w_start, w_end = "", None, None
        else:
            if not cur:
                w_start = s
            cur += ch
            w_end = e
    if cur:
        words.append((cur, w_start, w_end))
    return words


def synthesize(text: str, audio_path: str, ass_path: str):
    if not config.ELEVENLABS_API_KEY or not config.ELEVENLABS_VOICE_ID:
        raise ValueError("Chybi ELEVENLABS_API_KEY nebo ELEVENLABS_VOICE_ID.")
    r = requests.post(
        API.format(vid=config.ELEVENLABS_VOICE_ID),
        headers={"xi-api-key": config.ELEVENLABS_API_KEY,
                 "Content-Type": "application/json"},
        json={
            "text": text,
            "model_id": config.ELEVENLABS_MODEL,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.0},
        },
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    with open(audio_path, "wb") as f:
        f.write(base64.b64decode(data["audio_base64"]))
    align = data.get("alignment") or data.get("normalized_alignment")
    write_ass(_words_from_alignment(align), ass_path)
