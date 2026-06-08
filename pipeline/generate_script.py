"""Krok 2: generovani scenare pres Gemini (striktni JSON).

Odolnost:
- zkousi vic modelu (fallback), retry s backoffem na 429,
- kdyz LLM uplne selze (kvota/sit), slozi scenar z dat bez LLM (template),
  takze pipeline vzdy vyrobi video.
"""
import json
import time

import google.generativeai as genai
import config

SYSTEM_PROMPT = """Jsi scenarista virálních faceless videí pro TikTok o cestovatelských slevách.
Z dodané nabídky vytvoř krátký scénář (video 20-35 sekund) v ČEŠTINĚ.
Struktura scén: Hook (3s), Problém, Řešení, CTA.
Mluvený text (voiceover) musí být úderný, hovorový, bez vykání.
visual_overlay je krátký text na obrazovku (max 5 slov, velká čísla a sleva).
caption je popisek pod video včetně 5-8 hashtagů.
Vrať POUZE validní JSON, nic jiného."""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "video_title": {"type": "string"},
        "caption": {"type": "string"},
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "duration": {"type": "integer"},
                    "voiceover": {"type": "string"},
                    "visual_overlay": {"type": "string"},
                },
                "required": ["duration", "voiceover", "visual_overlay"],
            },
        },
    },
    "required": ["video_title", "caption", "scenes"],
}

MODEL_FALLBACK = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash"]


def _template_script(offer: dict) -> dict:
    """Scenar bez LLM - slozi se primo z dat nabidky."""
    loc = offer.get("location", "")
    price = offer.get("price", "")
    disc = offer.get("discount", "")
    return {
        "video_title": f"{loc} {disc}",
        "caption": (
            f"{loc} se slevou {disc}! Cena {price}. "
            f"Odkaz v biu/komentari. "
            f"#dovolena #sleva #cestovani #lastminute #{loc.split(',')[0].strip().replace(' ', '')} "
            f"#zajezd #travel #levnedovolene"
        ),
        "scenes": [
            {"duration": 3, "voiceover": f"Tohle musis videt. {loc} za zlomek ceny.",
             "visual_overlay": f"{loc}\n{disc}"},
            {"duration": 5, "voiceover": "Zapomen na drahe cestovky a hledani po internetu.",
             "visual_overlay": "STOP\ndrahym cestovkam"},
            {"duration": 5, "voiceover": f"Nasel jsem nabidku, kde to vyjde na {price}.",
             "visual_overlay": f"Cena\n{price}"},
            {"duration": 4, "voiceover": "Odkaz najdes v biu. Pospes si, mizi to rychle.",
             "visual_overlay": "Odkaz v biu"},
        ],
        "url": offer.get("url", ""),
    }


def _try_gemini(offer: dict) -> dict:
    genai.configure(api_key=config.GEMINI_API_KEY)
    user_prompt = (
        f"Nabídka:\n"
        f"- Lokalita: {offer['location']}\n"
        f"- Cena: {offer['price']}\n"
        f"- Sleva: {offer['discount']}\n"
        f"- Popis: {offer['description']}\n"
    )
    models = [config.GEMINI_MODEL] + [m for m in MODEL_FALLBACK if m != config.GEMINI_MODEL]
    last_err = None
    for model_name in models:
        for attempt in range(3):
            try:
                model = genai.GenerativeModel(
                    model_name,
                    system_instruction=SYSTEM_PROMPT,
                    generation_config={
                        "response_mime_type": "application/json",
                        "response_schema": RESPONSE_SCHEMA,
                        "temperature": 0.9,
                    },
                )
                resp = model.generate_content(user_prompt)
                script = json.loads(resp.text)
                script["url"] = offer.get("url", "")
                print(f"      LLM: {model_name}")
                return script
            except Exception as e:
                last_err = e
                msg = str(e)
                if "429" in msg or "quota" in msg.lower():
                    wait = 2 ** attempt
                    print(f"      {model_name} 429, retry za {wait}s...")
                    time.sleep(wait)
                else:
                    break  # jiny model nezkousej znovu se stejnou chybou
    raise last_err


def generate_script(offer: dict) -> dict:
    try:
        return _try_gemini(offer)
    except Exception as e:
        print(f"      LLM selhal ({e}). Pouzivam template fallback.")
        return _template_script(offer)
