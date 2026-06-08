import os
from pathlib import Path

ROOT = Path(__file__).parent
OUTPUT_DIR = ROOT / "output"
ASSETS_DIR = ROOT / "assets"
OUTPUT_DIR.mkdir(exist_ok=True)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")

AFFILIATE_API_URL = os.environ.get("AFFILIATE_API_URL", "")
AFFILIATE_API_KEY = os.environ.get("AFFILIATE_API_KEY", "")

# --- Hlas ---
TTS_PROVIDER = os.environ.get("TTS_PROVIDER", "edge")  # edge | elevenlabs
VOICE = os.environ.get("VOICE", "cs-CZ-AntoninNeural")        # edge-tts hlas (fallback)
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "")
ELEVENLABS_MODEL = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")

# --- Stock fotky ---
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

# --- Hudba ---
MUSIC_VOLUME = float(os.environ.get("MUSIC_VOLUME", "0.12"))

TIKTOK_CLIENT_KEY = os.environ.get("TIKTOK_CLIENT_KEY", "")
TIKTOK_CLIENT_SECRET = os.environ.get("TIKTOK_CLIENT_SECRET", "")
TIKTOK_REFRESH_TOKEN = os.environ.get("TIKTOK_REFRESH_TOKEN", "")

USE_SAMPLE_OFFER = os.environ.get("USE_SAMPLE_OFFER", "0") == "1"
PUBLISH = os.environ.get("PUBLISH", "0") == "1"

WIDTH, HEIGHT, FPS = 1080, 1920, 30
