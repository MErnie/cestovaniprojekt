"""Stock fotky destinace pres Pexels API (zdarma). Doplnuje obrazky z feedu
o zabery mesta, plaze a atrakci. Bez klice vrati [] (pipeline pak pouzije jen feed)."""
import requests
import config

SEARCH = "https://api.pexels.com/v1/search"


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
        print(f"      Pexels selhal ({e}). Pokracuji bez stock fotek.")
    return urls[:n]
