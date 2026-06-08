"""Krok 2: generovani scenare pres OpenRouter (OpenAI-compatible API), striktni JSON.

Odolnost:
- zkousi vic modelu (fallback), retry s backoffem na 429,
- kdyz LLM uplne selze (kvota/sit/klic), slozi scenar z dat bez LLM (template),
  takze pipeline vzdy vyrobi video.
"""
import json
import time

import requests
import config

API_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """Jsi scenarista virálních faceless videí pro TikTok o cestovatelských slevách.
Z dodané nabídky vytvoř krátký scénář (video 20-35 sekund) v ČEŠTINĚ.
Struktura scén: Hook (3s), Problém, Řešení, CTA.
Mluvený text (voiceover) musí být úderný, hovorový, bez vykání, S DIAKRITIKOU.
visual_overlay je krátký text na obrazovku (max 5 slov, velká čísla a sleva).
caption je popisek pod video včetně 5-8 hashtagů.

Vrať POUZE validní JSON v PŘESNĚ tomto tvaru, nic jiného:
{
  "video_title": "string",
  "caption": "string",
  "scenes": [
    {"duration": 3, "voiceover": "string", "visual_overlay": "string"}
  ]
}"""

# fallback modely (vsechny zdarma). Pokud primarni selze, zkusi je poporade.
MODEL_FALLBACK = [
    "deepseek/deepseek-v4-flash:free",
    "moonshotai/kimi-k2.6:free",
    "google/gemma-4-31b-it:free",
]


def _template_script(offer: dict) -> dict:
    loc = offer.get("location", "")
    price = offer.get("price", "")
    disc = offer.get("discount", "")
    return {
        "video_title": f"{loc} {disc}",
        "caption": (
            f"{loc} se slevou {disc}! Cena {price}. Odkaz v biu. "
            f"#dovolena #sleva #cestovani #lastminute "
            f"#{loc.split(',')[0].strip().replace(' ', '')} #zajezd #travel #levnedovolene"
        ),
        "scenes": [
            {"duration": 3, "voiceover": f"Tohle musíš vidět. {loc} za zlomek ceny.",
             "visual_overlay": f"{loc}\n{disc}"},
            {"duration": 5, "voiceover": "Zapomeň na drahé cestovky a hledání po internetu.",
             "visual_overlay": "STOP\ndrahým cestovkám"},
            {"duration": 5, "voiceover": f"Našel jsem nabídku, kde to vyjde na {price}.",
             "visual_overlay": f"Cena\n{price}"},
            {"duration": 4, "voiceover": "Odkaz najdeš v biu. Pospěš si, mizí to rychle.",
             "visual_overlay": "Odkaz v biu"},
        ],
        "url": offer.get("url", ""),
    }


def _parse_json(content: str) -> dict:
    content = content.strip()
    if content.startswith("```"):  # nekdy model obali JSON do code fence
        content = content.split("```", 2)[1].lstrip("json").strip("` \n")
    return json.loads(content)


def _try_openrouter(offer: dict) -> dict:
    user_prompt = (
        f"Nabídka:\n"
        f"- Lokalita: {offer['location']}\n"
        f"- Cena: {offer['price']}\n"
        f"- Sleva: {offer['discount']}\n"
        f"- Popis: {offer['description']}\n"
    )
    models = [config.OPENROUTER_MODEL] + [m for m in MODEL_FALLBACK if m != config.OPENROUTER_MODEL]
    last_err = None
    for model_name in models:
        for attempt in range(3):
            try:
                r = requests.post(
                    API_URL,
                    headers={
                        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.9,
                    },
                    timeout=60,
                )
                if r.status_code == 429:
                    raise requests.HTTPError("429")
                r.raise_for_status()
                content = r.json()["choices"][0]["message"]["content"]
                script = _parse_json(content)
                script["url"] = offer.get("url", "")
                print(f"      LLM: {model_name}")
                return script
            except Exception as e:
                last_err = e
                if "429" in str(e):
                    wait = 2 ** attempt
                    print(f"      {model_name} 429, retry za {wait}s...")
                    time.sleep(wait)
                else:
                    break  # zkus dalsi model
    raise last_err


def generate_script(offer: dict) -> dict:
    if not config.OPENROUTER_API_KEY:
        print("      Chybi OPENROUTER_API_KEY -> template fallback.")
        return _template_script(offer)
    try:
        return _try_openrouter(offer)
    except Exception as e:
        print(f"      LLM selhal ({e}). Pouzivam template fallback.")
        return _template_script(offer)
