import os
import asyncio
import datetime
import random
import json
import discord
from discord.ext import commands
from discord import app_commands
from keep_alive import keep_alive
import economy  # 🟢 Importação do módulo unificado de Economia

# =========================================================
# CONFIGURAÇÃO E INICIALIZAÇÃO
# =========================================================
from google import genai
from openai import OpenAI

# Inicializa os clientes das IAs lendo as chaves do ambiente
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY")) if os.getenv("GEMINI_API_KEY") else None
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ID do seu servidor no Discord (Guild)
GUILD_ID = 1434359569718706320

# Arquivo de armazenamento de configurações de registro
DB_REGISTRO = "config_registro.json"

def load_json(file_path, default):
    if not os.path.exists(file_path):
        return default
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)
    
    # Tornar as Views persistentes (não somem/quebram ao reiniciar)
    bot.add_view(PainelTicketView())
    bot.add_view(BotaoFecharTicket())
    bot.add_view(ViewBotaoComprar())
    
    print(f"🤖 Bot online e sincronizado com sucesso como: {bot.user}")

# =========================================================
# ⚡ COMANDO DE SINCRONIZAÇÃO DINÂMICA
# =========================================================
@bot.command(name="sync")
@commands.is_owner()
async def sync(ctx: commands.Context, spec: str = None):
    """Sincroniza os comandos Slash dinamicamente (Uso: !sync ou !sync guild)"""
    if spec == "guild":
        synced = await bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"✅ **{len(synced)}** comandos sincronizados neste servidor!")
    else:
        synced = await bot.tree.sync()
        await ctx.send(f"🌐 **{len(synced)}** comandos sincronizados globalmente!")

# =========================================================
# 🛒 SISTEMA DE VENDAS & TICKET INDIVIDUAL POR CANAL
# =========================================================
class BotaoComprar(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Comprar / Abrir Ticket", 
            style=discord.ButtonStyle.green, 
            emoji="🛒",
            custom_id="btn_abrir_ticket_compra_individual"
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        canal_origem = interaction.channel.name

        nome_ticket = f"ticket-{user.name}-{canal_origem}".lower().replace(" ", "-")
        
        ticket_existente = discord.utils.get(guild.text_channels, name=nome_ticket)
        if ticket_existente:
            return await interaction.response.send_message(
                f"❌ Você já possui um ticket aberto para este produto: {ticket_existente.mention}", 
                ephemeral=True
            )

        cat_atendimento = discord.utils.get(guild.categories, name="🛠️ 𝑨𝑻𝑬𝑵𝑫𝑰𝑑𝑬𝑵𝑻𝑶 ›") or interaction.channel.category

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        canal_ticket = await guild.create_text_channel(
            name=nome_ticket,
            category=cat_atendimento,
            overwrites=overwrites
        )

        embed_ticket = discord.Embed(
            title=f"🛒 Atendimento de Compra — {canal_origem.upper()}",
            description=(
                f"Olá {user.mention}, seja bem-vindo!\n\n"
                f"📌 **Produto Selecionado:** `{canal_origem}`\n"
                "Aguarde um momento. Um atendente ou administrador irá te responder em breve."
            ),
            color=discord.Color.green()
        )
        embed_ticket.set_footer(text=f"Usuário ID: {user.id}")

        await canal_ticket.send(content=f"{user.mention}", embed=embed_ticket, view=BotaoFecharTicket())
        await interaction.response.send_message(f"✅ Ticket criado com sucesso! Acesse: {canal_ticket.mention}", ephemeral=True)


class ViewBotaoComprar(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(BotaoComprar())


@bot.tree.command(name="fixar_produto", description="📌 Envia a imagem e detalhes do produto com o botão de ticket.")
@app_commands.checks.has_permissions(administrator=True)
async def fixar_produto(
    interaction: discord.Interaction, 
    titulo: str, 
    descricao: str, 
    url_imagem: str
):
    await interaction.response.defer(ephemeral=True)

    embed = discord.Embed(
        title=titulo,
        description=descricao.replace("\\n", "\n"),
        color=discord.Color.red()
    )
    embed.set_image(url=url_imagem)

    await interaction.channel.send(embed=embed, view=ViewBotaoComprar())
    await interaction.followup.send("✅ Anúncio do produto fixado com sucesso neste canal!", ephemeral=True)

# =========================================================
# 🪙 SISTEMA DE GOLDS (ECONOMIA CONECTADA AO economy.py)
# =========================================================
@bot.tree.command(name="carteira", description="Exibe o seu saldo atual de Golds.")
async def carteira(interaction: discord.Interaction, usuario: discord.Member = None):
    target = usuario or interaction.user
    saldo = economy.get_gold(target.id)

    embed = discord.Embed(
        title="🏛️ Banco Central Zy",
        description=f"Detalhamento financeiro de {target.mention}",
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="💰 Saldo em Golds", value=f"`{saldo:,}` 📀", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="daily", description="Resgate sua recompensa diária de Golds.")
async def daily(interaction: discord.Interaction):
    reward = random.randint(250, 600)
    novo_saldo = economy.add_gold(interaction.user.id, reward)

    embed = discord.Embed(
        title="🎁 Recompensa Diária Coletada!",
        description=f"Você recebeu **+{reward:,}** Golds 📀!",
        color=discord.Color.green()
    )
    embed.add_field(name="Novo Saldo", value=f"`{novo_saldo:,}` 📀")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="pay", description="Transfira Golds para outro usuário.")
async def pay(interaction: discord.Interaction, destino: discord.Member, quantia: int):
    if quantia <= 0 or destino.bot or destino.id == interaction.user.id:
        return await interaction.response.send_message("❌ Operação ou valor inválido!", ephemeral=True)

    if not economy.remove_gold(interaction.user.id, quantia):
        return await interaction.response.send_message("❌ Saldo insuficiente!", ephemeral=True)

    economy.add_gold(destino.id, quantia)
    await interaction.response.send_message(f"💸 **{interaction.user.mention}** enviou **{quantia:,}** Golds 📀 para **{destino.mention}**!")

import os
import json
import discord

@bot.tree.command(name="rank", description="🏆 Exibe o TOP 10 dos membros mais ricos do servidor.")
async def rank(interaction: discord.Interaction):
    # 🚨 1. Responde à API imediatamente para não dar timeout
    await interaction.response.defer()

    NOME_ARQUIVO = "banco.json"  # 👈 Altere aqui se o seu arquivo tiver outro nome (ex: "usuarios.json" ou "pets.json")

    try:
        # 📂 2. Se o arquivo não existir, ele cria um arquivo novo e vazio na hora
        if not os.path.exists(NOME_ARQUIVO):
            with open(NOME_ARQUIVO, "w", encoding="utf-8") as f:
                json.dump({}, f)

        # 📖 3. Lê o arquivo JSON
        with open(NOME_ARQUIVO, "r", encoding="utf-8") as f:
            try:
                dados = json.load(f)
            except json.JSONDecodeError:
                dados = {}

        # Se a base estiver vazia
        if not dados:
            return await interaction.followup.send("⚠️ Nenhum registro de moedas/Golds encontrado ainda.")

        # 📊 4. Ordena os usuários pelo saldo (suporta tanto {'user_id': 100} quanto {'user_id': {'golds': 100}})
        ranking_ordenado = sorted(
            dados.items(),
            key=lambda x: x[1].get("golds", 0) if isinstance(x[1], dict) else x[1],
            reverse=True
        )[:10]

        # 📜 5. Monta o Embed do Ranking
        embed = discord.Embed(
            title="🏆 𝑹𝑨𝑵𝑲 𝑫𝑶𝑺 𝑴𝑨𝑰𝑺 𝑹𝑰𝑪𝑶𝑺",
            description="Confira os membros com maior saldo de Golds no servidor:\n",
            color=discord.Color.gold()
        )

        posicoes = ["🥇", "🥈", "🥉", "4º", "5º", "6º", "7º", "8º", "9º", "10º"]

        for index, (user_id, info) in enumerate(ranking_ordenado):
            membro = interaction.guild.get_member(int(user_id))
            nome = membro.display_name if membro else f"Usuário ({user_id})"
            
            golds = info.get("golds", 0) if isinstance(info, dict) else info

            embed.add_field(
                name=f"{posicoes[index]} {nome}",
                value=f"💰 `{golds:,}` Golds",
                inline=False
            )

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ Ocorreu um erro ao carregar o rank: `{e}`")

# =========================================================
# 🎮 JOGO DA VELHA
# =========================================================
class TicTacToeButton(discord.ui.Button):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="", row=y)
        self.x, self.y = x, y

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToeView = self.view
        if view.board[self.y][self.x] != 0:
            return await interaction.response.send_message("❌ Posição ocupada!", ephemeral=True)
        if interaction.user != view.current_player:
            return await interaction.response.send_message("❌ Não é sua vez!", ephemeral=True)

        if view.current_player == view.player_x:
            self.style, self.label = discord.ButtonStyle.danger, "X"
            view.board[self.y][self.x] = 1
            view.current_player = view.player_o
            content = f"Vez de: {view.player_o.mention} (O)"
        else:
            self.style, self.label = discord.ButtonStyle.primary, "O"
            view.board[self.y][self.x] = 2
            view.current_player = view.player_x
            content = f"Vez de: {view.player_x.mention} (X)"

        self.disabled = True
        winner = view.check_winner()

        if winner is not None:
            content = f"🎉 **{view.player_x.mention} (X) Venceu!**" if winner == 1 else (
                f"🎉 **{view.player_o.mention} (O) Venceu!**" if winner == 2 else "👔 **Empate!**"
            )
            for child in view.children: child.disabled = True
            view.stop()

        await interaction.response.edit_message(content=content, view=view)

class TicTacToeView(discord.ui.View):
    def __init__(self, player_x: discord.Member, player_o: discord.Member):
        super().__init__(timeout=180)
        self.player_x, self.player_o, self.current_player = player_x, player_o, player_x
        self.board = [[0]*3 for _ in range(3)]
        for y in range(3):
            for x in range(3):
                self.add_item(TicTacToeButton(x, y))

    def check_winner(self):
        for i in range(3):
            if self.board[i][0] == self.board[i][1] == self.board[i][2] != 0: return self.board[i][0]
            if self.board[0][i] == self.board[1][i] == self.board[2][i] != 0: return self.board[0][i]
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != 0: return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != 0: return self.board[0][2]
        if all(cell != 0 for row in self.board for cell in row): return 0
        return None

@bot.tree.command(name="velha", description="Desafie um amigo para o Jogo da Velha!")
async def velha(interaction: discord.Interaction, oponente: discord.Member):
    if oponente.bot or oponente.id == interaction.user.id:
        return await interaction.response.send_message("❌ Oponente inválido!", ephemeral=True)
    view = TicTacToeView(player_x=interaction.user, player_o=oponente)
    await interaction.response.send_message(f"🎮 **Jogo da Velha!**\n{interaction.user.mention} (X) vs {oponente.mention} (O)", view=view)

# =========================================================
# 🔐 SISTEMA DE REGISTRO POR PALAVRA-PASSE
# =========================================================
@bot.tree.command(name="set_chat_filtracao", description="[ADMIN] Define o canal de filtração.")
@app_commands.checks.has_permissions(administrator=True)
async def set_chat_filtracao(interaction: discord.Interaction, canal: discord.TextChannel):
    cfg = load_json(DB_REGISTRO, {"canal_filtracao": None, "palavras": {}})
    cfg["canal_filtracao"] = canal.id
    save_json(DB_REGISTRO, cfg)
    await interaction.response.send_message(f"✅ Canal de filtração definido para: {canal.mention}")

@bot.tree.command(name="set_passe_cargo", description="[ADMIN] Registra palavra-passe para um cargo.")
@app_commands.checks.has_permissions(administrator=True)
async def set_passe_cargo(interaction: discord.Interaction, palavra_passe: str, cargo: discord.Role):
    cfg = load_json(DB_REGISTRO, {"canal_filtracao": None, "palavras": {}})
    cfg["palavras"][palavra_passe.lower()] = cargo.id
    save_json(DB_REGISTRO, cfg)
    await interaction.response.send_message(f"✅ Palavra-passe `{palavra_passe.lower()}` associada ao cargo **{cargo.name}**.")

@bot.event
async def on_member_join(member: discord.Member):
    cfg = load_json(DB_REGISTRO, {})
    canal_id = cfg.get("canal_filtracao")
    if canal_id:
        canal = member.guild.get_channel(canal_id)
        if canal:
            await canal.send(f"👋 Bem-vindo(a) {member.mention}! Digite a **palavra-passe** de acesso aqui no chat para liberar seu cargo.")

@bot.event
async def on_message(message: discord.Message):
    await bot.process_commands(message)

    if message.author.bot:
        return

    cfg = load_json(DB_REGISTRO, {})
    canal_id = cfg.get("canal_filtracao")

    if canal_id and message.channel.id == canal_id:
        texto = message.content.strip().lower()
        palavras = cfg.get("palavras", {})

        cargo_id = None
        for chave, cid in palavras.items():
            if chave in texto:
                cargo_id = cid
                break

        if cargo_id:
            cargo = message.guild.get_role(cargo_id)
            if cargo:
                try:
                    await message.author.add_roles(cargo)
                    await message.channel.send(f"🎉 {message.author.mention}, cargo **{cargo.name}** entregue!", delete_after=8)
                except discord.Forbidden:
                    pass

        try:
            await message.delete()
        except discord.Forbidden:
            pass

# ==========================================
# 🎫 SISTEMA DE TICKETS GENERALIZADO
# ==========================================
class BotaoFecharTicket(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Fechar Ticket", style=discord.ButtonStyle.red, custom_id="fechar_ticket_btn")
    async def fechar_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Este ticket será apagado em **5 segundos**...", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.channel.delete()

class MenuOpcoesTicket(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Suporte Geral", description="Dúvidas ou ajuda com o servidor", emoji="❓", value="Suporte Geral"),
            discord.SelectOption(label="Atendimento / Compras", description="Falar sobre planos ou serviços", emoji="🛒", value="Atendimento / Compras"),
            discord.SelectOption(label="Denúncia / Moderação", description="Reportar um membro ou problema", emoji="🛡️", value="Denúncia / Moderação"),
        ]
        super().__init__(placeholder="Selecione o motivo do seu atendimento...", min_values=1, max_values=1, options=options, custom_id="select_ticket_categoria")

    async def callback(self, interaction: discord.Interaction):
        categoria_nome = self.values[0]
        guild = interaction.guild
        membro = interaction.user

        nome_canal = f"ticket-{membro.name.lower().replace(' ', '-')}"

        canal_existente = discord.utils.get(guild.channels, name=nome_canal)
        if canal_existente:
            await interaction.response.send_message(f"⚠️ Você já tem um ticket aberto em {canal_existente.mention}!", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            membro: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        canal_ticket = await guild.create_text_channel(
            name=nome_canal,
            overwrites=overwrites,
            reason=f"Ticket aberto por {membro.name}"
        )

        embed_ticket = discord.Embed(
            title=f"🎫 Central de Atendimento | {categoria_nome}",
            description=f"Olá {membro.mention}, obrigado por entrar em contato!\nDescreva detalhadamente a sua solicitação. Nossa equipe irá te atender em breve.\n\nClique no botão abaixo quando desejar encerrar este atendimento.",
            color=discord.Color.brand_green()
        )
        embed_ticket.set_footer(text=f"Usuário ID: {membro.id}")

        await canal_ticket.send(embed=embed_ticket, view=BotaoFecharTicket())
        await interaction.response.send_message(f"✅ Seu ticket foi criado em {canal_ticket.mention}!", ephemeral=True)

class PainelTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MenuOpcoesTicket())

@bot.tree.command(name="painelticket", description="Envia o painel fixo de abertura de tickets no canal")
@app_commands.checks.has_permissions(administrator=True)
async def painelticket(interaction: discord.Interaction):
    embed = discord.Embed(
        title="💬 Central de Suporte & Atendimento",
        description="Precisa de ajuda, suporte ou quer tratar de algum assunto privado?\n\nEscolha uma categoria no menu suspenso abaixo para abrir um **canal de atendimento privado** com a nossa equipe.",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Zy-Bot • Sistema de Atendimento Automático")
    await interaction.response.send_message(embed=embed, view=PainelTicketView())
# ==========================================================
# 🏗️ SETUP DO SERVIDOR
# ==========================================================

@bot.tree.command(name="setup_servidor", description="✨ Cria a estrutura de canais com visual Serif/Bold impecável.")
@app_commands.checks.has_permissions(administrator=True)
async def setup_servidor(interaction: discord.Interaction):
    """Cria a estrutura de canais com todos os nomes estilizados corretamente."""
    
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild

    try:
        # 🚨 1. FILTRAÇÃO
        cat_filtracao = await guild.create_category("🚨 𝑭𝑰𝑳𝑻𝑹𝑨𝑪̧𝑨̃𝑶 ›")
        await guild.create_text_channel("🚨・filtração", category=cat_filtracao)

        # 📌 2. INGRESSO / INSTITUCIONAL
        cat_ing = await guild.create_category("📌 𝑾𝑬𝑳𝑪𝑶𝑴𝑬 ›")
        c_regras = await guild.create_text_channel("📜・diretrizes", category=cat_ing)
        await guild.create_text_channel("📢・anuncios", category=cat_ing)
        await guild.create_text_channel("🎟・cargos-free", category=cat_ing)

        embed_regras = discord.Embed(
            title="📜 𝑫𝑰𝑑𝑬𝑻𝑑𝑰𝒁𝑬𝑺 𝑬 𝑑𝑬𝑮𝑑𝑨𝑺",
            description=(
                "**1. Respeito Mútuo:** Conduta limpa e sem ofensas gratuitas.\n"
                "**2. Divulgação:** Proibida sem autorização prévia da moderação.\n"
                "**3. Compras & Suporte:** Use o canal de ticket para realizar seus pedidos."
            ),
            color=discord.Color.dark_red()
        )
        await c_regras.send(embed=embed_regras)

        # 🛒 3. ZYKLON VENDAS
        cat_loja = await guild.create_category("🛒 𝒁𝒀𝑲𝑳𝑶𝑵 𝑽𝑬𝑵𝑫𝑨𝑺 ›")
        await guild.create_text_channel("💎・dimas-via-token", category=cat_loja)
        await guild.create_text_channel("🎁・presentes-e-passes", category=cat_loja)
        await guild.create_text_channel("🤖・bots-e-automaticos", category=cat_loja)
        await guild.create_text_channel("👑・contas-ff", category=cat_loja)
        await guild.create_text_channel("❤️・likes-ff", category=cat_loja)
        await guild.create_text_channel("🛒・referencias", category=cat_loja)
        await guild.create_text_channel("📜・termos-e-uso", category=cat_loja)

        # 🛠️ 4. ATENDIMENTO & TICKETS
        cat_ticket = await guild.create_category("🛠️ 𝑨𝑻𝑬𝑵𝑫𝑰𝑑𝑬𝑵𝑻𝑶 ›")
        await guild.create_text_channel("🎫・abrir-ticket", category=cat_ticket)

        # 💬 5. COMUNIDADE
        cat_dev = await guild.create_category("⚙ 𝑵𝑬𝑑𝑼𝑺 ┃ 𝑪𝑶𝑴𝑼𝑵𝑰𝑫𝑨𝑫𝑬 ›")
        await guild.create_text_channel("💬・chat-geral", category=cat_dev)
        await guild.create_text_channel("🤖・comandos-bot", category=cat_dev)
        await guild.create_text_channel("💻・dev-lounge", category=cat_dev)
        await guild.create_text_channel("🤝・parcerias", category=cat_dev)

        # 🏆 6. GUILDA
        cat_ff = await guild.create_category("🏆 𝑶𝑺 𝑨𝑴𝑶𝑺𝑻𝑑𝑨𝑫𝑰𝑵𝑯𝑶𝑺 ›")
        await guild.create_text_channel("💬・chat-central", category=cat_ff)
        await guild.create_text_channel("📌・avisos-linha-de-frente", category=cat_ff)
        await guild.create_text_channel("🔒・chat-lideres-amd", category=cat_ff)

        for i in range(1, 11):
            await guild.create_voice_channel(f"🎙・{i}ª-Line", user_limit=5, category=cat_ff)

        # 🔊 7. CALLS PÚBLICAS
        cat_calls = await guild.create_category("🔊 𝑪𝑨𝑳𝑳𝑺 ┃ 𝑷𝑼𝑩𝑳𝑰𝑪𝑨𝑺 ›")
        await guild.create_voice_channel("🎧・Main-Lobby", category=cat_calls)
        await guild.create_voice_channel("🎯・Squad-01", user_limit=4, category=cat_calls)
        await guild.create_voice_channel("🎯・Squad-02", user_limit=4, category=cat_calls)
        await guild.create_voice_channel("☕・Resenha-01", category=cat_calls)

        # 🔒 8. ADMIN PANEL
        cat_admin = await guild.create_category("🔒 𝑨𝑫𝑑𝑰𝑵 𝑷𝑨𝑵𝑬𝑳 ›")
        await guild.create_text_channel("📡・bot-logs", category=cat_admin)
        await guild.create_text_channel("🛡・staff-only", category=cat_admin)

        await interaction.followup.send("✨ **Servidor gerado com sucesso e visual 100% corrigido!**", ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"❌ **Erro no setup:** `{e}`", ephemeral=True)

# ⚔️ 9. RPG YGGDRASIL
        cat_rpg = await guild.create_category("⚔️ 𝑹𝑷𝑮 𝒀𝑮𝑮𝑫𝑑𝑨𝑺𝑰𝑳 ›")
        
        c_como_jogar = await guild.create_text_channel("📜・como-jogar", category=cat_rpg)
        await guild.create_text_channel("🔥・foguinho-e-cassino", category=cat_rpg)
        await guild.create_text_channel("🐉・masmorras", category=cat_rpg)
        await guild.create_text_channel("🐾・meu-pet", category=cat_rpg)
        await guild.create_text_channel("🏆・ostentacao-rank", category=cat_rpg)

        # Mensagem explicativa no canal de tutorial
        embed_rpg_guia = discord.Embed(
            title="⚔️ 𝑩𝑬𝑴-𝑽𝑰𝑵𝑫𝑶 𝑨𝑶 𝑹𝑷𝑮 𝒀𝑮𝑮𝑫𝑑𝑨𝑺𝑰𝑳",
            description=(
                "Conquiste moedas, evolua seus pets e explore as profundezas da Yggdrasil!\n\n"
                "📌 **Comandos Principais:**\n"
                "• `/daily` — Colete sua recompensa diária de Golds.\n"
                "• `/foguinho` — Teste sua sorte no jogo do foguinho.\n"
                "• `/masmorra` — Enfrente monstros e ganhe recompensas.\n"
                "• `/pet` — Cuide do seu companheiro de batalha.\n"
                "• `/carteira` e `/rank` — Veja seu saldo e os mais ricos do servidor.\n"
                "• `/velha` — Desafie outro membro para um X1."
            ),
            color=discord.Color.dark_purple()
        )
        embed_rpg_guia.set_footer(text="Aproveite e boa sorte nas batalhas!")
        await c_como_jogar.send(embed=embed_rpg_guia)

# ==========================================
# ⚔️ SETUP ISOLADO DO RPG YGGDRASIL
# ==========================================
@bot.tree.command(name="setup_rpg", description="⚔️ Cria apenas a categoria e os canais do RPG Yggdrasil.")
@app_commands.checks.has_permissions(administrator=True)
async def setup_rpg(interaction: discord.Interaction):
    """Cria isoladamente a estrutura do RPG Yggdrasil."""
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild

    # 🛑 1. Verifica se a categoria já existe para evitar duplicados
    nome_categoria = "⚔️ 𝑹𝑷𝑮 𝒀𝑮𝑮𝑫𝑑𝑨𝑺𝑰𝑳 ›"
    cat_existente = discord.utils.get(guild.categories, name=nome_categoria)

    if cat_existente:
        return await interaction.followup.send(
            f"⚠️ A categoria **{nome_categoria}** já existe neste servidor! Apague-a primeiro se quiser recriar.", 
            ephemeral=True
        )

    try:
        # 🛡️ 2. Cria a categoria e os canais do RPG
        cat_rpg = await guild.create_category(nome_categoria)

        c_como_jogar = await guild.create_text_channel("📜・como-jogar", category=cat_rpg)
        await guild.create_text_channel("🔥・foguinho-e-cassino", category=cat_rpg)
        await guild.create_text_channel("🐉・masmorras", category=cat_rpg)
        await guild.create_text_channel("🐾・meu-pet", category=cat_rpg)
        await guild.create_text_channel("🏆・ostentacao-rank", category=cat_rpg)

        # 📜 3. Envia o guia no canal de tutorial
        embed_rpg_guia = discord.Embed(
            title="⚔️ 𝑩𝑬𝑴-𝑽𝑰𝑵𝑫𝑶 𝑨𝑶 𝑹𝑷𝑮 𝒀𝑮𝑮𝑫𝑑𝑨𝑺𝑰𝑳",
            description=(
                "Conquiste moedas, evolua seus pets e explore as profundezas da Yggdrasil!\n\n"
                "📌 **Comandos Principais:**\n"
                "• `/daily` — Colete sua recompensa diária de Golds.\n"
                "• `/foguinho` — Teste sua sorte no jogo do foguinho.\n"
                "• `/masmorra` — Enfrente monstros e ganhe recompensas.\n"
                "• `/pet` — Cuide do seu companheiro de batalha.\n"
                "• `/carteira` e `/rank` — Veja seu saldo e os mais ricos do servidor.\n"
                "• `/velha` — Desafie outro membro para um X1."
            ),
            color=discord.Color.dark_purple()
        )
        embed_rpg_guia.set_footer(text="Aproveite e boa sorte nas batalhas!")
        await c_como_jogar.send(embed=embed_rpg_guia)

        await interaction.followup.send("✨ **Categoria e canais do RPG Yggdrasil criados com sucesso!**", ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"❌ **Erro ao criar a categoria RPG:** `{e}`", ephemeral=True)

# ==========================================
# 🛠️ UTILITÁRIOS
# ==========================================
@bot.tree.command(name="ping", description="Verifica a latência do bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.defer()
    ms = round(bot.latency * 1000)
    await interaction.followup.send(f"🏓 Pong! Latência atual: **{ms}ms**")

@bot.tree.command(name="userinfo", description="Exibe informações de um membro")
async def userinfo(interaction: discord.Interaction, membro: discord.Member = None):
    await interaction.response.defer()
    alvo = membro or interaction.user
    roles = [role.mention for role in alvo.roles if role.name != "@everyone"]
    roles_str = ", ".join(roles) if roles else "Nenhum cargo relevante"
    
    embed = discord.Embed(title=f"👤 Perfil de {alvo.name}", color=discord.Color.blue())
    embed.add_field(name="ID", value=f"`{alvo.id}`", inline=True)
    embed.add_field(name="Conta Criada", value=alvo.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="Entrou no Servidor", value=alvo.joined_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="Cargos", value=roles_str, inline=False)
    embed.set_thumbnail(url=alvo.display_avatar.url)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="serverinfo", description="Exibe detalhes do servidor")
async def serverinfo(interaction: discord.Interaction):
    await interaction.response.defer()
    guild = interaction.guild
    embed = discord.Embed(title=f"🏰 {guild.name}", color=discord.Color.purple())
    embed.add_field(name="Dono", value=f"<@{guild.owner_id}>", inline=True)
    embed.add_field(name="Membros", value=f"👥 {guild.member_count}", inline=True)
    embed.add_field(name="Canais", value=f"💬 {len(guild.channels)}", inline=True)
    embed.add_field(name="Criado em", value=guild.created_at.strftime("%d/%m/%Y"), inline=False)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="ajuda", description="Lista todos os comandos do bot")
async def ajuda(interaction: discord.Interaction):
    await interaction.response.defer()
    embed = discord.Embed(title="🤖 Central de Comandos | Zy-Bot", color=discord.Color.gold())
    embed.add_field(
        name="🛠️ Utilitários", 
        value="`/ping` `/userinfo` `/serverinfo` `/avatar` `/embed` `/enquete` `/lembrete` `/moeda`", 
        inline=False
    )
    embed.add_field(
        name="🛒 Loja & Vendas", 
        value="`/fixar_produto` `/painelticket`", 
        inline=False
    )
    embed.add_field(
        name="🪙 Economia & Games", 
        value="`/carteira` `/daily` `/pay` `/rank` `/velha` `/pet` `/foguinho` `/masmorra`", 
        inline=False
    )
    embed.add_field(
        name="🎫 Atendimento & Registro", 
        value="`/set_chat_filtracao` `/set_passe_cargo`", 
        inline=False
    )
    embed.add_field(
        name="🛡️ Moderação & Gestão", 
        value="`/limpar` `/limparuser` `/kick` `/ban` `/mute` `/unmute` `/warn` `/addcargo` `/removecargo` `/nick` `/lock` `/unlock` `/anuncio` `/sorteio`", 
        inline=False
    )
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="avatar", description="Manda o avatar de um membro")
async def avatar(interaction: discord.Interaction, membro: discord.Member = None):
    await interaction.response.defer()
    alvo = membro or interaction.user
    embed = discord.Embed(title=f"🖼️ Avatar de {alvo.name}", color=discord.Color.dark_theme())
    embed.set_image(url=alvo.display_avatar.url)
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="embed", description="Cria uma mensagem formatada (Embed)")
@app_commands.checks.has_permissions(manage_messages=True)
async def embed(interaction: discord.Interaction, titulo: str, conteudo: str, cor_hex: str = "3498db"):
    await interaction.response.defer(ephemeral=True)
    try:
        cor_int = int(cor_hex.replace("#", ""), 16)
    except ValueError:
        cor_int = 0x3498db
    embed_msg = discord.Embed(title=titulo, description=conteudo, color=cor_int)
    await interaction.channel.send(embed=embed_msg)
    await interaction.followup.send("✅ Embed enviada!", ephemeral=True)

@bot.tree.command(name="enquete", description="Abre uma votação com reações")
async def enquete(interaction: discord.Interaction, pergunta: str):
    await interaction.response.defer()
    embed = discord.Embed(title="📊 Votação / Enquete", description=pergunta, color=discord.Color.blue())
    mensagem = await interaction.followup.send(embed=embed, wait=True)
    await mensagem.add_reaction("👍")
    await mensagem.add_reaction("👎")

@bot.tree.command(name="lembrete", description="Define um lembrete")
async def lembrete(interaction: discord.Interaction, minutos: int, texto: str):
    await interaction.response.defer()
    await interaction.followup.send(f"⏰ Lembrete definido para daqui a **{minutos}m**.")
    await asyncio.sleep(minutos * 60)
    await interaction.channel.send(f"🔔 {interaction.user.mention}, **Lembrete:** {texto}")

@bot.tree.command(name="moeda", description="Joga cara ou coroa")
async def moeda(interaction: discord.Interaction):
    await interaction.response.defer()
    await interaction.followup.send(f"🎲 Resultado: **{random.choice(['Cara 🪙', 'Coroa 👑'])}**")

# ==========================================
# 🤖 COMANDOS DE INTELIGÊNCIA ARTIFICIAL
# ==========================================

@bot.tree.command(name="gemini", description="Pergunte algo para a IA do Google (Gemini).")
async def gemini_cmd(interaction: discord.Interaction, pergunta: str):
    """Responde dúvidas usando o modelo Gemini 2.5 Flash."""
    await interaction.response.defer()

    if not gemini_client:
        await interaction.followup.send("⚠️ A chave `GEMINI_API_KEY` não foi configurada nas variáveis de ambiente.")
        return

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=pergunta
        )
        resposta = response.text

        if len(resposta) > 1900:
            resposta = resposta[:1900] + "...\n*(Resposta cortada devido ao limite de caracteres)*"

        embed = discord.Embed(
            title="✨ Resposta do Gemini",
            description=resposta,
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Pergunta de: {interaction.user.display_name}")
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ Erro ao processar resposta do Gemini: `{e}`")


@bot.tree.command(name="chatgpt", description="Pergunte algo para o ChatGPT (OpenAI).")
async def chatgpt_cmd(interaction: discord.Interaction, pergunta: str):
    """Responde dúvidas usando o ChatGPT (GPT-4o-mini)."""
    await interaction.response.defer()

    if not openai_client:
        await interaction.followup.send("⚠️ A chave `OPENAI_API_KEY` não foi configurada nas variáveis de ambiente.")
        return

    try:
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um assistente útil e amigável em um servidor do Discord."},
                {"role": "user", "content": pergunta}
            ]
        )
        resposta = completion.choices[0].message.content

        if len(resposta) > 1900:
            resposta = resposta[:1900] + "...\n*(Resposta cortada devido ao limite de caracteres)*"

        embed = discord.Embed(
            title="🤖 Resposta do ChatGPT",
            description=resposta,
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Pergunta de: {interaction.user.display_name}")
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ Erro ao processar resposta do ChatGPT: `{e}`")

# ==========================================
# 🎨 COMANDOS DE GERENCIAMENTO E DECORAÇÃO DE CANAIS
# ==========================================

@bot.tree.command(name="criar_canal", description="Cria um novo canal com nome decorado e personalizado.")
@app_commands.checks.has_permissions(manage_channels=True)
@app_commands.choices(tipo=[
    app_commands.Choice(name="Texto", value="texto"),
    app_commands.Choice(name="Voz", value="voz")
])
async def criar_canal(
    interaction: discord.Interaction, 
    nome_decorado: str, 
    tipo: app_commands.Choice[str], 
    categoria: discord.CategoryChannel = None,
    topico: str = None
):
    """Cria um canal de texto ou voz formatado."""
    await interaction.response.defer(ephemeral=True)

    try:
        if tipo.value == "texto":
            canal = await interaction.guild.create_text_channel(
                name=nome_decorado,
                category=categoria,
                topic=topico
            )
            tipo_txt = "Texto 💬"
        else:
            canal = await interaction.guild.create_voice_channel(
                name=nome_decorado,
                category=categoria
            )
            tipo_txt = "Voz 🔊"

        embed = discord.Embed(
            title="✨ Canal Criado com Sucesso!",
            description=f"**Canal:** {canal.mention}\n**Tipo:** {tipo_txt}\n**Categoria:** {categoria.name if categoria else 'Nenhuma'}",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)

    except discord.Forbidden:
        await interaction.followup.send("❌ Não tenho permissão de `Gerenciar Canais` para executar essa ação.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"⚠️ Ocorreu um erro ao criar o canal: `{e}`", ephemeral=True)


@bot.tree.command(name="renomear_canal", description="Altera o nome de um canal para um novo formato/decorado.")
@app_commands.checks.has_permissions(manage_channels=True)
async def renomear_canal(
    interaction: discord.Interaction, 
    novo_nome_decorado: str, 
    canal: discord.abc.GuildChannel = None
):
    """Renomeia qualquer canal existente."""
    await interaction.response.defer(ephemeral=True)

    target_channel = canal or interaction.channel

    try:
        nome_antigo = target_channel.name
        await target_channel.edit(name=novo_nome_decorado)

        embed = discord.Embed(
            title="🎨 Canal Renomeado!",
            description=f"**Canal:** {target_channel.mention}\n**De:** `{nome_antigo}`\n**Para:** `{novo_nome_decorado}`",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed)

    except discord.Forbidden:
        await interaction.followup.send("❌ Não tenho permissão para editar este canal.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"⚠️ Ocorreu um erro ao renomear: `{e}`", ephemeral=True)

# ==========================================
# 🛡️ MODERAÇÃO E GESTÃO
# ==========================================
@bot.tree.command(name="limpar", description="Apaga mensagens em massa")
@app_commands.checks.has_permissions(manage_messages=True)
async def limpar(interaction: discord.Interaction, quantidade: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=quantidade)
    await interaction.followup.send(f"🧹 **{len(deleted)}** mensagens apagadas!", ephemeral=True)

@bot.tree.command(name="limparuser", description="Apaga mensagens de um usuário específico")
@app_commands.checks.has_permissions(manage_messages=True)
async def limparuser(interaction: discord.Interaction, membro: discord.Member, quantidade: int = 20):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=quantidade, check=lambda m: m.author.id == membro.id)
    await interaction.followup.send(f"🧹 Apagadas **{len(deleted)}** mensagens de {membro.mention}!", ephemeral=True)

@bot.tree.command(name="kick", description="Expulsa um membro")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Não especificado"):
    await interaction.response.defer()
    await membro.kick(reason=motivo)
    await interaction.followup.send(f"👞 **{membro.mention}** foi expulsos. Motivo: *{motivo}*")

@bot.tree.command(name="ban", description="Bane um membro")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Não especificado"):
    await interaction.response.defer()
    await membro.ban(reason=motivo)
    await interaction.followup.send(f"🔨 **{membro.mention}** foi banido. Motivo: *{motivo}*")

@bot.tree.command(name="mute", description="Silencia um membro temporariamente")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, membro: discord.Member, minutos: int, motivo: str = "Não especificado"):
    await interaction.response.defer()
    tempo = discord.utils.utcnow() + datetime.timedelta(minutes=minutos)
    await membro.timeout(tempo, reason=motivo)
    await interaction.followup.send(f"🔇 **{membro.mention}** silenciado por **{minutos}m**.")

@bot.tree.command(name="unmute", description="Remove o silêncio de um membro")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, membro: discord.Member):
    await interaction.response.defer()
    await membro.timeout(None)
    await interaction.followup.send(f"🔊 O silêncio de **{membro.mention}** foi removido!")

@bot.tree.command(name="warn", description="Envia uma advertência para um membro")
@app_commands.checks.has_permissions(moderate_members=True)
async def warn(interaction: discord.Interaction, membro: discord.Member, motivo: str):
    await interaction.response.defer()
    embed = discord.Embed(title="⚠️ Advertência Recebida", description=f"Servidor: **{interaction.guild.name}**\n**Motivo:** {motivo}", color=discord.Color.dark_gold())
    try:
        await membro.send(embed=embed)
    except Exception:
        pass
    await interaction.followup.send(f"⚠️ Advertência aplicada a **{membro.mention}**!\n**Motivo:** *{motivo}*")

@bot.tree.command(name="addcargo", description="Adiciona um cargo a um membro")
@app_commands.checks.has_permissions(manage_roles=True)
async def addcargo(interaction: discord.Interaction, membro: discord.Member, cargo: discord.Role):
    await interaction.response.defer()
    await membro.add_roles(cargo)
    await interaction.followup.send(f"✅ Cargo {cargo.mention} adicionado a **{membro.mention}**!")

@bot.tree.command(name="removecargo", description="Remove um cargo de um membro")
@app_commands.checks.has_permissions(manage_roles=True)
async def removecargo(interaction: discord.Interaction, membro: discord.Member, cargo: discord.Role):
    await interaction.response.defer()
    await membro.remove_roles(cargo)
    await interaction.followup.send(f"🗑️ Cargo {cargo.mention} removido de **{membro.mention}**!")

@bot.tree.command(name="nick", description="Altera o apelido de um membro")
@app_commands.checks.has_permissions(manage_nicknames=True)
async def nick(interaction: discord.Interaction, membro: discord.Member, novo_apelido: str):
    await interaction.response.defer()
    await membro.edit(nick=novo_apelido)
    await interaction.followup.send(f"📝 Apelido de **{membro.mention}** alterado para `{novo_apelido}`!")

@bot.tree.command(name="anuncio", description="Envia um anúncio formatado")
@app_commands.checks.has_permissions(administrator=True)
async def anuncio(interaction: discord.Interaction, canal: discord.TextChannel, titulo: str, mensagem: str):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(title=f"📢 {titulo}", description=mensagem, color=discord.Color.gold())
    await canal.send(embed=embed)
    await interaction.followup.send(f"✅ Anúncio enviado em {canal.mention}!", ephemeral=True)

@bot.tree.command(name="lock", description="Tranca o canal atual")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.response.defer()
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.followup.send("🔒 Este canal foi **trancado**.")

@bot.tree.command(name="unlock", description="Destranca o canal atual")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.response.defer()
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.followup.send("🔓 Este canal foi **destrancado**.")

@bot.tree.command(name="sorteio", description="Sorteia um membro do servidor")
@app_commands.checks.has_permissions(administrator=True)
async def sorteio(interaction: discord.Interaction, premio: str):
    await interaction.response.defer()
    membros = [m for m in interaction.guild.members if not m.bot]
    vencedor = random.choice(membros)
    embed = discord.Embed(title="🎉 SORTEIO!", description=f"**Prêmio:** {premio}\n🏆 **Vencedor:** {vencedor.mention}", color=discord.Color.gold())
    await interaction.followup.send(embed=embed)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        msg = "❌ Você não tem permissão para usar este comando."
        if not interaction.response.is_done():
            await interaction.response.send_message(msg, ephemeral=True)
        else:
            await interaction.followup.send(msg, ephemeral=True)

# ==========================================
# 🚀 INICIALIZAÇÃO
# ==========================================
keep_alive()

async def main():
    async with bot:
        token = os.environ.get('DISCORD_TOKEN')
        if not token:
            print("❌ ERRO CRÍTICO: DISCORD_TOKEN não encontrado!")
            return
        
        # Carrega a Cog do RPG dinamicamente
        await bot.load_extension("pet_rpg")
        
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
        
