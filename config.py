import os
from pathlib import Path

ROOT = Path(__file__).parent
OUTPUT_DIR = ROOT / "output"
ASSETS_DIR = ROOT / "assets"
OUTPUT_DIR.mkdir(exist_ok=True)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

AFFILIATE_API_URL = os.environ.get("AFFILIATE_API_URL", "")
AFFILIATE_API_KEY = os.environ.get("AFFILIATE_API_KEY", "")

VOICE = os.environ.get("VOICE", "cs-CZ-AntoninNeural")

TIKTOK_CLIENT_KEY = os.environ.get("TIKTOK_CLIENT_KEY", "")
TIKTOK_CLIENT_SECRET = os.environ.get("TIKTOK_CLIENT_SECRET", "")
TIKTOK_REFRESH_TOKEN = os.environ.get("TIKTOK_REFRESH_TOKEN", "")

USE_SAMPLE_OFFER = os.environ.get("USE_SAMPLE_OFFER", "0") == "1"
PUBLISH = os.environ.get("PUBLISH", "0") == "1"

WIDTH, HEIGHT, FPS = 1080, 1920, 30
