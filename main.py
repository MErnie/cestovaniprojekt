"""Orchestrace cele pipeline: nabidka -> scenar -> hlas -> render -> publikace."""
import json
import sys
from datetime import datetime

import config
from pipeline import fetch_offer, generate_script, tts, render


def run():
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"[1/5] Ziskavam nabidku...")
    offer = fetch_offer.get_offer()
    print(f"      {offer['location']} | {offer['price']} | {offer['discount']}")

    print(f"[2/5] Generuji scenar (Gemini)...")
    script = generate_script.generate_script(offer)
    print(f"      {len(script['scenes'])} scen | titulek: {script['video_title']}")

    print(f"[3/5] Generuji hlas (edge-tts)...")
    scene_assets = []
    for i, scene in enumerate(script["scenes"]):
        audio = str(config.OUTPUT_DIR / f"work/aud_{i}.mp3")
        subs = str(config.OUTPUT_DIR / f"work/sub_{i}.ass")
        config.OUTPUT_DIR.joinpath("work").mkdir(exist_ok=True)
        tts.synthesize(scene["voiceover"], audio, subs)
        scene_assets.append({"audio": audio, "subs": subs})

    print(f"[4/5] Renderuji video (FFmpeg)...")
    out = str(config.OUTPUT_DIR / f"video_{stamp}.mp4")
    render.build_video(script, scene_assets, offer, out)
    print(f"      Hotovo: {out}")

    # caption k videu (popisek + hashtagy + affiliate odkaz)
    with open(config.OUTPUT_DIR / f"video_{stamp}.txt", "w", encoding="utf-8") as f:
        f.write(script["caption"] + "\n\n" + script.get("url", ""))

    if config.PUBLISH:
        print(f"[5/5] Publikuji na TikTok...")
        from pipeline import publish_tiktok
        res = publish_tiktok.upload(out, script["caption"])
        print(f"      publish_id: {res['publish_id']}")
    else:
        print(f"[5/5] PUBLISH=0 -> preskakuji publikaci. Video je v output/.")

    return out


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"CHYBA: {e}", file=sys.stderr)
        sys.exit(1)
