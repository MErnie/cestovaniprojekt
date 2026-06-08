import os
from pathlib import Path

ROOT = Path(__file__).parent
OUTPUT_DIR = ROOT / "output"
ASSETS_DIR = ROOT / "assets"
OUTPUT_DIR.mkdir(exist_ok=True)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL") or "deepseek/deepseek-v4-flash:free"

AFFILIATE_API_URL = os.environ.get("AFFILIATE_API_URL", "")
AFFILIATE_API_KEY = os.environ.get("AFFILIATE_API_KEY", "")

# --- Vyber nabidky ---
SELECT_MODE = os.environ.get("SELECT_MODE") or "random"   # discount | random
SELECT_TOP_N = int(os.environ.get("SELECT_TOP_N") or "8")  # z kolika top nabidek losovat
ROTATE = (os.environ.get("ROTATE") or "1") == "1"          # 1 = neopakovat nabidky, 0 = vzdy nejlepsi (i opakovane)
DEST_FILTER = os.environ.get("DEST_FILTER", "")            # napr. "Chorvatsko" (prazdne = bez filtru)
STATE_FILE = ROOT / "state" / "seen.json"                  # rotace: uz zpracovane nabidky

# --- Hlas ---
TTS_PROVIDER = os.environ.get("TTS_PROVIDER") or "edge"  # edge | elevenlabs
VOICE = os.environ.get("VOICE", "cs-CZ-AntoninNeural")        # edge-tts hlas (fallback)
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "")
ELEVENLABS_MODEL = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")

# --- Stock fotky / video ---
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
USE_VIDEO_BG = (os.environ.get("USE_VIDEO_BG") or "1") == "1"  # 1 = video pozadi, 0 = jen foto

# --- Hudba ---
MUSIC_VOLUME = float(os.environ.get("MUSIC_VOLUME", "0.12"))

TIKTOK_CLIENT_KEY = os.environ.get("TIKTOK_CLIENT_KEY", "")
TIKTOK_CLIENT_SECRET = os.environ.get("TIKTOK_CLIENT_SECRET", "")
TIKTOK_REFRESH_TOKEN = os.environ.get("TIKTOK_REFRESH_TOKEN", "")

USE_SAMPLE_OFFER = os.environ.get("USE_SAMPLE_OFFER", "0") == "1"
PUBLISH = os.environ.get("PUBLISH", "0") == "1"

WIDTH, HEIGHT, FPS = 1080, 1920, 30
