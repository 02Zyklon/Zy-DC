import discord
from discord.ext import commands
from discord import app_commands
import wavelink

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # Cria uma tarefa em background para conectar assim que o bot estiver online no Discord
        self.bot.loop.create_task(self.connect_nodes())

    async def connect_nodes(self):
        # Aguarda o bot carregar o ID do usuário/cliente no Discord
        await self.bot.wait_until_ready()

        nodes = [
            wavelink.Node(
                identifier="meu-lavalink",
                uri="https://meu-lavalink-q57d.onrender.com",
                password="zyklon123",
                retries=10
            )
        ]
        
        try:
            await wavelink.Pool.connect(nodes=nodes, client=self.bot, cache_capacity=100)
        except Exception as e:
            print(f"⚠️ Erro ao conectar ao Lavalink: {e}")

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        print(f"🟢 Lavalink Conectado com Sucesso: {payload.node.identifier}")

    @app_commands.command(name="play", description="Toca uma música no canal de voz")
    @app_commands.describe(busca="Nome da música ou link")
    async def play(self, interaction: discord.Interaction, busca: str):
        await interaction.response.defer(thinking=True)

        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.followup.send("❌ Você precisa estar em um canal de voz!")

        voice_channel = interaction.user.voice.channel

        if not interaction.guild.voice_client:
            player: wavelink.Player = await voice_channel.connect(cls=wavelink.Player)
        else:
            player: wavelink.Player = interaction.guild.voice_client
            if player.channel != voice_channel:
                await player.move_to(voice_channel)

        tracks = await wavelink.Playable.search(busca, source=wavelink.TrackSource.SoundCloud)
        if not tracks:
            return await interaction.followup.send("❌ Nenhuma música encontrada.")

        track = tracks[0]

        if player.playing or not player.queue.is_empty:
            await player.queue.put_wait(track)
            await interaction.followup.send(f"➕ Adicionado à fila: **{track.title}**")
        else:
            await player.play(track)
            await interaction.followup.send(f"🎶 Tocando agora: **{track.title}**")

    @app_commands.command(name="skip", description="Pula a música atual")
    async def skip(self, interaction: discord.Interaction):
        player: wavelink.Player = interaction.guild.voice_client
        if player and (player.playing or player.paused):
            await player.skip(force=True)
            await interaction.response.send_message("⏭️ Música pulada!")
        else:
            await interaction.response.send_message("❌ Nenhuma música tocando no momento.")

    @app_commands.command(name="stop", description="Para a música e desconecta o bot")
    async def stop(self, interaction: discord.Interaction):
        player: wavelink.Player = interaction.guild.voice_client
        if player:
            await player.disconnect()
            await interaction.response.send_message("🛑 Bot desconectado!")
        else:
            await interaction.response.send_message("❌ O bot não está em um canal de voz.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
