"""Orchestrace cele pipeline: nabidka -> scenar -> hlas -> render -> publikace."""
import json
import sys
from datetime import datetime

import config
from pipeline import fetch_offer, generate_script, tts, render, stock


def run():
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"[1/5] Ziskavam nabidku...")
    offer = fetch_offer.get_offer()
    print(f"      {offer['location']} | {offer['price']} | {offer['discount']}")

    print(f"[2/5] Generuji scenar...")
    script = generate_script.generate_script(offer)
    n = len(script["scenes"])
    print(f"      {n} scen | titulek: {script['video_title']}")

    print(f"[3/5] Generuji hlas ({config.TTS_PROVIDER})...")
    scene_assets = []
    for i, scene in enumerate(script["scenes"]):
        audio = str(config.OUTPUT_DIR / f"work/aud_{i}.mp3")
        subs = str(config.OUTPUT_DIR / f"work/sub_{i}.ass")
        config.OUTPUT_DIR.joinpath("work").mkdir(exist_ok=True)
        tts.synthesize(scene["voiceover"], audio, subs)
        scene_assets.append({"audio": audio, "subs": subs})

    print(f"[4/5] Renderuji video (FFmpeg)...")
    loc = offer.get("location", "")
    # fotky: z feedu + stock fotky destinace (fallback kdyz neni video)
    images = list(offer.get("image_urls", []))
    images += stock.get_stock_images(loc, n=max(n - len(images), 0) + 2)
    # video pozadi (preferovane) - stock b-roll destinace
    videos = stock.get_stock_videos(loc, n=n) if config.USE_VIDEO_BG else []
    print(f"      pozadi: {len(videos)} videi, {len(images)} fotek")
    out = str(config.OUTPUT_DIR / f"video_{stamp}.mp4")
    render.build_video(script, scene_assets, images, videos, out)
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
