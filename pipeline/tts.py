"""Krok 3: hlas. Dispatcher mezi ElevenLabs (realisticky) a edge-tts (zdarma fallback).

TTS_PROVIDER=elevenlabs -> zkusi ElevenLabs, pri chybe (kvota/klic/sit) spadne na edge-tts.
TTS_PROVIDER=edge       -> rovnou edge-tts.
Tim se pipeline nikdy nezasekne na hlasu.
"""
import config
from pipeline import tts_edge


def synthesize(text: str, audio_path: str, ass_path: str):
    if config.TTS_PROVIDER == "elevenlabs":
        try:
            from pipeline import tts_elevenlabs
            tts_elevenlabs.synthesize(text, audio_path, ass_path)
            return
        except Exception as e:
            print(f"      ElevenLabs selhal ({e}). Fallback na edge-tts.")
    tts_edge.synthesize(text, audio_path, ass_path)
