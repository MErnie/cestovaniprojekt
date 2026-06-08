"""Orchestrace automatu: nabidka -> (produce engine) -> publikace."""
import sys

import config
from pipeline import fetch_offer, produce


def run():
    print("[1/3] Ziskavam nabidku...")
    offer = fetch_offer.get_offer()
    print(f"      {offer['location']} | {offer['price']} | {offer['discount']}")

    print("[2/3] Vyrabim video...")
    result = produce.produce_video(offer, progress=lambda s: print(f"      {s}"))
    out = result["video"]
    print(f"      Hotovo: {out}")

    if config.PUBLISH:
        print("[3/3] Publikuji na TikTok...")
        from pipeline import publish_tiktok
        res = publish_tiktok.upload(out, result["caption"])
        print(f"      publish_id: {res['publish_id']}")
    else:
        print("[3/3] PUBLISH=0 -> preskakuji publikaci. Video je v output/.")
    return out


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"CHYBA: {e}", file=sys.stderr)
        sys.exit(1)
