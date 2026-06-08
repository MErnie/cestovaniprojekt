"""Web app (FastAPI) - rucni tvorba videi.

Spusteni lokalne:  uvicorn webapp.app:app --host 0.0.0.0 --port 8000
Pak otevri:        http://localhost:8000
"""
import html
import os
import sys
import traceback

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from pipeline import fetch_offer, produce

app = FastAPI(title="Video-tovarna")
OFFERS = {}   # cache: id -> offer
FEEDS = ["bomby", "nejpro", "zakladni"]

PAGE = """<!doctype html><html lang="cs"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Video-továrna</title>
<style>
:root{{color-scheme:dark}}
body{{font-family:system-ui,-apple-system,sans-serif;background:#0d1117;color:#e6edf3;margin:0;padding:24px;max-width:1100px;margin:0 auto}}
a{{color:#58a6ff;text-decoration:none}}
h1{{margin:0 0 4px}} .sub{{color:#8b949e;margin-bottom:20px}}
.tabs a{{display:inline-block;padding:6px 14px;margin-right:6px;background:#161b22;border:1px solid #30363d;border-radius:8px}}
.tabs a.act{{background:#1f6feb;border-color:#1f6feb;color:#fff}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px;margin-top:20px}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:12px;overflow:hidden;display:flex;flex-direction:column}}
.card img{{width:100%;height:150px;object-fit:cover;background:#21262d}}
.card .b{{padding:12px;flex:1;display:flex;flex-direction:column;gap:6px}}
.disc{{color:#3fb950;font-weight:700;font-size:20px}}
.price{{color:#e6edf3;font-weight:600}} .loc{{color:#8b949e;font-size:14px}}
.btn{{display:block;text-align:center;background:#1f6feb;color:#fff;padding:10px;border-radius:8px;border:0;font-size:15px;cursor:pointer;width:100%}}
.btn:hover{{background:#388bfd}}
textarea,select{{width:100%;background:#0d1117;color:#e6edf3;border:1px solid #30363d;border-radius:8px;padding:10px;font-size:15px;box-sizing:border-box}}
label{{display:block;margin:14px 0 6px;color:#8b949e}}
.box{{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:20px;margin-top:16px}}
video{{width:100%;max-width:360px;border-radius:12px;display:block;margin:10px 0}}
.err{{background:#3d1418;border:1px solid #f85149;color:#ffa198;padding:14px;border-radius:8px;white-space:pre-wrap}}
</style></head><body>{body}</body></html>"""


def render_page(body):
    return HTMLResponse(PAGE.format(body=body))


@app.get("/", response_class=HTMLResponse)
def index(feed: str = "bomby"):
    if feed not in FEEDS:
        feed = "bomby"
    try:
        offers = fetch_offer.list_offers(feed)
    except Exception as e:
        return render_page(f"<h1>Video-továrna</h1><div class='err'>Nepodařilo se načíst feed: {html.escape(str(e))}</div>")
    for o in offers:
        OFFERS[o["id"]] = o

    tabs = "".join(
        f"<a class='{'act' if f == feed else ''}' href='/?feed={f}'>{f}</a>" for f in FEEDS)
    cards = []
    for o in offers:
        img = (o.get("image_urls") or [""])[0]
        imgtag = f"<img src='{html.escape(img)}'>" if img else "<img>"
        cards.append(
            f"<div class='card'>{imgtag}<div class='b'>"
            f"<div class='disc'>{html.escape(o['discount'] or '')}</div>"
            f"<div class='price'>{html.escape(o['price'] or '')}</div>"
            f"<div class='loc'>{html.escape(o['location'] or o['title'])}</div>"
            f"<form action='/offer/{o['id']}' method='get' style='margin-top:auto'>"
            f"<button class='btn'>Vytvořit video</button></form>"
            f"</div></div>")
    body = (f"<h1>Video-továrna</h1><div class='sub'>Vyber dovolenou, ze které chceš video</div>"
            f"<div class='tabs'>{tabs}</div><div class='grid'>{''.join(cards)}</div>")
    return render_page(body)


@app.get("/offer/{offer_id}", response_class=HTMLResponse)
def offer_detail(offer_id: str):
    o = OFFERS.get(offer_id)
    if not o:
        return RedirectResponse("/")
    img = (o.get("image_urls") or [""])[0]
    imgtag = f"<img src='{html.escape(img)}' style='width:100%;max-width:300px;border-radius:12px'>" if img else ""
    body = f"""<a href="/">&larr; zpět na nabídky</a>
<h1>{html.escape(o['location'] or o['title'])}</h1>
<div class='sub'>{html.escape(o['discount'] or '')} &middot; {html.escape(o['price'] or '')}</div>
{imgtag}
<form action="/generate" method="post" class="box">
<input type="hidden" name="offer_id" value="{offer_id}">
<label>Co k tomu říct / tvůj úhel (AI to zapracuje do scénáře) — nepovinné</label>
<textarea name="notes" rows="3" placeholder="Např.: zdůrazni že je to ideální pro rodiny, all inclusive, last minute pryč za týden"></textarea>
<label>Hlas</label>
<select name="voice">
  <option value="edge:cs-CZ-AntoninNeural">Muž (edge, zdarma)</option>
  <option value="edge:cs-CZ-VlastaNeural">Žena (edge, zdarma)</option>
  <option value="elevenlabs">ElevenLabs (realistický)</option>
</select>
<label>Pozadí</label>
<select name="bg">
  <option value="video">Video b-roll (Pexels)</option>
  <option value="photo">Jen fotky + Ken Burns</option>
</select>
<div style="margin-top:18px"><button class="btn">Vygenerovat video &raquo;</button></div>
<div class='sub' style="margin-top:10px">Render trvá cca 1–3 minuty, vydrž na stránce.</div>
</form>"""
    return render_page(body)


@app.post("/generate", response_class=HTMLResponse)
def generate(offer_id: str = Form(...), notes: str = Form(""),
             voice: str = Form("edge:cs-CZ-AntoninNeural"), bg: str = Form("video")):
    o = OFFERS.get(offer_id)
    if not o:
        return RedirectResponse("/", status_code=303)

    # nastaveni dle UI (config se cte za behu)
    if voice == "elevenlabs":
        config.TTS_PROVIDER = "elevenlabs"
    else:
        config.TTS_PROVIDER = "edge"
        config.VOICE = voice.split(":", 1)[1]
    config.USE_VIDEO_BG = (bg == "video")

    try:
        result = produce.produce_video(o, notes)
    except Exception:
        return render_page(f"<a href='/'>&larr; zpět</a><h1>Chyba při generování</h1>"
                           f"<div class='err'>{html.escape(traceback.format_exc()[-1500:])}</div>")

    fname = os.path.basename(result["video"])
    body = f"""<a href="/">&larr; nové video</a><h1>Hotovo ✅</h1>
<div class='sub'>{html.escape(o['location'] or o['title'])}</div>
<video controls src="/video/{fname}"></video>
<div class="box"><label>Popisek + hashtagy</label>
<textarea rows="5">{html.escape(result['caption'])}</textarea></div>
<p><a class="btn" style="max-width:300px" href="/video/{fname}" download>Stáhnout .mp4</a></p>"""
    return render_page(body)


@app.get("/video/{fname}")
def serve_video(fname: str):
    path = config.OUTPUT_DIR / os.path.basename(fname)
    if not path.exists():
        return RedirectResponse("/")
    return FileResponse(str(path), media_type="video/mp4")
