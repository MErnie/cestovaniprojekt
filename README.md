# Video-továrna (faceless TikTok)

Plně automatický pipeline: **nabídka → scénář (OpenRouter) → hlas (edge-tts) → render (FFmpeg) → TikTok**.
Běží zdarma na GitHub Actions. Žádný server, žádný měsíční poplatek.

```
fetch_offer → generate_script → tts → render → publish_tiktok
```

## Co funguje hned (otestováno)

- Render vertikálního videa 1080×1920 s overlay textem a karaoke titulky (slovo po slově).
- **Video pozadí** — stock b-roll destinace (Pexels Video API), s fallbackem na fotky.
- **Ken Burns pohyb** (pomalý zoom/pan) na fotkách, když není video.
- **Víc fotek** — z Invia feedu + stock fotky destinace (město/pláž/atrakce) přes Pexels; každá scéna jiná.
- **Chunky karaoke titulky** — 3-slovní bloky, zvýraznění slova jak ho hlas vyslovuje.
- **Hudba do pozadí** — automaticky z `assets/music/` (loop + mix pod hlas).
- **Hlas:** edge-tts (český, zdarma, bez klíče).
- Scénář v JSON přes OpenRouter + template fallback.
- Spuštění denně cronem + ruční tlačítko.

## Hudba

Vlož jeden royalty-free track do `assets/music/` (viz `assets/music/README.md`).
Bez něj se video vyrenderuje jen s hlasem.

## Lokální test (volitelné)

```bash
pip install -r requirements.txt && cp .env.example .env
# v .env nech USE_SAMPLE_OFFER=1 a PUBLISH=0, vypln OPENROUTER_API_KEY
python main.py
# vysledek: output/video_*.mp4 + popisek output/video_*.txt
```

---

## Co musíš udělat TY (3 věci, které za tebe nikdo neudělá)

### 1. Nahrát projekt na GitHub

```bash
cd cestovaniprojekt
git init && git add . && git commit -m "init"
# vytvor prazdny repo na github.com, pak:
git remote add origin https://github.com/TVUJ_USER/cestovaniprojekt.git
git push -u origin main
```

### 2. Vyplnit klíče (GitHub → Settings → Secrets and variables → Actions)

**Secrets** (tajné):

| Secret | Kde získat | Povinné? |
|---|---|---|
| `OPENROUTER_API_KEY` | https://openrouter.ai/keys | ne (bez něj template scénář) |
| `PEXELS_API_KEY` | https://www.pexels.com/api/ (zdarma) | ne (bez něj jen fotky z feedu) |
| `TIKTOK_CLIENT_KEY` | TikTok Developer Portal (viz krok 3) | jen pro publikaci |
| `TIKTOK_CLIENT_SECRET` | TikTok Developer Portal | jen pro publikaci |
| `TIKTOK_REFRESH_TOKEN` | z OAuth flow (viz krok 3) | jen pro publikaci |

**Variables** (záložka Variables, ne Secrets):

| Variable | Hodnota |
|---|---|
| `FEED` | `bomby` (největší slevy) / `nejpro` / `zakladni` |
| `OPENROUTER_MODEL` | `deepseek/deepseek-v4-flash:free` (zdarma, čeština, JSON) |
| `SELECT_MODE` | `random` (náhodně z TOP) / `discount` (vždy největší sleva) |
| `DEST_FILTER` | prázdné = vše / např. `Chorvatsko` (jen daná destinace) |
| `USE_VIDEO_BG` | `1` video pozadí / `0` jen foto |
| `USE_SAMPLE_OFFER` | `1` pro test / `0` v ostrém provozu |
| `PUBLISH` | `0` jen render / `1` publikovat na TikTok |

### Výběr nabídky a rotace

Z feedu se vybírá podle `SELECT_MODE` (náhodně z TOP N nejvýhodnějších, nebo vždy
největší sleva), volitelně omezeno na `DEST_FILTER`. **Rotace je vždy zapnutá** —
zpracované nabídky se ukládají do `state/seen.json` a neopakují se, dokud se pool
nevyčerpá (pak se reset). Stav se po každém běhu commitne zpět do repa (proto má
workflow `permissions: contents: write`).

Hlas: **edge-tts** (český, zdarma, napevno). ElevenLabs vynechán — nemá češtinu.

Vše má fallback: chybí-li OpenRouter klíč, scénář se složí z dat (template); chybí-li Pexels, použijí se jen fotky z feedu. Pipeline se nikdy nezasekne na chybějícím klíči.

Invia feedy jsou veřejné XML URL (bez klíče), napevno v `pipeline/fetch_offer.py`. Žádný `AFFILIATE_API_KEY` není potřeba.

> Doporučení: první běh nech `USE_SAMPLE_OFFER=1`, `PUBLISH=0`. V Actions → spusť ručně (`Run workflow`) → stáhni výsledné video z artifactů. Až sedí, přepni na ostrý provoz.

### 3. TikTok — napojení (nejdelší krok, kvůli reviewu TikToku)

1. Registruj appku na https://developers.tiktok.com → přidej produkt **Content Posting API**, scope `video.publish`.
2. Zkopíruj `client_key` a `client_secret` do secrets.
3. **Schválení appky** — TikTok ji musí schválit (dny). Než schválí, funguje jen upload jako soukromý (`privacy_level=SELF_ONLY`, už nastaveno v `publish_tiktok.py`).
4. Jednorázově projdi OAuth a získej `refresh_token`:
   - Sestav authorize URL s `client_key`, `scope=video.publish`, `redirect_uri`.
   - Po přihlášení dostaneš `code` → vyměň ho na `/v2/oauth/token/` za `refresh_token`.
   - `refresh_token` vlož do secrets. Pipeline si z něj sama obnovuje access token.
5. Po schválení appky změň v `pipeline/publish_tiktok.py` `privacy_level` na `PUBLIC_TO_EVERYONE`.

---

## Krok 1 — Invia feed (HOTOVO)

Napojeno na tvoje 3 Invia XML feedy. Parser se sám adaptuje na strukturu feedu
(najde položky, namapuje pole, dopočítá slevu) a vybere nabídku s největší slevou.

Ověř strukturu feedu jedním příkazem:

```bash
FEED=bomby USE_SAMPLE_OFFER=0 python -m pipeline.fetch_offer --inspect
```

Vypíše dostupná pole první položky + jak se namapovala. Pokud by některé pole
chybělo (jiný název tagu), přidej ho do `FIELD_TAGS` v `pipeline/fetch_offer.py`.

## Úpravy designu (později)

- Barvy pozadí: `_PALETTE` v `pipeline/render.py`.
- Velikost/pozice titulků: `ASS_HEADER` v `pipeline/tts.py` (`Fontsize`, `MarginV`).
- Overlay text: `drawtext` ve `pipeline/render.py`.
- Hlas: secret/variable `VOICE` (např. `cs-CZ-VlastaNeural` ženský).
- 2 videa denně: přidej druhý `cron` řádek v `.github/workflows/daily.yml`.

## Náklady

Fixní 0 Kč. Při 1–2 videích denně se vejdeš do free tierů Gemini i GitHub Actions
(2000 min/měs). edge-tts, FFmpeg, TikTok API jsou zdarma.
