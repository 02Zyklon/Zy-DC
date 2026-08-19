import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio

# Configurações do YT-DLP para extrair o áudio direto
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
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0'
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="play", description="Toca uma música diretamente no canal de voz")
    @app_commands.describe(busca="Nome da música ou link")
    async def play(self, interaction: discord.Interaction, busca: str):
        await interaction.response.defer(thinking=True)

        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.followup.send("❌ Você precisa estar em um canal de voz!")

        voice_channel = interaction.user.voice.channel

        # Conecta ao canal de voz usando a API nativa do Discord
        if not interaction.guild.voice_client:
            vc = await voice_channel.connect()
        else:
            vc = interaction.guild.voice_client
            if vc.channel != voice_channel:
                await vc.move_to(voice_channel)

        if vc.is_playing():
            return await interaction.followup.send("⚠️ Já tem uma música tocando! Pare a anterior primeiro.")

        # Busca o áudio via yt-dlp
        loop = asyncio.get_event_loop()
        try:
            with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ytdl:
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(busca, download=False))
                
                if 'entries' in data:
                    data = data['entries'][0]

                url = data['url']
                title = data.get('title', 'Música')

            # Toca o stream de áudio via FFmpeg
            audio_source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
            vc.play(audio_source)

            await interaction.followup.send(f"🎶 Tocando agora: **{title}**")

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao tentar tocar a música: {e}")

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
