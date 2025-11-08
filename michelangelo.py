import os
import asyncio
import re
from difflib import SequenceMatcher
import discord
import yt_dlp
from dotenv import load_dotenv

class Michelangelo:
    def __init__(self):
        load_dotenv()
        self.token = os.getenv("discord_token")
        if not self.token:
            raise RuntimeError("Variabile d'ambiente 'discord_token' mancante.")

        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)

        self.voice_clients: dict[int, discord.VoiceClient] = {}
        # yt_dlp options: best audio only
        yt_dl_options = {"format": "bestaudio/best"}
        self.ytdl = yt_dlp.YoutubeDL(yt_dl_options)
        # FFmpeg options: drop video, attempt reconnects for livestreams
        self.ffmpeg_before_options = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
        self.ffmpeg_options = "-vn"

        @self.client.event
        async def on_ready():
            print(f'{self.client.user} è connesso!')
        
        @self.client.event
        async def on_message(message):

            # play (URL o ricerca per somiglianza)
            if message.content.startswith("!play"):
                try:
                    arg_str = message.content[len("!play"):].strip()
                    if not arg_str:
                        await message.channel.send("Uso: !play <url YouTube | parole chiave>")
                        return

                    # Ensure author is in a voice channel
                    if not message.author.voice or not message.author.voice.channel:
                        await message.channel.send("Devi essere in un canale vocale.")
                        return

                    guild_id = message.guild.id
                    voice_client = self.voice_clients.get(guild_id)
                    if not (voice_client and voice_client.is_connected()):
                        voice_client = await message.author.voice.channel.connect()
                        self.voice_clients[guild_id] = voice_client

                    loop = asyncio.get_event_loop()
                    is_url = re.match(r'https?://', arg_str) is not None
                    chosen_title = arg_str

                    if is_url:
                        data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(arg_str, download=False))
                        song_url = data.get('url')
                        chosen_title = data.get('title', arg_str)
                    else:
                        search_query = arg_str
                        search_term = f"ytsearch5:{search_query}"
                        search_data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(search_term, download=False))
                        entries = (search_data or {}).get('entries', [])
                        if not entries:
                            await message.channel.send("Nessun risultato trovato.")
                            return
                        def sim(title: str) -> float:
                            return SequenceMatcher(None, search_query.lower(), title.lower()).ratio()
                        best = max(entries, key=lambda e: sim(e.get('title', '')))
                        song_url = best.get('url')
                        chosen_title = best.get('title', 'Titolo sconosciuto')

                    if not song_url:
                        await message.channel.send("Non sono riuscito a ottenere l'audio.")
                        return

                    audio_source = discord.FFmpegPCMAudio(
                        song_url,
                        before_options=self.ffmpeg_before_options,
                        options=self.ffmpeg_options
                    )
                    if voice_client.is_playing():
                        voice_client.stop()
                    voice_client.play(audio_source)
                    if is_url:
                        await message.channel.send(f"Questa è nmostru (URL): {chosen_title}")
                    else:
                        await message.channel.send(f"Questa è nmostru (ricerca): {chosen_title}")
                except Exception as e:
                    print(e)
                    await message.channel.send(f"no mbare non me la fa partire: {e}")
            
            #pause
            if message.content.startswith("!pause"):
                vc = self.voice_clients.get(message.guild.id)
                if vc and vc.is_playing():
                    vc.pause()
                    await message.channel.send("Misi in pausa.")
                else:
                    await message.channel.send("Nessun audio in riproduzione.")

            #resume
            if message.content.startswith("!resume"):
                vc = self.voice_clients.get(message.guild.id)
                if vc and vc.is_paused():
                    vc.resume()
                    await message.channel.send("Unnerumu...ah si.")
                else:
                    await message.channel.send("Ma frate non c'è nulla in pausa.")
            #stop
            if message.content.startswith("!stop"):
                vc = self.voice_clients.get(message.guild.id)
                if vc and (vc.is_playing() or vc.is_paused()):
                    vc.stop()
                    await message.channel.send("Nooo minchia sul più bello.")
                else:
                    await message.channel.send("Guarda che non c'è nulla da fermare.")

            #leave
            if message.content.startswith("!leave"):
                vc = self.voice_clients.get(message.guild.id)
                if vc and vc.is_connected():
                    await vc.disconnect()
                    await message.channel.send("Ti salutai.")
                    del self.voice_clients[message.guild.id]
                else:
                    await message.channel.send("Viri ca già mi ni ii.")


    def run(self):
        self.client.run(self.token)


