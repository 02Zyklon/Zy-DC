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
        """Conecta ao servidor do Lavalink."""
        await self.bot.wait_until_ready()
        
        # URI corrigido para http:// (Lavalink lida com WebSocket internamente)
        node = wavelink.Node(
            identifier="ZyklonRenderNode",
            uri="http://lavalink-qvir.onrender.com:80",
            password="$1N;ZyklonSS"
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

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        """Toca a próxima música da fila automaticamente ao finalizar a atual."""
        player: wavelink.Player = payload.player
        if not player:
            return

        if not player.queue.is_empty:
            next_track = await player.queue.get_wait()
            await player.play(next_track)

    @commands.command(name="play", aliases=["p"], help="Toca uma música do YouTube ou Spotify")
    async def play(self, ctx: commands.Context, *, busca: str):
        if not ctx.author.voice:
            return await ctx.send("❌ Você precisa estar em um canal de voz para tocar músicas!")

        if not ctx.voice_client:
            vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = ctx.voice_client

        try:
            # Busca faixas usando o provedor padrão do Wavelink
            results: wavelink.Search = await wavelink.Playable.search(busca)
            if not results:
                return await ctx.send("❌ Nenhuma música encontrada com esse termo.")

            # Trata se for uma playlist ou apenas faixas individuais
            if isinstance(results, wavelink.Playlist):
                track = results.tracks[0]
                for t in results.tracks:
                    await vc.queue.put_wait(t)
                await ctx.send(f"📚 Adicionada a playlist **{results.name}** ({len(results.tracks)} músicas) à fila!")
            else:
                track = results[0]
                await vc.queue.put_wait(track)

            if not vc.playing:
                first_track = await vc.queue.get_wait()
                await vc.play(first_track)
                await ctx.send(f"🎵 Tocando agora: **{track.title}** - `{track.author}`")
            elif not isinstance(results, wavelink.Playlist):
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
