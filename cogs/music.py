import logging
import discord
from discord.ext import commands
import wavelink

logger = logging.getLogger("Zy-DC")

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        """Inicia a conexão com o node do Lavalink ao carregar o Cog."""
        self.bot.loop.create_task(self.conectar_node())

    async def conectar_node(self):
        """Conecta ao servidor privado do Lavalink no Render."""
        await self.bot.wait_until_ready()
        
        node = wavelink.Node(
            identifier="ZyklonRenderNode",
            uri="https://lavalink-qvir.onrender.com",
            password="youshallnotpass"
        )
        try:
            await wavelink.Pool.connect(nodes=[node], client=self.bot)
            logger.info("✅ Conectado ao Lavalink do Render com sucesso!")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar no Lavalink: {e}")

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        """Evento acionado quando o Node do Lavalink está pronto."""
        logger.info(f"🚀 Node Lavalink '{payload.node.identifier}' totalmente operacional!")

    @commands.command(name="play", aliases=["p"], help="Toca uma música do YouTube ou Spotify")
    async def play(self, ctx: commands.Context, *, busca: str):
        if not ctx.author.voice:
            return await ctx.send("❌ Você precisa estar em um canal de voz para tocar músicas!")

        if not ctx.voice_client:
            vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = ctx.voice_client

        try:
            tracks: wavelink.Search = await wavelink.Playable.search(busca)
            if not tracks:
                return await ctx.send("❌ Nenhuma música encontrada com esse termo.")

            track = tracks[0] if isinstance(tracks, list) else tracks.tracks[0]
            await vc.queue.put_wait(track)

            if not vc.playing:
                await vc.play(vc.queue.get())
                await ctx.send(f"🎵 Tocando agora: **{track.title}** - `{track.author}`")
            else:
                await ctx.send(f"➕ Adicionado à fila: **{track.title}**")

        except Exception as e:
            logger.error(f"Erro no comando play: {e}")
            await ctx.send(f"❌ Erro ao processar a música: `{e}`")

    @commands.command(name="stop", aliases=["sair"], help="Para a música e desconecta o bot")
    async def stop(self, ctx: commands.Context):
        vc: wavelink.Player = ctx.voice_client
        if vc:
            await vc.disconnect()
            await ctx.send("⏹️ Reprodução parada e desconectado do canal.")
        else:
            await ctx.send("❌ O bot não está conectado a nenhum canal de voz.")

    @commands.command(name="skip", aliases=["s"], help="Pula para a próxima música")
    async def skip(self, ctx: commands.Context):
        vc: wavelink.Player = ctx.voice_client
        if vc and vc.playing:
            await vc.skip()
            await ctx.send("⏭️ Música pulada!")
        else:
            await ctx.send("❌ Não há nenhuma música tocando para pular.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
