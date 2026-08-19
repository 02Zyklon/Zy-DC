import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import static_ffmpeg

# Ativa o ffmpeg no ambiente
static_ffmpeg.add_paths()

# Configurações otimizadas do YT-DLP ignorando mídias com DRM
YTDL_OPTIONS = {
    'format': 'bestaudio[drm=none]/bestaudio/best',  # Ignora mídias com proteção DRM
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'scsearch',  # Busca no SoundCloud
    'source_address': '0.0.0.0'
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="play", description="Toca uma música no canal de voz")
    @app_commands.describe(busca="Nome da música ou link do SoundCloud")
    async def play(self, interaction: discord.Interaction, busca: str):
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

        loop = asyncio.get_event_loop()
        try:
            with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ytdl:
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(busca, download=False))
                
                if not data:
                    return await interaction.followup.send("❌ Nenhuma música encontrada.")

                # Seleciona a primeira entrada válida caso retorne uma lista de busca
                if 'entries' in data:
                    entries = [e for e in data['entries'] if e is not None]
                    if not entries:
                        return await interaction.followup.send("❌ Nenhuma faixa sem proteção DRM encontrada.")
                    data = entries[0]

                url = data.get('url')
                title = data.get('title', 'Música')

                if not url:
                    return await interaction.followup.send("❌ Não foi possível obter o link desta faixa (protegida por DRM).")

            audio_source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
            vc.play(audio_source)

            await interaction.followup.send(f"🎶 Tocando agora: **{title}**")

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao tentar processar a faixa: {e}")

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
