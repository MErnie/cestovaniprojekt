# Nasazení web appky na VPS

Web app = dashboard, kde si vybereš dovolenu, připíšeš úhel pohledu a vygeneruješ
video. Běží pořád, dostupná z prohlížeče i z mobilu.

Engine je stejný jako u automatu (`pipeline/`). Automat (GitHub Actions) běží dál
nezávisle — obojí může fungovat zároveň.

## Co potřebuješ

- VPS s Linuxem (Ubuntu 22/24). Stačí nejmenší (1 vCPU, 1–2 GB RAM). Např. Hetzner,
  DigitalOcean, Contabo — řádově pár dolarů měsíčně.
- Tvoje API klíče (OpenRouter, Pexels, případně ElevenLabs).

## Nejjednodušší cesta — Docker

```bash
# na VPS (přihlášený přes SSH):
sudo apt update && sudo apt install -y docker.io docker-compose-plugin git
git clone https://github.com/MErnie/cestovaniprojekt.git
cd cestovaniprojekt

# vytvor .env s klici (zkopiruj sablonu a vypln)
cp .env.example .env
nano .env        # vypln OPENROUTER_API_KEY, PEXELS_API_KEY, pripadne ELEVENLABS_*

# spusti
sudo docker compose up -d --build
```

Hotovo. Appka běží na `http://IP_TVEHO_SERVERU:8000`.

Restart serveru appku spustí sám (`restart: unless-stopped`). Update kódu:

```bash
cd cestovaniprojekt && git pull && sudo docker compose up -d --build
```

## Bez Dockeru (alternativa)

```bash
sudo apt update && sudo apt install -y python3-pip ffmpeg fonts-dejavu-core git
git clone https://github.com/MErnie/cestovaniprojekt.git && cd cestovaniprojekt
pip install -r requirements.txt
cp .env.example .env && nano .env       # vypln klice

# nacti .env a spust
set -a; . ./.env; set +a
uvicorn webapp.app:app --host 0.0.0.0 --port 8000
```

Pro běh na pozadí (i po odhlášení) použij `screen`, `tmux` nebo systemd službu.

## Doménu a HTTPS (volitelné)

Pro pěknou adresu (např. `https://tvujweb.cz`) dej před appku **Caddy** nebo
**nginx** jako reverzní proxy — Caddy vyřídí HTTPS certifikát automaticky.

## Bezpečnost

Appka nemá přihlášení — kdokoliv se znalostí IP ji může používat. Pro ostrý provoz:
- omez přístup firewallem na svoji IP, nebo
- dej před ni proxy s heslem (basic auth v Caddy/nginx).

Klíče jsou jen v `.env` na serveru, nikdy se necommitují (jsou v `.gitignore`).
