import discord
from discord.ext import commands
from discord import app_commands
import wavelink

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

   async def cog_load(self):
        # Conecta a um nó Lavalink v4 ativo e estável
        node = wavelink.Node(
            uri="https://lavalink.devamop.in:443", 
            password="youshallnotpass"
        )
        await wavelink.Pool.connect(nodes=[node], client=self.bot)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        print(f"🟢 Lavalink Conectado com Sucesso: {payload.node.identifier}")

    @app_commands.command(name="play", description="Toca músicas (YouTube, Spotify, SoundCloud)")
    @app_commands.describe(busca="Nome da música ou link")
    async def play(self, interaction: discord.Interaction, busca: str):
        await interaction.response.defer(thinking=True)

        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.followup.send("❌ Você precisa estar em um canal de voz!")

        player: wavelink.Player = interaction.guild.voice_client
        if not player:
            player = await interaction.user.voice.channel.connect(cls=wavelink.Player)

        # Busca a música em todas as plataformas sem travar
        tracks: wavelink.Search = await wavelink.Playable.search(busca)
        if not tracks:
            return await interaction.followup.send("❌ Nenhuma música encontrada.")

        track = tracks[0]

        if player.playing:
            await player.queue.put_wait(track)
            await interaction.followup.send(f"➕ Adicionado à fila: **{track.title}**")
        else:
            await player.play(track)
            await interaction.followup.send(f"🎶 Tocando agora: **{track.title}**")

    @app_commands.command(name="stop", description="Para e desconecta")
    async def stop(self, interaction: discord.Interaction):
        player: wavelink.Player = interaction.guild.voice_client
        if player:
            await player.disconnect()
            await interaction.response.send_message("🛑 Reprodução parada!")
        else:
            await interaction.response.send_message("❌ O bot não está em um canal de voz.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
