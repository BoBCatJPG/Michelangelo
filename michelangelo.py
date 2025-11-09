import os
import asyncio
import re
from difflib import SequenceMatcher
from collections import deque
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
        self.queues: dict[int, deque] = {}  # Code per ogni server
        # yt_dlp options: best audio only
        yt_dl_options = {"format": "bestaudio/best"}
        self.ytdl = yt_dlp.YoutubeDL(yt_dl_options) # type: ignore
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
                    
                    # Inizializza la coda se non esiste
                    if guild_id not in self.queues:
                        self.queues[guild_id] = deque()

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

                    # Aggiungi alla coda
                    self.queues[guild_id].append((song_url, chosen_title))
                    
                    # Se non sta già riproducendo, inizia
                    if not voice_client.is_playing():
                        await self.play_next(guild_id, message.channel)
                    else:
                        await message.channel.send(f"Aggiunto alla coda: {chosen_title}")
                        
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
                guild_id = message.guild.id
                vc = self.voice_clients.get(guild_id)
                if vc and (vc.is_playing() or vc.is_paused()):
                    # Svuota la coda e ferma la riproduzione
                    if guild_id in self.queues:
                        self.queues[guild_id].clear()
                    vc.stop()
                    await message.channel.send("Nooo minchia sul più bello.")
                else:
                    await message.channel.send("Guarda che non c'è nulla da fermare.")

            #skip
            if message.content.startswith("!skip"):
                guild_id = message.guild.id
                vc = self.voice_clients.get(guild_id)
                if vc and (vc.is_playing() or vc.is_paused()):
                    # Controlla se ci sono altre canzoni in coda
                    if guild_id in self.queues and len(self.queues[guild_id]) > 0:
                        vc.stop()  # Ferma la canzone corrente, play_next verrà chiamato automaticamente
                        await message.channel.send("Sti minchiat skippamu.")
                    else:
                        vc.stop()
                        await message.channel.send("Skippatu, ma nun c'è nenti autru in coda.")
                else:
                    await message.channel.send("Ma che skippo se non sta sonando niente?")

            #queue - mostra la coda
            if message.content.startswith("!queue"):
                guild_id = message.guild.id
                if guild_id not in self.queues or len(self.queues[guild_id]) == 0:
                    await message.channel.send("La coda è vuota.")
                else:
                    queue_list = "\n".join([f"{i+1}. {title}" for i, (_, title) in enumerate(self.queues[guild_id])])
                    await message.channel.send(f"**Coda:**\n{queue_list}")

            #leave
            if message.content.startswith("!leave"):
                vc = self.voice_clients.get(message.guild.id)
                if vc and vc.is_connected():
                    await vc.disconnect()
                    await message.channel.send("Ti salutai.")
                    del self.voice_clients[message.guild.id]
                else:
                    await message.channel.send("Viri ca già mi ni ii.")

    async def play_next(self, guild_id: int, channel):
        """Riproduce la prossima canzone nella coda"""
        if guild_id not in self.queues or len(self.queues[guild_id]) == 0:
            return
        
        voice_client = self.voice_clients.get(guild_id)
        if not voice_client or not voice_client.is_connected():
            return
        
        # Prendi la prossima canzone dalla coda
        song_url, chosen_title = self.queues[guild_id].popleft()
        
        audio_source = discord.FFmpegPCMAudio(
            song_url,
            before_options=self.ffmpeg_before_options,
            options=self.ffmpeg_options
        )
        
        # Callback per quando la canzone finisce
        def after_playing(error):
            if error:
                print(f"Errore durante la riproduzione: {error}")
            # Pianifica la prossima canzone
            coro = self.play_next(guild_id, channel)
            asyncio.run_coroutine_threadsafe(coro, self.client.loop)
        
        voice_client.play(audio_source, after=after_playing)
        await channel.send(f"Ora sta sonando: {chosen_title}")

    def run(self):
        self.client.run(self.token)  # type: ignore



