import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import os

# 1. Configuração Principal (Tenta YouTube com Cookies e Emulação de Android)
YTDL_OPTIONS_YT = {
    'format': 'bestaudio[drm=none]/bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
    'source_address': '0.0.0.0',
    'extractor_retries': 3,
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'web'],
            'skip': ['dash', 'hls']
        }
    }
}

# 2. Configuração de Fallback (SoundCloud - Altamente estável contra bloqueios)
YTDL_OPTIONS_SC = {
    'format': 'bestaudio[drm=none]/bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'scsearch',
    'source_address': '0.0.0.0'
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def extrair_audio(self, busca: str):
        """Tenta buscar no YouTube primeiro; se falhar, tenta no SoundCloud."""
        loop = asyncio.get_event_loop()
        
        # Tentativa 1: YouTube
        try:
            with yt_dlp.YoutubeDL(YTDL_OPTIONS_YT) as ytdl:
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(busca, download=False))
                if data and 'entries' in data:
                    entries = [e for e in data['entries'] if e is not None and e.get('url')]
                    if entries:
                        return entries[0]['url'], entries[0].get('title', 'Música'), "YouTube"
                elif data and data.get('url'):
                    return data['url'], data.get('title', 'Música'), "YouTube"
        except Exception:
            pass  # Falha silenciosa para ativar o Fallback

        # Tentativa 2: SoundCloud (Fallback)
        try:
            with yt_dlp.YoutubeDL(YTDL_OPTIONS_SC) as ytdl:
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(busca, download=False))
                if data and 'entries' in data:
                    entries = [e for e in data['entries'] if e is not None and e.get('url')]
                    if entries:
                        return entries[0]['url'], entries[0].get('title', 'Música'), "SoundCloud"
                elif data and data.get('url'):
                    return data['url'], data.get('title', 'Música'), "SoundCloud"
        except Exception:
            pass

        return None, None, None

    @app_commands.command(name="play", description="Toca uma música no canal de voz")
    @app_commands.describe(busca="Nome da música ou link")
    async def play(self, interaction: discord.Interaction, busca: str):
        # ⚠️ Previne o "O aplicativo não respondeu" instantaneamente
        await interaction.response.defer(thinking=True)

        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.followup.send("❌ Você precisa estar em um canal de voz!")

        voice_channel = interaction.user.voice.channel

        if not interaction.guild.voice_client:
            vc = await voice_channel.connect()
        else:
            vc = interaction.guild.voice_client
            if vc.channel != voice_channel:
                await vc.move_to(voice_channel)

        if vc.is_playing():
            return await interaction.followup.send("⚠️ Já existe uma música tocando!")

        # Busca com Fallback
        url, title, fonte = await self.extrair_audio(busca)

        if not url:
            return await interaction.followup.send("❌ Não foi possível carregar esta faixa em nenhuma das fontes disponíveis.")

        try:
            audio_source = discord.FFmpegPCMAudio(url, executable="ffmpeg", **FFMPEG_OPTIONS)
            vc.play(audio_source)
            await interaction.followup.send(f"🎶 Tocando agora via **{fonte}**: **{title}**")
        except Exception as e:
            await interaction.followup.send(f"❌ Erro na execução do FFmpeg: `{e}`")

    @app_commands.command(name="stop", description="Para a música e desconecta")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_connected():
            await vc.disconnect()
            await interaction.response.send_message("🛑 Bot desconectado!")
        else:
            await interaction.response.send_message("❌ O bot não está em um canal de voz.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
