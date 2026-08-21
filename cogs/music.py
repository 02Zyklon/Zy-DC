import discord
from discord.ext import commands
from discord import app_commands
import wavelink
import asyncio
import logging

# Configuração de logs para diagnóstico avançado de erros
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MusicBotBlindado")

class MusicBlindado(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Executa a conexão ao nó Lavalink assim que o Cog carregar
        self.bot.loop.create_task(self.conectar_node())

    async def conectar_node(self):
        """Conecta o bot ao seu servidor Lavalink privado (Docker)."""
        await self.bot.wait_until_ready()
        
        # Conexão ajustada para o seu servidor privado (application.yml)
        node = wavelink.Node(
            identifier="ZyklonNode",
            uri="http://127.0.0.1:8080",
            password="zyklon123"
        )
        try:
            await wavelink.Pool.connect(nodes=[node], client=self.bot)
            logger.info("✅ Conexão com o nó Lavalink privado estabelecida com sucesso!")
        except Exception as e:
            logger.error(f"❌ Erro crítico ao conectar ao Lavalink: {e}")

    # ==========================================
    # TRATAMENTO DE EVENTOS DE ÁUDIO E ERROS
    # ==========================================

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        """Trata o fim de uma faixa e toca a próxima da fila automaticamente."""
        player: wavelink.Player = payload.player
        if not player:
            return

        # Se houver músicas na fila, toca a próxima
        if not player.queue.is_empty:
            proxima_faixa = player.queue.get()
            try:
                await player.play(proxima_faixa)
            except Exception as e:
                logger.error(f"Erro ao reproduzir próxima faixa da fila: {e}")
                if player.home:
                    await player.home.send(f"⚠️ **Erro de reprodução:** Não foi possível tocar `{proxima_faixa.title}`. Pulando...")
                await self.on_wavelink_track_end(payload)
        else:
            # Fila vazia: aguarda 2 minutos antes de desconectar para economizar recursos
            await asyncio.sleep(120)
            if not player.is_playing() and player.queue.is_empty:
                await player.disconnect()
                if player.home:
                    await player.home.send("💤 **Desconectado por inatividade:** A fila terminou e o canal ficou ocioso.")

    @commands.Cog.listener()
    async def on_wavelink_node_closed(self, node: wavelink.Node, disconnected: list[wavelink.Player]):
        """Recuperação de desastres caso o servidor Lavalink caia."""
        logger.warning(f"⚠️ Nó Lavalink '{node.identifier}' foi desconectado!")

    # ==========================================
    # CHECAGENS DE SEGURANÇA (MIDDLEWARES)
    # ==========================================

    async def validar_conexao_voz(self, interaction: discord.Interaction) -> tuple[bool, str, discord.VoiceChannel]:
        """Aplica todas as regras de validação do canal de voz antes de processar qualquer comando."""
        if not interaction.user.voice or not interaction.user.voice.channel:
            return False, "❌ **Acesso Negado:** Você precisa estar conectado a um canal de voz!", None

        canal_usuario = interaction.user.voice.channel
        meu_player: wavelink.Player = interaction.guild.voice_client

        if meu_player and meu_player.channel != canal_usuario:
            return False, f"❌ **Conflito:** Já estou tocando áudio no canal {meu_player.channel.mention}!", None

        # Validação de permissões do bot no canal de voz
        perm = canal_usuario.permissions_for(interaction.guild.me)
        if not perm.connect or not perm.speak:
            return False, "❌ **Permissão Insuficiente:** Não tenho permissão para **Conectar** ou **Falar** neste canal de voz!", None

        return True, "", canal_usuario

    # ==========================================
    # COMANDOS DO BOT DE MÚSICA
    # ==========================================

    @app_commands.command(name="play", description="Toca uma música (SoundCloud, Spotify ou Link Direto).")
    async def play(self, interaction: discord.Interaction, busca: str):
        await interaction.response.defer()

        # 1. Validações de Voz
        sucesso, erro_msg, canal_voz = await self.validar_conexao_voz(interaction)
        if not sucesso:
            await interaction.followup.send(erro_msg, ephemeral=True)
            return

        # 2. Obtenção ou Criação do Player
        player: wavelink.Player = interaction.guild.voice_client
        if not player:
            try:
                player = await canal_voz.connect(cls=wavelink.Player)
                player.home = interaction.channel  # Define o canal de texto principal para respostas
            except Exception as e:
                await interaction.followup.send(f"❌ **Erro de Conexão:** Falha ao entrar no canal de voz: `{e}`")
                return

        # 3. Busca de Músicas com Proteção contra Falhas
        try:
            # Tratamento para utilizar a busca via SoundCloud habilitada no seu Lavalink
            query = busca if busca.startswith(("http://", "https://")) else f"scsearch:{busca}"
            tracks: wavelink.Search = await wavelink.Playable.search(query)
            if not tracks:
                await interaction.followup.send(f"🔍 **Nenhum resultado:** Nenhuma faixa encontrada para `{busca}`.")
                return
        except Exception as e:
            await interaction.followup.send("⚠️ **Erro na API de Busca:** Não foi possível carregar os dados desta música ou playlist.")
            logger.error(f"Erro na busca do Wavelink: {e}")
            return

        # 4. Tratamento de Playlists vs Faixa Única
        if isinstance(tracks, wavelink.Playlist):
            for track in tracks.tracks:
                await player.queue.put_wait(track)
            await interaction.followup.send(f"📚 **Playlist Adicionada:** **{tracks.name}** ({len(tracks.tracks)} faixas adicionadas à fila).")
        else:
            track = tracks[0]
            if player.is_playing():
                await player.queue.put_wait(track)
                await interaction.followup.send(f"➕ **Adicionado à Fila (#{player.queue.count}):** `{track.title}` - `{track.author}`")
            else:
                await player.play(track)
                await interaction.followup.send(f"🎶 **Tocando Agora:** `{track.title}` - `{track.author}`")

    @app_commands.command(name="skip", description="Pula a música atual para a próxima da fila.")
    async def skip(self, interaction: discord.Interaction):
        player: wavelink.Player = interaction.guild.voice_client
        
        if not player or not player.is_playing():
            await interaction.response.send_message("❌ **Aviso:** Nenhuma música está sendo reproduzida no momento.", ephemeral=True)
            return

        sucesso, erro_msg, _ = await self.validar_conexao_voz(interaction)
        if not sucesso:
            await interaction.response.send_message(erro_msg, ephemeral=True)
            return

        faixa_atual = player.current.title if player.current else "Música"
        await player.skip_to()
        await interaction.response.send_message(f"⏭️ **Faixa Pulada:** `{faixa_atual}` foi interrompida.")

    @app_commands.command(name="pause", description="Pausa ou retoma a música atual.")
    async def pause(self, interaction: discord.Interaction):
        player: wavelink.Player = interaction.guild.voice_client

        if not player or not player.current:
            await interaction.response.send_message("❌ **Aviso:** Nenhuma música ativa para pausar/despausar.", ephemeral=True)
            return

        sucesso, erro_msg, _ = await self.validar_conexao_voz(interaction)
        if not sucesso:
            await interaction.response.send_message(erro_msg, ephemeral=True)
            return

        estado_novo = not player.paused
        await player.pause(estado_novo)
        status_str = "⏸️ **Pausado**" if estado_novo else "▶️ **Retomado**"
        await interaction.response.send_message(f"{status_str} a reprodução de `{player.current.title}`.")

    @app_commands.command(name="stop", description="Para a música, limpa a fila e desconecta o bot.")
    async def stop(self, interaction: discord.Interaction):
        player: wavelink.Player = interaction.guild.voice_client

        if not player:
            await interaction.response.send_message("❌ **Aviso:** O bot não está conectado a nenhum canal de voz.", ephemeral=True)
            return

        sucesso, erro_msg, _ = await self.validar_conexao_voz(interaction)
        if not sucesso:
            await interaction.response.send_message(erro_msg, ephemeral=True)
            return

        player.queue.clear()
        await player.disconnect()
        await interaction.response.send_message("🛑 **Sessão Encerrada:** Fila limpa e bot desconectado com sucesso.")

    @app_commands.command(name="queue", description="Exibe as próximas músicas presentes na fila.")
    async def queue(self, interaction: discord.Interaction):
        player: wavelink.Player = interaction.guild.voice_client

        if not player or (player.queue.is_empty and not player.current):
            await interaction.response.send_message("📜 **Fila Vazia:** Não há nenhuma música programada.", ephemeral=True)
            return

        embed = discord.Embed(title="📜 Fila de Reprodução", color=discord.Color.purple())
        
        if player.current:
            embed.add_field(
                name="🎶 Tocando Agora", 
                value=f"`{player.current.title}` - `{player.current.author}`", 
                inline=False
            )

        if not player.queue.is_empty:
            lista_faixas = []
            for idx, track in enumerate(player.queue[:10], start=1):
                lista_faixas.append(f"`{idx}.` **{track.title}** - `{track.author}`")
            
            embed.add_field(name="📋 Próximas da Fila", value="\n".join(lista_faixas), inline=False)
            if player.queue.count > 10:
                embed.set_footer(text=f"E mais {player.queue.count - 10} faixa(s) na fila...")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicBlindado(bot))
