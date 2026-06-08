"""Sdileny engine: z nabidky vyrobi video. Pouziva main.py (automat) i web app (rucne)."""
from datetime import datetime

import config
from pipeline import generate_script, tts, render, stock


def produce_video(offer: dict, notes: str = "", progress=lambda s: None) -> dict:
    """offer -> hotove video. progress(text) je volitelny callback pro UI/log."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    work = config.OUTPUT_DIR / "work"
    work.mkdir(parents=True, exist_ok=True)

    progress("Generuji scenar...")
    script = generate_script.generate_script(offer, notes)
    n = len(script["scenes"])

    progress(f"Generuji hlas ({config.TTS_PROVIDER})...")
    scene_assets = []
    for i, scene in enumerate(script["scenes"]):
        audio = str(work / f"aud_{i}.mp3")
        subs = str(work / f"sub_{i}.ass")
        tts.synthesize(scene["voiceover"], audio, subs)
        scene_assets.append({"audio": audio, "subs": subs})

    progress("Stahuji pozadi a renderuji...")
    loc = offer.get("location", "")
    feed_imgs = list(offer.get("image_urls", []))
    hotel_image = feed_imgs[0] if feed_imgs else ""   # fotka hotelu z feedu
    images = feed_imgs + stock.get_stock_images(loc, n=max(n - len(feed_imgs), 0) + 2)
    videos = stock.get_stock_videos(loc, n=n) if config.USE_VIDEO_BG else []

    out = str(config.OUTPUT_DIR / f"video_{stamp}.mp4")
    render.build_video(script, scene_assets, images, videos, out,
                       hotel_image=hotel_image, stars=offer.get("stars", ""))

    caption_path = str(config.OUTPUT_DIR / f"video_{stamp}.txt")
    with open(caption_path, "w", encoding="utf-8") as f:
        f.write(script["caption"] + "\n\n" + script.get("url", ""))

    progress("Hotovo.")
    return {"video": out, "caption_file": caption_path, "caption": script["caption"],
            "script": script, "stamp": stamp}
