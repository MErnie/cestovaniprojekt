"""Krok 2: generovani scenare pres Gemini (striktni JSON)."""
import json
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


def generate_script(offer: dict) -> dict:
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        config.GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT,
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": RESPONSE_SCHEMA,
            "temperature": 0.9,
        },
    )
    user_prompt = (
        f"Nabídka:\n"
        f"- Lokalita: {offer['location']}\n"
        f"- Cena: {offer['price']}\n"
        f"- Sleva: {offer['discount']}\n"
        f"- Popis: {offer['description']}\n"
    )
    resp = model.generate_content(user_prompt)
    script = json.loads(resp.text)
    script["url"] = offer.get("url", "")
    return script
