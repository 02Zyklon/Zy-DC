import os
import asyncio
import datetime
import random
import json
import logging
import discord
import aiohttp
from discord.ext import commands
from discord import app_commands
from keep_alive import keep_alive
import economy  # 🟢 Importação do módulo unificado de Economia

# Configura logs visíveis em tempo real no Discloud
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

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

# Arquivos de armazenamento JSON
DB_REGISTRO = "config_registro.json"
DB_AJUDA = "ajuda_config.json"

CATEGORIAS_VALIDAS = [
    "🎮 Jogos & Mini-Games",
    "💰 Economia & Carteira",
    "🛠️ Utilitários & IAs",
    "🛒 Vendas & Tickets",
    "🎫 Atendimento & Registro",
    "🛡️ Moderação & Gestão"
]

COMANDOS_INICIAIS_PADRAO = {
    "🎮 Jogos & Mini-Games": {
        "/daily": "Coleta sua recompensa diária de Golds.",
        "/foguinho": "Aposte e tente multiplicar seus Golds sem explodir.",
        "/masmorra": "Enfrente monstros nas profundezas por recompensas.",
        "/pet": "Cuide do seu companheiro de batalha.",
        "/explorar": "Explora biomas perigosos (Requer Nível 20+).",
        "/velha": "Desafie outro membro para um X1 de Jogo da Velha.",
        "/akinator": "Inicia um jogo interativo com o Akinator para adivinhar seu personagem.",
        "/ppt": "Desafie a IA para uma partida de Pedra, Papel ou Tesoura.",
        "/dado": "Rola um dado virtual de 6 a 100 lados.",
        "/caracoroa": "Aposte Golds no cara ou coroa contra o bot.",
        "/roleta": "Gire a roleta da sorte para tentar ganhar Golds."
    },
    "💰 Economia & Carteira": {
        "/carteira": "Consulte o seu saldo atual de Golds.",
        "/pay": "Transfira Golds para outros usuários.",
        "/rank": "Exibe o TOP 10 dos membros mais ricos do servidor."
    },
    "🛠️ Utilitários & IAs": {
        "/gemini": "Pergunta algo para a IA do Google (Gemini 2.5 Flash).",
        "/chatgpt": "Pergunta algo para o ChatGPT (GPT-4o-mini).",
        "/moeda": "Consulta cotações e converte valores entre moedas (USD, EUR, BRL, BTC).",
        "/ping": "Exibe a latência de conexão do bot.",
        "/userinfo": "Mostra datas, ID e cargos de um membro.",
        "/serverinfo": "Mostra informações completas do servidor.",
        "/avatar": "Baixa e exibe a foto de perfil de um membro.",
        "/embed": "Cria uma caixa de mensagem formatada.",
        "/enquete": "Inicia uma votação por reações (👍 / 👎).",
        "/lembrete": "Programa um aviso com contagem regressiva."
    },
    "🛒 Vendas & Tickets": {
        "/fixar_produto": "Fixa o anúncio de um produto com botão de compra.",
        "/painelticket": "Envia o painel fixo de suporte e atendimento geral."
    },
    "🎫 Atendimento & Registro": {
        "/set_chat_filtracao": "Configura o canal onde os membros digitam a senha.",
        "/set_passe_cargo": "Associa uma palavra-passe a um cargo automático."
    },
    "🛡️ Moderação & Gestão": {
        "/setup_servidor": "Cria a estrutura completa de canais do servidor.",
        "/setup_rpg": "Cria isoladamente a categoria e canais do RPG Yggdrasil.",
        "/limpar": "Apaga mensagens em massa no canal.",
        "/limparuser": "Apaga mensagens de um usuário específico.",
        "/kick": "Expulsa um membro do servidor.",
        "/ban": "Bane um membro do servidor.",
        "/mute": "Silencia um membro temporariamente por minutos.",
        "/unmute": "Remove o silêncio de um membro.",
        "/warn": "Aplica uma advertência privada no PV do usuário.",
        "/addcargo": "Adiciona um cargo a um membro.",
        "/removecargo": "Remove um cargo de um membro.",
        "/nick": "Altera o apelido de um membro no servidor.",
        "/lock": "Tranca o canal atual para os membros.",
        "/unlock": "Destranca o canal atual.",
        "/anuncio": "Envia uma mensagem oficial formatada em canal específico.",
        "/sorteio": "Sorteia um membro aleatório do servidor.",
        "/criar_canal": "Cria um novo canal com nome decorado e personalizado.",
        "/renomear_canal": "Altera o nome de um canal para um novo formato/decorado.",
        "/adc_comando": "[ADMIN] Adiciona um novo comando dinamicamente ao menu."
    }
}

def load_json(file_path, default):
    if not os.path.exists(file_path):
        if file_path == DB_AJUDA:
            save_json(DB_AJUDA, COMANDOS_INICIAIS_PADRAO)
            return COMANDOS_INICIAIS_PADRAO
        return default
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@bot.event
async def on_ready():
    # Sincroniza a árvore de comandos globalmente ao ligar
    try:
        synced = await bot.tree.sync()
        print(f"🌐 Sincronizados {len(synced)} comandos Slash globalmente!")
    except Exception as e:
        print(f"⚠️ Erro ao sincronizar comandos: {e}")
    
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


@bot.tree.command(name="pay", description="Transfira Golds para outro usuário.")
async def pay(interaction: discord.Interaction, destino: discord.Member, quantia: int):
    if quantia <= 0 or destino.bot or destino.id == interaction.user.id:
        return await interaction.response.send_message("❌ Operação ou valor inválido!", ephemeral=True)

    if not economy.remove_gold(interaction.user.id, quantia):
        return await interaction.response.send_message("❌ Saldo insuficiente!", ephemeral=True)

    economy.add_gold(destino.id, quantia)
    await interaction.response.send_message(f"💸 **{interaction.user.mention}** enviou **{quantia:,}** Golds 📀 para **{destino.mention}**!")


@bot.tree.command(name="rank", description="🏆 Exibe o TOP 10 dos membros mais ricos do servidor.")
async def rank(interaction: discord.Interaction):
    await interaction.response.defer()

    try:
        top_richest = economy.get_top_richest(10)

        if not top_richest:
            return await interaction.followup.send("⚠️ Nenhum registro de moedas/Golds encontrado ainda.")

        embed = discord.Embed(
            title="🏆 𝑹𝑨𝑵𝑲 𝑫𝑶𝑺 𝑴𝑨𝑰𝑺 𝑹𝑰𝑪𝑶𝑺",
            description="Confira os membros com maior saldo de Golds no servidor:\n",
            color=discord.Color.gold()
        )

        posicoes = ["🥇", "🥈", "🥉", "4º", "5º", "6º", "7º", "8º", "9º", "10º"]

        for index, (user_id, info) in enumerate(top_richest):
            membro = interaction.guild.get_member(int(user_id))
            nome = membro.display_name if membro else f"Usuário ({user_id})"
            golds = info.get("gold", 0) if isinstance(info, dict) else 0

            embed.add_field(
                name=f"{posicoes[index]} {nome}",
                value=f"💰 `{golds:,}` Golds",
                inline=False
            )

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ Ocorreu um erro ao carregar o rank: `{e}`")



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
async def on_app_command_completion(interaction: discord.Interaction, command: app_commands.Command):
    print(f"📌 [COMANDO EXECUTADO] /{command.name} por {interaction.user} (ID: {interaction.user.id})", flush=True)


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

# ==========================================
# ➕ COMANDO ADMIN: ADICIONAR COMANDO AO /AJUDA
# ==========================================
@@bot.tree.command(name="adc_comando", description="[ADMIN] Adiciona um novo comando a uma categoria no menu /ajuda.")
@app_commands.describe(
    categoria="A categoria onde o comando vai aparecer",
    nome_comando="O nome do comando (ex: /ban ou /pet)",
    descricao="Breve explicação do que o comando faz"
)
@app_commands.choices(categoria=[
    app_commands.Choice(name=cat, value=cat) for cat in CATEGORIAS_VALIDAS
])
@app_commands.checks.has_permissions(administrator=True)
async def adc_comando(interaction: discord.Interaction, categoria: app_commands.Choice[str], nome_comando: str, descricao: str):
    await interaction.response.defer(ephemeral=True)
    
    cat_nome = categoria.value
    dados_ajuda = load_json(DB_AJUDA, {cat: {} for cat in CATEGORIAS_VALIDAS})
    
    if cat_nome not in dados_ajuda:
        dados_ajuda[cat_nome] = {}
        
    dados_ajuda[cat_nome][nome_comando] = descricao
    save_json(DB_AJUDA, dados_ajuda)
    
    await interaction.followup.send(
        f"✅ Comando **{nome_comando}** adicionado com sucesso à categoria **{cat_nome}**!", 
        ephemeral=True
    )


# ==========================================
# 📚 MENU DE AJUDA INTERATIVO DINÂMICO
# ==========================================
class AjudaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

        # Mapeamento de emojis e descrições visuais para o menu
        icones_e_descricoes = {
            "🎮 Jogos & Mini-Games": ("🎮", "Comandos de RPG, mini-games, apostas e diversão."),
            "💰 Economia & Carteira": ("💳", "Comandos de saldo, pagamentos e rank de golds."),
            "🛠️ Utilitários & IAs": ("🛠️", "Comandos gerais, perfil, cotações e Inteligências Artificiais."),
            "🛒 Vendas & Tickets": ("🛒", "Sistemas de suporte e anúncios de produtos."),
            "🎫 Atendimento & Registro": ("🎫", "Configurações de suporte e filtração por senha."),
            "🛡️ Moderação & Gestão": ("🛡️", "Comandos de administração do servidor.")
        }

        options = []
        for cat in CATEGORIAS_VALIDAS:
            emoji, desc = icones_e_descricoes.get(cat, ("📂", "Lista de comandos da categoria."))
            options.append(
                discord.SelectOption(label=cat, description=desc, emoji=emoji)
            )

        select_menu = discord.ui.Select(
            placeholder="📂 Escolha uma categoria de comandos...",
            min_values=1,
            max_values=1,
            options=options
        )
        select_menu.callback = self.selecionar_categoria
        self.add_item(select_menu)

    async def selecionar_categoria(self, interaction: discord.Interaction):
        # Pega a opção selecionada no menu
        opcao = interaction.data["values"][0]
        
        dados_ajuda = load_json(DB_AJUDA, {})
        comandos_categoria = dados_ajuda.get(opcao, {})

        cores = {
            "🎮 Jogos & Mini-Games": discord.Color.green(),
            "💰 Economia & Carteira": discord.Color.gold(),
            "🛠️ Utilitários & IAs": discord.Color.blue(),
            "🛒 Vendas & Tickets": discord.Color.green(),
            "🎫 Atendimento & Registro": discord.Color.purple(),
            "🛡️ Moderação & Gestão": discord.Color.red()
        }

        embed = discord.Embed(
            title=f"📂 Central de Ajuda — {opcao}",
            description="Lista de comandos cadastrados nesta categoria:\n",
            color=cores.get(opcao, discord.Color.dark_theme())
        )

        if not comandos_categoria:
            embed.add_field(name="Vazio", value="Nenhum comando cadastrado nesta categoria ainda.", inline=False)
        else:
            for cmd, desc in comandos_categoria.items():
                embed.add_field(name=cmd, value=desc, inline=False)

        embed.set_footer(text="Zy-Bot • Selecione qualquer categoria no menu acima para navegar.")
        await interaction.response.edit_message(embed=embed, view=self)

@bot.tree.command(name="ajuda", description="Central de ajuda interativa do bot")
async def ajuda(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Central de Comandos | Zy-Bot",
        description=(
            "Seja bem-vindo à central de ajuda do servidor!\n\n"
            "📌 **Como usar:**\n"
            "Selecione uma das opções no **menu suspenso abaixo** para abrir a lista completa de comandos e suas respectivas explicações."
        ),
        color=discord.Color.dark_theme()
    )
    embed.set_footer(text="Escolha uma categoria abaixo para navegar.")

    view = AjudaView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


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


# ==========================================
# 💵 COMANDO DE COTAÇÃO E CONVERSÃO DE MOEDAS
# ==========================================
@bot.tree.command(name="moeda", description="💱 Cotação em tempo real e conversão de moedas (USD, EUR, BRL, BTC).")
@app_commands.choices(
    de=[
        app_commands.Choice(name="Dólar (USD)", value="USD"),
        app_commands.Choice(name="Euro (EUR)", value="EUR"),
        app_commands.Choice(name="Real (BRL)", value="BRL"),
        app_commands.Choice(name="Bitcoin (BTC)", value="BTC")
    ],
    para=[
        app_commands.Choice(name="Real (BRL)", value="BRL"),
        app_commands.Choice(name="Dólar (USD)", value="USD"),
        app_commands.Choice(name="Euro (EUR)", value="EUR"),
        app_commands.Choice(name="Bitcoin (BTC)", value="BTC")
    ]
)
async def moeda(interaction: discord.Interaction, de: str = "USD", para: str = "BRL", quantidade: float = 1.0):
    await interaction.response.defer()

    if de == para:
        return await interaction.followup.send("⚠️ As moedas de origem e destino devem ser diferentes.")

    par = f"{de}-{para}"
    url = f"https://economia.awesomeapi.com.br/last/{par}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return await interaction.followup.send(f"❌ Não foi possível obter a cotação para o par `{par}`.")

                data = await response.json()
                key = f"{de}{para}"
                if key not in data:
                    return await interaction.followup.send("❌ Dados de cotação indisponíveis no momento.")

                cotacao = float(data[key]["bid"])
                variacao = float(data[key]["pctChange"])
                valor_convertido = quantidade * cotacao

                simbolos = {"USD": "$", "EUR": "€", "BRL": "R$", "BTC": "₿"}
                s_de = simbolos.get(de, "")
                s_para = simbolos.get(para, "")

                fmt_de = f"{s_de} {quantidade:,.2f}" if de != "BTC" else f"{s_de} {quantidade:.6f}"
                fmt_para = f"{s_para} {valor_convertido:,.2f}" if para != "BTC" else f"{s_para} {valor_convertido:.6f}"

                cor_var = discord.Color.green() if variacao >= 0 else discord.Color.red()

                embed = discord.Embed(
                    title=f"💱 Cotação: {de} ➔ {para}",
                    color=cor_var
                )
                embed.add_field(name="📥 Quantidade", value=f"`{fmt_de}`", inline=True)
                embed.add_field(name="📤 Resultado", value=f"`{fmt_para}`", inline=True)
                embed.add_field(
                    name="📈 Taxa de Câmbio", 
                    value=f"1 {de} = `{cotacao:,.4f}` {para}\n**Variação (24h):** `{variacao:+.2f}%`", 
                    inline=False
                )
                embed.set_footer(text="Dados fornecidos via AwesomeAPI em tempo real.")

                await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ Ocorreu um erro ao consultar as cotações: `{e}`")
        
        
        # ==========================================
# 🤖 COMANDOS DE INTELIGÊNCIA ARTIFICIAL
# ==========================================
@bot.tree.command(name="gemini", description="Pergunte algo para a IA do Google (Gemini).")
async def gemini_cmd(interaction: discord.Interaction, pergunta: str):
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
    await interaction.followup.send(f"👞 **{membro.mention}** foi expulso. Motivo: *{motivo}*")


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


# ==========================================
# ⚙️ TRATAMENTO UNIFICADO DE ERROS
# ==========================================
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        minutos = round(error.retry_after / 60)
        msg = f"⏳ Calma aí! Seus personagens estão exaustos. Você poderá batalhar novamente em **{minutos} minutos**."
    elif isinstance(error, app_commands.MissingPermissions):
        msg = "❌ Você não tem permissão para usar este comando."
    else:
        msg = f"❌ Ocorreu um erro ao executar este comando: `{error}`"

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
        
        # 1. Carrega a Cog do RPG (pet_rpg.py na raiz)
        try:
            await bot.load_extension("pet_rpg")
            print("🟢 Cog 'pet_rpg' carregada!")
        except Exception as e:
            print(f"⚠️ Erro ao carregar 'pet_rpg': {e}")

        # 2. Carrega a Cog de Música
        try:
            await bot.load_extension("cogs.music")
            print("🟢 Cog 'cogs.music' carregada!")
        except Exception as e:
            print(f"⚠️ Erro ao carregar 'cogs.music': {e}")

        # 3. Carrega a Cog de Jogos
        try:
            await bot.load_extension("cogs.jogos")
            print("🟢 Cog 'cogs.jogos' carregada!")
        except Exception as e:
            print(f"⚠️ Erro ao carregar 'cogs.jogos': {e}")

        # 4. Carrega a Cog de Gacha
        try:
            await bot.load_extension("cogs.gacha")
            print("🟢 Cog 'cogs.gacha' carregada!")
        except Exception as e:
            print(f"⚠️ Erro ao carregar 'cogs.gacha': {e}")
        
        # 5. Inicia o bot
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
