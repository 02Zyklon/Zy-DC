import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio

# Configurações do yt-dlp para extrair apenas o áudio com melhor qualidade
YTDL_OPTIONS = {
    'cookiefile': 'cookies.txt',
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
    'default_search': 'ytsearch',  # Mantém a busca padronizada
    'source_address': '0.0.0.0',
    # --- BURLAR O BLOQUEIO DE BOT ---
    'nocheckwebpage': True,
    'youtube_include_dash_manifest': False,
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'web'], # Utiliza o cliente mobile do Android que ignora o PoToken
            'skip': ['hls', 'dash']
        }
    }
}

# Configurações do FFmpeg para otimização do streaming de voz
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues = {}  # Fila de músicas por ID da guilda

    def get_queue(self, guild_id: int):
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

    def play_next(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild_id)
        if len(queue) > 0:
            next_song = queue.pop(0)
            voice_client = interaction.guild.voice_client
            
            if voice_client and voice_client.is_connected():
                source = discord.FFmpegPCMAudio(next_song['url'], **FFMPEG_OPTIONS)
                voice_client.play(
                    source, 
                    after=lambda e: self.play_next(interaction)
                )
                # Envia mensagem no canal informando a próxima música
                asyncio.run_coroutine_threadsafe(
                    interaction.channel.send(f"🎵 Tocando agora: **{next_song['title']}**"),
                    self.bot.loop
                )

    @app_commands.command(name="play", description="Toca uma música ou adiciona à fila (URL ou busca)")
    @app_commands.describe(busca="Nome da música ou link do YouTube")
    async def play(self, interaction: discord.Interaction, busca: str):
        await interaction.response.defer()

        # 1. Verifica se o usuário está em um canal de voz
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.followup.send("❌ Você precisa estar em um canal de voz para usar este comando!")

        voice_channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client

        # 2. Conecta ao canal de voz se ainda não estiver conectado
        if voice_client is None:
            voice_client = await voice_channel.connect()
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)

        # 3. Extrai as informações da música usando yt-dlp em uma thread separada
        loop = asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{busca}", download=False))
            if 'entries' in data and len(data['entries']) > 0:
                data = data['entries'][0]
            elif 'entries' in data and not data['entries']:
                return await interaction.followup.send("❌ Nenhuma música encontrada com esse termo.")
        except Exception as e:
            return await interaction.followup.send(f"⚠️ Erro ao buscar a música: `{str(e)}`")

        song_info = {
            'url': data['url'],
            'title': data.get('title', 'Música sem título'),
            'duration': data.get('duration', 0)
        }

        queue = self.get_queue(interaction.guild_id)

        # 4. Se o bot já estiver tocando algo, adiciona à fila. Caso contrário, toca imediatamente.
        if voice_client.is_playing() or voice_client.is_paused():
            queue.append(song_info)
            await interaction.followup.send(f"➕ Adicionado à fila: **{song_info['title']}**")
        else:
            source = discord.FFmpegPCMAudio(song_info['url'], **FFMPEG_OPTIONS)
            voice_client.play(source, after=lambda e: self.play_next(interaction))
            await interaction.followup.send(f"🎶 Tocando agora: **{song_info['title']}**")

    @app_commands.command(name="skip", description="Pula a música que está tocando atualmente")
    async def skip(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await interaction.response.send_message("⏭️ Música pulada!")
        else:
            await interaction.response.send_message("❌ Não há nenhuma música tocando no momento.")

    @app_commands.command(name="stop", description="Para a música, limpa a fila e desconecta o bot")
    async def stop(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client:
            self.queues[interaction.guild_id] = []
            await voice_client.disconnect()
            await interaction.response.send_message("🛑 Reprodução parada e desconectado do canal!")
        else:
            await interaction.response.send_message("❌ O bot não está em um canal de voz.")

    @app_commands.command(name="queue", description="Mostra a fila atual de músicas")
    async def queue(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild_id)
        if not queue:
            return await interaction.response.send_message("📄 A fila de músicas está vazia!")

        descricao = "\n".join([f"**{i+1}.** {song['title']}" for i, song in enumerate(queue[:10])])
        embed = discord.Embed(title="📋 Fila de Músicas", description=descricao, color=discord.Color.blue())
        if len(queue) > 10:
            embed.set_footer(text=f"E mais {len(queue) - 10} música(s) na fila.")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
