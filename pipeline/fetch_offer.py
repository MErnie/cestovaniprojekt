"""Krok 1: ziskani nabidky z Invia XML feedu (affiliate).

Samo-adaptivni parser: najde opakujici se polozky a namapuje pole podle nazvu
tagu (case-insensitive, vic synonym). Vybere nejlepsi nabidku podle slevy.

Diagnostika struktury feedu:
    python -m pipeline.fetch_offer --inspect
(vypise root, polozkovy tag a dostupna pole prvni polozky)
"""
import hashlib
import json
import os
import random
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter

import requests
import config

FEEDS = {
    "bomby": "https://affil.invia.cz/direct/core/tool_xml-feed/download/id/9159030-6a1345ff6279d/",
    "nejpro": "https://affil.invia.cz/direct/core/tool_xml-feed/download/id/9159030-6a134572a44b1/",
    "zakladni": "https://affil.invia.cz/direct/core/tool_xml-feed/download/id/9159030-6a134664746eb/",
}

# kandidatni nazvy tagu pro kazde normalizovane pole (lowercase, bez namespace)
FIELD_TAGS = {
    "name": ["nazev", "nazev_hotelu", "hotel", "name", "title", "nazevhotelu"],
    "country": ["zeme", "stat", "country"],
    "location": ["lokalita", "destinace", "misto", "oblast", "location", "mesto", "region", "strediska", "stredisko"],
    "price": ["cena", "cena_od", "cena_zajezdu", "cena_celkem", "price", "cena_po_sleve"],
    "old_price": ["cena_puvodni", "puvodni_cena", "cena_bez_slevy", "old_price", "price_old", "cena_pred_slevou"],
    "discount": ["sleva", "sleva_procenta", "discount", "sleva_pct"],
    "url": ["url", "odkaz", "link", "deeplink", "affiliate_url", "url_zajezdu"],
    "image": ["obrazek", "image", "foto", "img", "picture", "image_url", "fotka", "main_photo"],
    "stars": ["hvezdicky", "stars", "trida", "kategorie", "kategorie_hotelu"],
    "board": ["strava", "stravovani", "board", "typ_stravy"],
    "term": ["termin", "datum", "term", "date_from", "datum_od", "odjezd"],
    "nights": ["pocet_noci", "noci", "delka", "pocet_dni", "nights", "days"],
}


def _localname(tag: str) -> str:
    return tag.split("}")[-1].lower()


def _find(item, keys):
    """Vrati text prvniho potomka, jehoz lokalni tag je v keys."""
    for el in item.iter():
        if _localname(el.tag) in keys and el.text and el.text.strip():
            return el.text.strip()
    return ""


def _all(item, keys):
    out = []
    for el in item.iter():
        if _localname(el.tag) in keys and el.text and el.text.strip():
            out.append(el.text.strip())
    return out


def _num(s: str) -> float | None:
    if not s:
        return None
    digits = re.sub(r"[^\d]", "", s.replace(",", "."))
    return float(digits) if digits else None


def _download(feed_key: str) -> bytes:
    url = FEEDS.get(feed_key) or config.AFFILIATE_API_URL
    if not url:
        raise ValueError(f"Nezmany feed '{feed_key}'. Pouzij: {list(FEEDS)}")
    r = requests.get(url, timeout=120, headers={"User-Agent": "Mozilla/5.0 video-tovarna"})
    r.raise_for_status()
    return r.content


def _item_elements(root):
    """Najde opakujici se polozkovy element (nejcastejsi tag mezi vnoucaty)."""
    # zkus primé deti rootu
    children = list(root)
    if children:
        tags = Counter(_localname(c.tag) for c in children)
        common, n = tags.most_common(1)[0]
        if n >= 2:
            return [c for c in children if _localname(c.tag) == common]
    # jinak hledej o uroven niz
    for child in children:
        sub = list(child)
        tags = Counter(_localname(c.tag) for c in sub)
        if tags:
            common, n = tags.most_common(1)[0]
            if n >= 2:
                return [c for c in sub if _localname(c.tag) == common]
    return children


def _to_offer(item) -> dict:
    name = _find(item, FIELD_TAGS["name"])
    country = _find(item, FIELD_TAGS["country"])
    location = _find(item, FIELD_TAGS["location"])
    price_raw = _find(item, FIELD_TAGS["price"])
    old_raw = _find(item, FIELD_TAGS["old_price"])
    disc_raw = _find(item, FIELD_TAGS["discount"])
    stars = _find(item, FIELD_TAGS["stars"])
    board = _find(item, FIELD_TAGS["board"])
    term = _find(item, FIELD_TAGS["term"])
    nights = _find(item, FIELD_TAGS["nights"])
    url = _find(item, FIELD_TAGS["url"])
    images = _all(item, FIELD_TAGS["image"])[:5]

    price = _num(price_raw)
    old = _num(old_raw)
    disc = _num(disc_raw)
    if disc is None and price and old and old > price:
        disc = round((1 - price / old) * 100)

    loc = ", ".join(x for x in [location, country] if x) or country or location or name
    desc_parts = []
    if stars:
        desc_parts.append(f"{stars}* hotel")
    if name:
        desc_parts.append(name)
    if loc:
        desc_parts.append(f"v lokalite {loc}")
    if board:
        desc_parts.append(board)
    if nights:
        desc_parts.append(f"{nights} noci")
    if old and price:
        desc_parts.append(f"puvodne {old:.0f} Kc, nyni {price:.0f} Kc")

    return {
        "title": name or loc,
        "location": loc,
        "price": f"{price:.0f} Kc" if price else (price_raw or ""),
        "discount": f"-{disc:.0f} %" if disc else (disc_raw or ""),
        "description": ". ".join(desc_parts),
        "url": url,
        "image_urls": images,
        "_discount_num": disc or 0,
        "_price_num": price or 1e12,
    }


def _offer_id(o: dict) -> str:
    base = o.get("url") or f"{o.get('title')}|{o.get('price')}"
    return hashlib.md5(base.encode("utf-8")).hexdigest()[:16]


def _load_seen() -> list:
    try:
        return json.loads(config.STATE_FILE.read_text())
    except Exception:
        return []


def _save_seen(seen: list):
    config.STATE_FILE.parent.mkdir(exist_ok=True)
    # drz jen poslednich 500 zaznamu, at soubor neroste donekonecna
    config.STATE_FILE.write_text(json.dumps(seen[-500:], ensure_ascii=False))


def _select(offers: list) -> dict:
    """Vyber podle DEST_FILTER + rotace (bez opakovani) + SELECT_MODE."""
    # filtr destinace
    if config.DEST_FILTER:
        f = config.DEST_FILTER.lower()
        filtered = [o for o in offers if f in (o.get("location", "") + o.get("title", "")).lower()]
        offers = filtered or offers  # kdyz filtr nic nenajde, neztrat vse

    # serad podle slevy (pak nejnizsi cena)
    offers.sort(key=lambda o: (-o["_discount_num"], o["_price_num"]))

    # rotace: vyhod uz zpracovane; kdyz dojdou, resetuj
    seen = _load_seen()
    fresh = [o for o in offers if _offer_id(o) not in seen]
    if not fresh:
        seen, fresh = [], offers

    if config.SELECT_MODE == "random":
        chosen = random.choice(fresh[:max(config.SELECT_TOP_N, 1)])
    else:  # discount
        chosen = fresh[0]

    seen.append(_offer_id(chosen))
    _save_seen(seen)
    return chosen


def fetch_from_affiliate_api() -> dict:
    feed_key = os.environ.get("FEED") or "bomby"
    root = ET.fromstring(_download(feed_key))
    items = _item_elements(root)
    offers = [_to_offer(i) for i in items]
    offers = [o for o in offers if o["title"] and (o["_price_num"] < 1e12)]
    if not offers:
        raise ValueError("Z feedu se nepodarilo vytahnout zadnou nabidku. Spust --inspect.")
    best = _select(offers)
    best.pop("_discount_num", None)
    best.pop("_price_num", None)
    return best


SAMPLE_OFFER = {
    "title": "Chorvatsko za hubicku",
    "location": "Pula, Chorvatsko",
    "price": "8 900 Kc",
    "discount": "-45 %",
    "description": "Luxusni 5* hotel v Pule se slevou 45 %. Bezne 16 000 Kc, ted 8 900 Kc.",
    "url": "https://example.com/?aff=TVOJE_ID",
    "image_urls": [],
}


def get_offer() -> dict:
    if config.USE_SAMPLE_OFFER:
        return SAMPLE_OFFER
    return fetch_from_affiliate_api()


def _inspect():
    feed_key = os.environ.get("FEED", "bomby")
    print(f"Feed: {feed_key}")
    root = ET.fromstring(_download(feed_key))
    print(f"Root tag: {_localname(root.tag)}")
    items = _item_elements(root)
    print(f"Pocet polozek: {len(items)}")
    if items:
        first = items[0]
        print(f"Polozkovy tag: {_localname(first.tag)}")
        print("Dostupna pole prvni polozky:")
        for el in first.iter():
            if el is first:
                continue
            txt = (el.text or "").strip()[:60]
            print(f"  <{_localname(el.tag)}> = {txt}")
        print("\nNamapovana nabidka:")
        for k, v in _to_offer(first).items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    if "--inspect" in sys.argv:
        _inspect()
    else:
        print(get_offer())
