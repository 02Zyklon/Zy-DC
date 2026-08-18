import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

# Configuração do Spotify (Opcional - usa credenciais se existirem no .env)
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

sp = None
if SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET:
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET
        ))
    except Exception as e:
        print(f"⚠️ Erro ao inicializar o Spotify: {e}")

# Opções do yt-dlp para extrair áudio de alta qualidade
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    # Bypass para evitar o bloqueio de bot do YouTube em servidores cloud
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'ios'],
            'skip': ['webpage', 'configs']
        }
    }
}

# Opções do FFmpeg para manter o stream estável sem travamentos
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()

        # Trata links do Spotify se o cliente estiver configurado
        if sp and "spotify.com" in url:
            if "track" in url:
                try:
                    track_info = sp.track(url)
                    url = f"{track_info['name']} {track_info['artists'][0]['name']}"
                except Exception:
                    pass

        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)


class Musica(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="play", description="Toca uma música no canal de voz (busca no YouTube ou link do Spotify).")
    @app_commands.describe(busca="Nome da música ou link do YouTube/Spotify")
    async def play(self, interaction: discord.Interaction, busca: str):
        await interaction.response.defer()

        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.followup.send("❌ Você precisa estar em um canal de voz para tocar música!")

        canal_voz = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client

        if voice_client is None:
            voice_client = await canal_voz.connect()
        elif voice_client.channel != canal_voz:
            await voice_client.move_to(canal_voz)

        try:
            player = await YTDLSource.from_url(busca, loop=self.bot.loop, stream=True)

            if not voice_client.is_playing():
                voice_client.play(player, after=lambda e: print(f'Erro no reprodução: {e}') if e else None)
                
                embed = discord.Embed(
                    title="🎵 Tocando Agora",
                    description=f"**[{player.title}]({player.url})**",
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"Pedido por {interaction.user.display_name}")
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("⚠️ O bot já está tocando uma música no momento!")

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao reproduzir o áudio: `{e}`")

    @app_commands.command(name="stop", description="Para a música e desconecta o bot da call.")
    async def stop(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client

        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
            await interaction.response.send_message("⏹️ Música interrompida e bot desconectado da call.")
        else:
            await interaction.response.send_message("❌ O bot não está em nenhum canal de voz no momento.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Musica(bot))
