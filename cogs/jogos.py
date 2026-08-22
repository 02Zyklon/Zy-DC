import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import datetime
import json
import os
import akinator as aki
import economy

# --- CARREGAMENTO DINÂMICO DE TEXTOS (textos.json) ---
def carregar_textos():
    caminho = os.path.join(os.path.dirname(__file__), "..", "textos.json")
    if not os.path.exists(caminho):
        caminho = "textos.json"
    
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Erro ao carregar textos.json: {e}")
        return {
            "termo": ["TERMO", "DADOS", "PODER", "JOGOS", "NOITE"],
            "forca": {
                "geral": ["DISCORD", "PYTHON", "TECLADO", "DESENVOLVEDOR"],
                "programacao": ["PYTHON", "JAVASCRIPT", "ALGORITMO", "DISCORD"],
                "games": ["MINECRAFT", "VALORANT", "FORTNITE", "FREEFIRE"]
            },
            "quiz": [
                {"p": "Qual é a linguagem principal deste bot?", "r": "python"},
                {"p": "Qual o planeta mais próximo do Sol?", "r": "mercurio"},
                {"p": "Em que ano o Free Fire foi lançado?", "r": "2017"}
            ]
        }

TEXTOS = carregar_textos()


# ==========================================
# 1. COMPONENTES E INTERFACES (VIEWS / MODALS)
# ==========================================

# --- MODAL DO JOGO DO TERMO ---
class TermoModal(discord.ui.Modal, title="Jogo do Termo"):
    palpite = discord.ui.TextInput(
        label="Digite uma palavra de 5 letras",
        max_length=5,
        min_length=5,
        placeholder="Ex: TERMO"
    )

    def __init__(self, palavra_secreta):
        super().__init__()
        self.palavra_secreta = palavra_secreta

    async def on_submit(self, interaction: discord.Interaction):
        chute = self.palpite.value.upper()
        res = []
        for i in range(5):
            if chute[i] == self.palavra_secreta[i]:
                res.append(f"🟩 `{chute[i]}`")
            elif chute[i] in self.palavra_secreta:
                res.append(f"🟨 `{chute[i]}`")
            else:
                res.append(f"⬛ `{chute[i]}`")
        
        resultado_str = " ".join(res)
        if chute == self.palavra_secreta:
            await interaction.response.send_message(
                f"🎉 **Parabéns!** Você acertou a palavra!\n{resultado_str}"
            )
        else:
            await interaction.response.send_message(
                f"Tente novamente na próxima!\nResultado: {resultado_str}\n(A palavra era: **{self.palavra_secreta}**)"
            )

# --- VIEW DO AKINATOR ---
class AkinatorView(discord.ui.View):
    def __init__(self, aki_game, interaction: discord.Interaction):
        super().__init__(timeout=120.0)
        self.aki = aki_game
        self.user_id = interaction.user.id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Apenas quem iniciou o jogo pode responder!", ephemeral=True)
            return False
        return True

    async def atualizar_pergunta(self, interaction: discord.Interaction):
        if self.aki.progression >= 80 or self.aki.step >= 79:
            await self.aki.win()
            embed = discord.Embed(
                title="🧙‍♂️ Akinator — Encontrei seu personagem!",
                description=f"Acho que é **{self.aki.first_guess['name']}**!\n*{self.aki.first_guess['description']}*",
                color=discord.Color.gold()
            )
            embed.set_image(url=self.aki.first_guess['absolute_picture_path'])
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()
            return

        embed = discord.Embed(
            title=f"🧙‍♂️ Akinator — Pergunta #{self.aki.step + 1}",
            description=f"**{self.aki.question}**",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Progresso: {int(self.aki.progression)}%")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Sim", style=discord.ButtonStyle.green)
    async def responder_sim(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.aki.answer("y")
        await self.atualizar_pergunta(interaction)

    @discord.ui.button(label="Não", style=discord.ButtonStyle.red)
    async def responder_nao(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.aki.answer("n")
        await self.atualizar_pergunta(interaction)

    @discord.ui.button(label="Não Sei", style=discord.ButtonStyle.secondary)
    async def responder_nao_sei(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.aki.answer("i")
        await self.atualizar_pergunta(interaction)

    @discord.ui.button(label="Provavelmente Sim", style=discord.ButtonStyle.primary)
    async def responder_prov_sim(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.aki.answer("p")
        await self.atualizar_pergunta(interaction)

    @discord.ui.button(label="Provavelmente Não", style=discord.ButtonStyle.primary)
    async def responder_prov_nao(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.aki.answer("pn")
        await self.atualizar_pergunta(interaction)

# --- VIEW DO BLACKJACK (/21) ---
class BlackjackView(discord.ui.View):
    def __init__(self, user_id: int, aposta: int):
        super().__init__(timeout=60.0)
        self.user_id = user_id
        self.aposta = aposta
        self.baralho = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4
        random.shuffle(self.baralho)
        self.mao_jogador = [self.baralho.pop(), self.baralho.pop()]
        self.mao_dealer = [self.baralho.pop(), self.baralho.pop()]

    def calcular_pontos(self, mao):
        pontos = sum(mao)
        while pontos > 21 and 11 in mao:
            mao[mao.index(11)] = 1
            pontos = sum(mao)
        return pontos

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    def gerar_embed(self, final=False):
        pts_j = self.calcular_pontos(self.mao_jogador)
        pts_d = self.calcular_pontos(self.mao_dealer)
        embed = discord.Embed(title="🃏 Blackjack (21)", color=discord.Color.dark_green())
        embed.add_field(name=f"Sua Mão ({pts_j})", value=" ".join([f"`{c}`" for c in self.mao_jogador]), inline=False)
        if final:
            embed.add_field(name=f"Mão do Bot ({pts_d})", value=" ".join([f"`{c}`" for c in self.mao_dealer]), inline=False)
        else:
            embed.add_field(name="Mão do Bot", value=f"`{self.mao_dealer[0]}` `?`", inline=False)
        return embed

    @discord.ui.button(label="Comprar Carta", style=discord.ButtonStyle.green)
    async def pedir_carta(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.mao_jogador.append(self.baralho.pop())
        pts = self.calcular_pontos(self.mao_jogador)
        if pts > 21:
            economy.remove_gold(self.user_id, self.aposta)
            embed = self.gerar_embed(final=True)
            embed.description = f"💥 **Estourou!** Você fez {pts} pontos e perdeu **{self.aposta:,} Golds**."
            for item in self.children: item.disabled = True
            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()
        else:
            await interaction.response.edit_message(embed=self.gerar_embed(), view=self)

    @discord.ui.button(label="Parar", style=discord.ButtonStyle.red)
    async def parar(self, interaction: discord.Interaction, button: discord.ui.Button):
        pts_j = self.calcular_pontos(self.mao_jogador)
        pts_d = self.calcular_pontos(self.mao_dealer)
        while pts_d < 17:
            self.mao_dealer.append(self.baralho.pop())
            pts_d = self.calcular_pontos(self.mao_dealer)

        embed = self.gerar_embed(final=True)
        if pts_d > 21 or pts_j > pts_d:
            economy.add_gold(self.user_id, self.aposta)
            embed.description = f"🏆 **Você Venceu!** Ganhou **{self.aposta:,} Golds**."
        elif pts_j < pts_d:
            economy.remove_gold(self.user_id, self.aposta)
            embed.description = f"💀 **O Bot Venceu!** Você perdeu **{self.aposta:,} Golds**."
        else:
            embed.description = "⚖️ **Empate!** Seus Golds foram devolvidos."

        for item in self.children: item.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

# --- VIEWS DO JOGO DA VELHA ---
class VelhaButton(discord.ui.Button):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="‎", row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view: JogoDaVelhaView = self.view
        if interaction.user != view.jogador_atual:
            await interaction.response.send_message("❌ Não é seu turno!", ephemeral=True)
            return

        simbolo = "❌" if view.turn == 1 else "⭕"
        self.label = simbolo
        self.style = discord.ButtonStyle.danger if view.turn == 1 else discord.ButtonStyle.primary
        self.disabled = True
        view.tabuleiro[self.y][self.x] = simbolo

        if view.checar_vitoria(simbolo):
            for child in view.children: child.disabled = True
            await interaction.response.edit_message(content=f"🎉 {view.jogador_atual.mention} venceu o Jogo da Velha!", view=view)
            view.stop()
            return
        elif view.checar_empate():
            for child in view.children: child.disabled = True
            await interaction.response.edit_message(content="⚖️ O Jogo da Velha terminou em empate!", view=view)
            view.stop()
            return

        view.turn = 2 if view.turn == 1 else 1
        view.jogador_atual = view.p2 if view.turn == 2 else view.p1
        await interaction.response.edit_message(content=f"🎮 Turno de {view.jogador_atual.mention} ({'❌' if view.turn == 1 else '⭕'})", view=view)

class JogoDaVelhaView(discord.ui.View):
    def __init__(self, p1: discord.Member, p2: discord.Member):
        super().__init__(timeout=120.0)
        self.p1 = p1
        self.p2 = p2
        self.turn = 1
        self.jogador_atual = p1
        self.tabuleiro = [["" for _ in range(3)] for _ in range(3)]

        for y in range(3):
            for x in range(3):
                self.add_item(VelhaButton(x, y))

    def checar_vitoria(self, s):
        t = self.tabuleiro
        for i in range(3):
            if all(t[i][j] == s for j in range(3)) or all(t[j][i] == s for j in range(3)): return True
        if t[0][0] == t[1][1] == t[2][2] == s or t[0][2] == t[1][1] == t[2][0] == s: return True
        return False

    def checar_empate(self):
        return all(self.tabuleiro[y][x] != "" for y in range(3) for x in range(3))


# ==========================================
# 2. COG PRINCIPAL DE JOGOS
# ==========================================
class Jogos(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 1. AKINATOR
    @app_commands.command(name="akinator", description="Desafie o Akinator para adivinhar seu personagem!")
    async def akinator(self, interaction: discord.Interaction):
        await interaction.response.defer()
        aki_game = aki.Akinator()
        try:
            q = await aki_game.start_game(language="pt")
        except Exception:
            await interaction.followup.send("❌ Não foi possível se conectar ao Akinator agora.")
            return

        embed = discord.Embed(title="🧙‍♂️ Akinator — Pergunta #1", description=f"**{q}**", color=discord.Color.blue())
        view = AkinatorView(aki_game, interaction)
        await interaction.followup.send(embed=embed, view=view)

    # 2. TERMO
    @app_commands.command(name="termo", description="Adivinhe a palavra secreta de 5 letras.")
    async def termo(self, interaction: discord.Interaction):
        lista_termo = TEXTOS.get("termo", ["TERMO"])
        palavra_secreta = random.choice(lista_termo)
        await interaction.response.send_modal(TermoModal(palavra_secreta))

# Conjunto para rastrear canais que já possuem um jogo da forca ativo
    jogos_forca_ativos = set()

    # 3. FORCA (CORRIGIDA COM CONTROLE DE SESSÃO)
    @app_commands.command(name="forca", description="Jogo da forca no chat.")
    @app_commands.choices(categoria=[
        app_commands.Choice(name="Geral / Diversos", value="geral"),
        app_commands.Choice(name="Programação", value="programacao"),
        app_commands.Choice(name="Games", value="games")
    ])
    async def forca(self, interaction: discord.Interaction, categoria: app_commands.Choice[str] = None):
        channel_id = interaction.channel_id

        # Verifica se já existe um jogo da forca rodando neste canal
        if channel_id in self.jogos_forca_ativos:
            await interaction.response.send_message(
                "⚠️ Já existe um jogo da forca em andamento neste canal! Aguarde o término.", 
                ephemeral=True
            )
            return

        # Registra o canal como ativo
        self.jogos_forca_ativos.add(channel_id)

        try:
            cat = categoria.value if categoria else "geral"
            banco_forca = TEXTOS.get("forca", {})
            lista_palavras = banco_forca.get(cat, banco_forca.get("geral", ["DISCORD"]))
            
            palavra = random.choice(lista_palavras).upper()
            letras_descobertas = set()
            tentativas = 6

            def formatar_palavra():
                return " ".join([l if l in letras_descobertas else "\\_" for l in palavra])

            await interaction.response.send_message(
                f"🎮 **Jogo da Forca iniciado!**\nPalavra: {formatar_palavra()}\nTentativas restantes: `{tentativas}`"
            )

            def check(m):
                return m.channel == interaction.channel and len(m.content) == 1 and m.content.isalpha()

            while tentativas > 0:
                try:
                    msg = await self.bot.wait_for("message", check=check, timeout=30.0)
                except asyncio.TimeoutError:
                    await interaction.channel.send("⏳ Tempo esgotado! O jogo da forca foi encerrado.")
                    return

                letra = msg.content.upper()
                if letra in letras_descobertas:
                    continue

                letras_descobertas.add(letra)

                if letra in palavra:
                    if set(palavra).issubset(letras_descobertas):
                        await interaction.channel.send(f"🏆 **Vitória!** {msg.author.mention} acertou a palavra **{palavra}**!")
                        return
                    await interaction.channel.send(f"✅ Letra `{letra}` encontrada!\nPalavra: {formatar_palavra()}")
                else:
                    tentativas -= 1
                    await interaction.channel.send(f"❌ Letra `{letra}` incorreta.\nPalavra: {formatar_palavra()}\nTentativas: `{tentativas}`")

            await interaction.channel.send(f"💀 **Game Over!** A palavra era **{palavra}**.")

        finally:
            # Libera o canal para um novo jogo ao encerrar (por vitória, derrota ou tempo)
            self.jogos_forca_ativos.discard(channel_id)

    # 4. BLACKJACK / 21
    @app_commands.command(name="21", description="Aposte seus Golds no Blackjack (21).")
    async def blackjack(self, interaction: discord.Interaction, aposta: int):
        if aposta <= 0:
            await interaction.response.send_message("❌ A aposta precisa ser maior que zero!", ephemeral=True)
            return

        saldo = economy.get_gold(interaction.user.id)
        if saldo < aposta:
            await interaction.response.send_message(f"❌ Você não tem Golds suficientes. Saldo atual: `{saldo:,}` Golds", ephemeral=True)
            return

        view = BlackjackView(interaction.user.id, aposta)
        await interaction.response.send_message(embed=view.gerar_embed(), view=view)

    # 5. ROLETA RUSSA
    class Jogos(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.jogos_forca_ativos = set()

    @app_commands.command(name="roleta", description="Puxe o gatilho! Risco de tomar 1 min de timeout.")
    async def roleta(self, interaction: discord.Interaction):
        if random.randint(1, 6) == 1:
            await interaction.response.send_message(f"💥 **BANG!** {interaction.user.mention} deu azar e tomou um tiro! Silenciado por 1 minuto.")
            
            # Blindagem: Garante que o interaction.user tem o método de timeout
            if isinstance(interaction.user, discord.Member):
                try:
                    await interaction.user.timeout(datetime.timedelta(minutes=1), reason="Perdeu na Roleta Russa")
                except discord.Forbidden:
                    await interaction.followup.send("⚠️ Não tenho permissão de Moderador superior à sua para te silenciar!", ephemeral=True)
                except Exception as e:
                    print(f"Erro ao aplicar timeout: {e}")
        else:
            await interaction.response.send_message(f" *CLIQUE!* {interaction.user.mention} puxou o gatilho e a câmara estava vazia.")

    # 6. CAÇA-NÍQUEIS
    @app_commands.command(name="slots", description="Aposte Golds no Caça-Níqueis.")
    async def slots(self, interaction: discord.Interaction, aposta: int):
        if aposta <= 0:
            await interaction.response.send_message("❌ A aposta precisa ser maior que zero!", ephemeral=True)
            return

        saldo = economy.get_gold(interaction.user.id)
        if saldo < aposta:
            await interaction.response.send_message(f"❌ Saldo insuficiente! Saldo atual: `{saldo:,}` Golds", ephemeral=True)
            return

        emojis = ["🍒", "🍋", "🔔", "🎰", "💎"]
        r1, r2, r3 = random.choice(emojis), random.choice(emojis), random.choice(emojis)

        if r1 == r2 == r3:
            ganho = aposta * 3
            economy.add_gold(interaction.user.id, ganho)
            res = f"🎉 **JACKPOT!** Ganhou **{ganho:,} Golds**!"
        elif r1 == r2 or r2 == r3 or r1 == r3:
            ganho = int(aposta * 1.5)
            economy.add_gold(interaction.user.id, ganho)
            res = f"✨ **Dupla!** Ganhou **{ganho:,} Golds**!"
        else:
            economy.remove_gold(interaction.user.id, aposta)
            res = f"💀 Perdeu **{aposta:,} Golds**."

        await interaction.response.send_message(f"🎰 | [ {r1} | {r2} | {r3} ]\n{res}")

    # 7. JOGO DA VELHA
    @app_commands.command(name="velha", description="Desafie um membro para o Jogo da Velha.")
    async def velha(self, interaction: discord.Interaction, oponente: discord.Member):
        if oponente.bot or oponente == interaction.user:
            await interaction.response.send_message("❌ Oponente inválido!", ephemeral=True)
            return

        view = JogoDaVelhaView(interaction.user, oponente)
        await interaction.response.send_message(content=f"🎮 Turno de {interaction.user.mention} (❌)", view=view)

    # 8. PEDRA, PAPEL E TESOURA
    @app_commands.command(name="jokenpo", description="Jogue Pedra, Papel ou Tesoura contra o bot.")
    @app_commands.choices(escolha=[
        app_commands.Choice(name="Pedra 🪨", value="pedra"),
        app_commands.Choice(name="Papel 📄", value="papel"),
        app_commands.Choice(name="Tesoura ✂️", value="tesoura")
    ])
    async def jokenpo(self, interaction: discord.Interaction, escolha: app_commands.Choice[str]):
        bot_choice = random.choice(["pedra", "papel", "tesoura"])
        user_choice = escolha.value

        if user_choice == bot_choice:
            res = "⚖️ **Empate!**"
        elif (user_choice == "pedra" and bot_choice == "tesoura") or \
             (user_choice == "papel" and bot_choice == "pedra") or \
             (user_choice == "tesoura" and bot_choice == "papel"):
            res = "🏆 **Você Venceu!**"
        else:
            res = "💀 **O Bot Venceu!**"

        await interaction.response.send_message(f"Você: `{user_choice}` vs Bot: `{bot_choice}`\n{res}")

    # 10. ADIVINHAÇÃO
    @app_commands.command(name="adivinhe", description="Tente adivinhar o número de 1 a 100.")
    async def adivinhe(self, interaction: discord.Interaction):
        numero = random.randint(1, 100)
        await interaction.response.send_message("🔢 Pensei em um número de **1 a 100**. Digite seu palpite no chat! (30s)")

        def check(m):
            return m.channel == interaction.channel and m.author == interaction.user and m.content.isdigit()

        for _ in range(5):
            try:
                msg = await self.bot.wait_for("message", check=check, timeout=30.0)
            except asyncio.TimeoutError:
                await interaction.followup.send("⏳ Tempo esgotado!")
                return

            chute = int(msg.content)
            if chute == numero:
                await interaction.channel.send(f"🎉 **Parabéns!** Você acertou o número **{numero}**!")
                return
            elif chute < numero:
                await interaction.channel.send("📈 Mais **ALTO**!")
            else:
                await interaction.channel.send("📉 Mais **BAIXO**!")

        await interaction.channel.send(f"💀 Fim de tentativas! O número era **{numero}**.")

    # 11. QUIZ
    @app_commands.command(name="quiz", description="Responda a uma pergunta do banco de dados.")
    async def quiz(self, interaction: discord.Interaction):
        lista_quiz = TEXTOS.get("quiz", [])
        if not lista_quiz:
            await interaction.response.send_message("❌ Nenhuma pergunta cadastrada no momento!", ephemeral=True)
            return

        q = random.choice(lista_quiz)
        await interaction.response.send_message(f"❓ **Quiz:** {q['p']}\n*(Digite a resposta no chat em até 20s)*")

        def check(m):
            return m.channel == interaction.channel and m.author == interaction.user

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=20.0)
        except asyncio.TimeoutError:
            await interaction.followup.send("⏳ Tempo esgotado!")
            return

        if msg.content.strip().lower() == q['r'].strip().lower():
            await interaction.channel.send("🎉 **Resposta Correta!**")
        else:
            await interaction.channel.send(f"❌ Errado! A resposta era **{q['r']}**.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Jogos(bot))
