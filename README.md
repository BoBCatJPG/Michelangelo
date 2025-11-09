# Michelangelo
Michelangelo, il bot di discord più zauddo che mai.

## Installation

1. Create virtual environment preventing libraries conflicts
    -   python -m venv <_env name_>

2. Switch environment
    - ./<_env name_>/Scripts/activate

3. Install Requirements
    - python -m pip install -r  requirements.txt

4. Create `.env` file to store discord bot token and other sensitive data:

```
discord_token=YOUR_TOKEN_HERE
```

5. Ensure FFmpeg is installed on your system (required for audio streaming). On Linux you can run:

```
sudo apt update && sudo apt install -y ffmpeg
```

## Commands

In qualsiasi canale testuale:

- `!play <url>`: riproduce l'audio del video YouTube
- `!play <parole chiave>`: effettua una ricerca YouTube (fuzzy) e riproduce il miglior risultato
- `!pause`: mette in pausa
- `!resume`: riprende l'audio
- `!stop`: ferma la riproduzione
- `!leave`: disconnette il bot dal canale vocale

## Run

Avvia il bot:

```
python main.py
```

## Docker

Build dell'immagine:

```
docker build -t michelangelo-bot .
```

Esecuzione (passando il token come env var):

```
docker run -d --name michelangelo --restart unless-stopped -e discord_token=YOUR_TOKEN michelangelo-bot
```

Con docker-compose:

```
discord_token=YOUR_TOKEN docker compose up -d --build
```

Aggiornare l'immagine dopo modifiche:

```
docker compose build michelangelo && docker compose up -d michelangelo
```

## Avvio automatico a boot (systemd)

Due opzioni:

1. Avviare direttamente lo script Python.
2. Avviare il container Docker.

### Esempio service (Docker)

Creare il file `/etc/systemd/system/michelangelo.service`:

```
[Unit]
Description=Michelangelo Discord Bot (Docker)
After=network-online.target docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/USER/Michelangelo
Environment="discord_token=YOUR_TOKEN"
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0
StandardOutput=journal
StandardError=journal
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Poi:

```
sudo systemctl daemon-reload
sudo systemctl enable michelangelo.service
sudo systemctl start michelangelo.service
```

### Esempio service (Python diretto)

```
[Unit]
Description=Michelangelo Discord Bot (Python diretto)
After=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/USER/Michelangelo
Environment="discord_token=YOUR_TOKEN"
ExecStart=/usr/bin/python /home/USER/Michelangelo/main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Sostituire `USER` con il proprio username.

Abilitare e avviare:

```
sudo systemctl daemon-reload
sudo systemctl enable michelangelo.service
sudo systemctl start michelangelo.service
```

## Notes

- Usa `bestaudio/best` da yt-dlp senza scaricare il file, streaming diretto.
- Riconnessioni automatiche FFmpeg abilitate per stream/live.
- Per il supporto voce di Discord è necessaria la libreria `PyNaCl` (già inclusa in `requirements.txt`). Se l'audio non parte assicurati che l'installazione sia riuscita.

That's all.
