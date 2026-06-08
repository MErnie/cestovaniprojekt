"""Stock fotky destinace pres Pexels API (zdarma). Doplnuje obrazky z feedu
o zabery mesta, plaze a atrakci. Bez klice vrati [] (pipeline pak pouzije jen feed)."""
import requests
import config

SEARCH = "https://api.pexels.com/v1/search"
VIDEO_SEARCH = "https://api.pexels.com/videos/search"


def _query_terms(location: str):
    city = location.split(",")[0].strip()
    country = location.split(",")[-1].strip() if "," in location else location
    return [f"{city} beach", f"{city} city", f"{country} travel", f"{city} resort"]


def get_stock_images(location: str, n: int = 3) -> list:
    if not config.PEXELS_API_KEY or not location:
        return []
    urls = []
    try:
        for q in _query_terms(location):
            if len(urls) >= n:
                break
            r = requests.get(
                SEARCH,
                headers={"Authorization": config.PEXELS_API_KEY},
                params={"query": q, "per_page": 2, "orientation": "portrait"},
                timeout=30,
            )
            if r.status_code != 200:
                continue
            for p in r.json().get("photos", []):
                src = p.get("src", {})
                u = src.get("portrait") or src.get("large")
                if u and u not in urls:
                    urls.append(u)
                if len(urls) >= n:
                    break
    except Exception as e:
        print(f"      Pexels foto selhal ({e}). Pokracuji bez stock fotek.")
    return urls[:n]


def _best_video_file(video: dict) -> str:
    """Vybere portrait mp4 soubor v rozumnem rozliseni."""
    files = [f for f in video.get("video_files", []) if f.get("file_type") == "video/mp4"]
    # preferuj portrait (vyssi nez sirsi) a vysku >= 1080
    portrait = [f for f in files if (f.get("height") or 0) >= (f.get("width") or 0)]
    pool = portrait or files
    pool = sorted(pool, key=lambda f: abs((f.get("height") or 0) - 1920))
    return pool[0]["link"] if pool else ""


def get_stock_videos(location: str, n: int = 3) -> list:
    if not config.PEXELS_API_KEY or not location:
        return []
    urls = []
    try:
        for q in _query_terms(location):
            if len(urls) >= n:
                break
            r = requests.get(
                VIDEO_SEARCH,
                headers={"Authorization": config.PEXELS_API_KEY},
                params={"query": q, "per_page": 2, "orientation": "portrait"},
                timeout=30,
            )
            if r.status_code != 200:
                continue
            for v in r.json().get("videos", []):
                link = _best_video_file(v)
                if link and link not in urls:
                    urls.append(link)
                if len(urls) >= n:
                    break
    except Exception as e:
        print(f"      Pexels video selhal ({e}). Pokracuji bez video pozadi.")
    return urls[:n]
