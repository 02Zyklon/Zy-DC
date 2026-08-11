import os
import asyncio
import datetime
import random
import json
import discord
from discord.ext import commands
from discord import app_commands
from keep_alive import keep_alive

# =========================================================
# CONFIGURAÇÃO E INICIALIZAÇÃO
# =========================================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ID do seu servidor no Discord (Guild)
GUILD_ID = 1434359569718706320

# Arquivos de armazenamento em JSON
DB_ECONOMIA = "database_golds.json"
DB_REGISTRO = "config_registro.json"

def load_json(file_path, default):
    if not os.path.exists(file_path):
        return default
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def get_user_gold(db, user_id):
    uid = str(user_id)
    if uid not in db:
        db[uid] = {"gold": 100}
    return db[uid]

@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)
    print(f"🤖 Bot online e sincronizado com sucesso como: {bot.user}")

# =========================================================
# 🪙 SISTEMA DE GOLDS (ECONOMIA)
# =========================================================
@bot.tree.command(name="carteira", description="Exibe o seu saldo atual de Golds.")
async def carteira(interaction: discord.Interaction, usuario: discord.Member = None):
    target = usuario or interaction.user
    db = load_json(DB_ECONOMIA, {})
    data = get_user_gold(db, target.id)

    embed = discord.Embed(
        title="🏛️ Banco Central Zy",
        description=f"Detalhamento financeiro de {target.mention}",
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="💰 Saldo em Golds", value=f"`{data['gold']:,}` 📀", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="daily", description="Resgate sua recompensa diária de Golds.")
async def daily(interaction: discord.Interaction):
    db = load_json(DB_ECONOMIA, {})
    user_data = get_user_gold(db, interaction.user.id)

    reward = random.randint(250, 600)
    user_data["gold"] += reward
    save_json(DB_ECONOMIA, db)

    embed = discord.Embed(
        title="🎁 Recompensa Diária Coletada!",
        description=f"Você recebeu **+{reward}** Golds 📀!",
        color=discord.Color.green()
    )
    embed.add_field(name="Novo Saldo", value=f"`{user_data['gold']:,}` 📀")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="pay", description="Transfira Golds para outro usuário.")
async def pay(interaction: discord.Interaction, destino: discord.Member, quantia: int):
    if quantia <= 0 or destino.id == interaction.user.id:
        return await interaction.response.send_message("❌ Operação inválida.", ephemeral=True)

    db = load_json(DB_ECONOMIA, {})
    autor_data = get_user_gold(db, interaction.user.id)
    destino_data = get_user_gold(db, destino.id)

    if autor_data["gold"] < quantia:
        return await interaction.response.send_message("❌ Saldo insuficiente!", ephemeral=True)

    autor_data["gold"] -= quantia
    destino_data["gold"] += quantia
    save_json(DB_ECONOMIA, db)

    await interaction.response.send_message(f"💸 **{interaction.user.mention}** enviou **{quantia:,}** Golds 📀 para **{destino.mention}**!")

@bot.tree.command(name="rank", description="Exibe o Ranking dos usuários mais ricos.")
async def rank(interaction: discord.Interaction):
    db = load_json(DB_ECONOMIA, {})
    sorted_users = sorted(db.items(), key=lambda x: x[1].get("gold", 0), reverse=True)[:10]

    embed = discord.Embed(title="🏆 Ranking de Golds - Top 10", color=discord.Color.gold())
    medals = ["🥇", "🥈", "🥉"]
    desc = ""

    for idx, (uid, data) in enumerate(sorted_users, 1):
        user = bot.get_user(int(uid))
        name = user.display_name if user else f"Usuário ({uid})"
        prefix = medals[idx-1] if idx <= 3 else f"`#{idx}`"
        desc += f"{prefix} **{name}** — `{data.get('gold', 0):,}` 📀\n"

    embed.description = desc or "Sem dados econômicos."
    await interaction.response.send_message(embed=embed)

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
# 🎫 SISTEMA DE TICKETS & ATENDIMENTO
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
        name="🪙 Economia & Games", 
        value="`/carteira` `/daily` `/pay` `/rank` `/velha`", 
        inline=False
    )
    embed.add_field(
        name="🎫 Atendimento & Registro", 
        value="`/painelticket` `/set_chat_filtracao` `/set_passe_cargo`", 
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
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
