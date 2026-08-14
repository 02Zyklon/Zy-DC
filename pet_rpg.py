import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import time
import random

DATA_FILE = "pets.json"

# --- AUXILIARES DO BANCO DE DADOS (JSON) ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- VIEW INTERATIVA PARA O DUELO PVP ---
class DuelView(discord.ui.View):
    def __init__(self, desafiante: discord.Member, desafiado: discord.Member, timeout=60):
        super().__init__(timeout=timeout)
        self.desafiante = desafiante
        self.desafiado = desafiado
        self.aceito = False

    @discord.ui.button(label="⚔️ Aceitar Duelo", style=discord.ButtonStyle.green)
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.desafiado.id:
            return await interaction.response.send_message("❌ Apenas o jogador desafiado pode aceitar o duelo!", ephemeral=True)
        
        self.aceito = True
        self.stop()
        # Desabilita botões
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="⚔️ **O duelo foi aceito! O combate está começando...**", view=self)

    @discord.ui.button(label="🏳️ Recusar", style=discord.ButtonStyle.red)
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.desafiado.id:
            return await interaction.response.send_message("❌ Apenas o jogador desafiado pode recusar!", ephemeral=True)
        
        self.stop()
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content=f"🏳️ {self.desafiado.mention} recusou o desafio de duelo de {self.desafiante.mention}.", view=self)

# --- CLASSE DA COG ---
class PetRPG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 1. COMANDO: /pet_adotar
    @app_commands.command(name="pet_adotar", description="Escolha o seu Pet inicial!")
    @app_commands.choices(elemento=[
        app_commands.Choice(name="🔥 Fogo (Faisquinha) - Foco em Dano", value="fogo"),
        app_commands.Choice(name="💧 Água (Pinguelim) - Foco em Vida/Defesa", value="agua"),
        app_commands.Choice(name="⚡ Trovão (Faísca) - Foco em Agilidade/Esquiva", value="trovao")
    ])
    async def pet_adotar(self, interaction: discord.Interaction, elemento: app_commands.Choice[str]):
        user_id = str(interaction.user.id)
        data = load_data()

        if user_id in data:
            return await interaction.response.send_message("❌ Você já possui um Pet! Use `/foguinho` para cuidar dele.", ephemeral=True)

        stats_base = {
            "fogo": {"hp": 80, "hp_max": 80, "atq": 25, "def": 8, "agi": 12, "nome_raça": "Faisquinha"},
            "agua": {"hp": 120, "hp_max": 120, "atq": 15, "def": 18, "agi": 8, "nome_raça": "Pinguelim"},
            "trovao": {"hp": 90, "hp_max": 90, "atq": 20, "def": 10, "agi": 22, "nome_raça": "Faísca"}
        }

        elem = elemento.value
        base = stats_base[elem]

        data[user_id] = {
            "elemento": elem,
            "nome": f"Pet de {interaction.user.name}",
            "raça": base["nome_raça"],
            "level": 1,
            "xp": 0,
            "last_daily": 0,
            "streak": 0,
            "midia": None,
            "stats": {
                "hp_atual": base["hp"],
                "hp_max": base["hp_max"],
                "atq": base["atq"],
                "defesa": base["def"],
                "agi": base["agi"]
            },
            "historico": {"vitorias": 0, "derrotas": 0}
        }

        save_data(data)

        embed = discord.Embed(
            title="🐣 NOVO PET ADOTADO!",
            description=f"Parabéns {interaction.user.mention}! Você escolheu o elemento **{elem.upper()}**.\nSeu pet começou como **{base['nome_raça']}**!",
            color=discord.Color.brand_green()
        )
        embed.add_field(name="❤️ HP", value=str(base["hp"]), inline=True)
        embed.add_field(name="⚔️ ATQ", value=str(base["atq"]), inline=True)
        embed.add_field(name="🛡️ DEF", value=str(base["def"]), inline=True)

        await interaction.response.send_message(embed=embed)

    # 2. COMANDO: /foguinho (DAILY / CUIDAR DO PET)
    @app_commands.command(name="foguinho", description="Alimente seu Pet diariamente para ganhar XP e subir de nível!")
    async def foguinho(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = load_data()

        if user_id not in data:
            return await interaction.response.send_message("❌ Você ainda não tem um Pet! Use `/pet_adotar` primeiro.", ephemeral=True)

        pet = data[user_id]
        agora = int(time.time())
        tempo_24h = 86400

        tempo_passado = agora - pet["last_daily"]
        if tempo_passado < tempo_24h:
            restante = tempo_24h - tempo_passado
            horas = restante // 3600
            minutos = (restante % 3600) // 60
            return await interaction.response.send_message(f"⏳ Seu Pet já está alimentado! Volte em **{horas}h {minutos}m**.", ephemeral=True)

        if tempo_passado > (tempo_24h * 2):
            pet["streak"] = 1
        else:
            pet["streak"] += 1

        xp_ganho = random.randint(20, 50)
        if pet["streak"] >= 7:
            xp_ganho = int(xp_ganho * 1.25)

        pet["xp"] += xp_ganho
        pet["last_daily"] = agora

        xp_necessario = pet["level"] * 100
        subiu = False
        while pet["xp"] >= xp_necessario:
            pet["xp"] -= xp_necessario
            pet["level"] += 1
            subiu = True
            
            pet["stats"]["hp_max"] += 10
            pet["stats"]["hp_atual"] = pet["stats"]["hp_max"]
            pet["stats"]["atq"] += 3
            pet["stats"]["defesa"] += 2
            xp_necessario = pet["level"] * 100

        save_data(data)

        embed = discord.Embed(
            title=f"🔥 Você alimentou {pet['nome']}!",
            description=f"🎉 **+{xp_ganho} XP** adquiridos!\n🔥 **Sequência (Streak):** {pet['streak']} dia(s)",
            color=discord.Color.orange()
        )
        if subiu:
            embed.add_field(name="🎊 LEVEL UP!", value=f"Seu Pet subiu para o **Nível {pet['level']}**!", inline=False)

        embed.add_field(name="Nível", value=str(pet["level"]), inline=True)
        embed.add_field(name="XP", value=f"{pet['xp']} / {pet['level'] * 100}", inline=True)

        await interaction.response.send_message(embed=embed)

    # 3. COMANDO: /pet_perfil
    @app_commands.command(name="pet_perfil", description="Veja os status e detalhes do seu Pet!")
    async def pet_perfil(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = load_data()

        if user_id not in data:
            return await interaction.response.send_message("❌ Você ainda não tem um Pet! Use `/pet_adotar`.", ephemeral=True)

        pet = data[user_id]
        st = pet["stats"]
        hist = pet.get("historico", {"vitorias": 0, "derrotas": 0})

        embed = discord.Embed(
            title=f"🐾 {pet['nome']} ({pet['raça']})",
            color=discord.Color.red() if pet["elemento"] == "fogo" else discord.Color.blue()
        )
        embed.add_field(name="Elemento", value=pet["elemento"].upper(), inline=True)
        embed.add_field(name="Nível", value=str(pet["level"]), inline=True)
        embed.add_field(name="XP", value=f"{pet['xp']}/{pet['level']*100}", inline=True)
        
        embed.add_field(name="❤️ HP", value=f"{st['hp_atual']}/{st['hp_max']}", inline=True)
        embed.add_field(name="⚔️ ATQ", value=str(st['atq']), inline=True)
        embed.add_field(name="🛡️ DEF", value=str(st['defesa']), inline=True)

        embed.add_field(name="📊 Histórico", value=f"🏆 Vitórias: `{hist['vitorias']}` | 💀 Derrotas: `{hist['derrotas']}`", inline=False)

        if pet["midia"]:
            embed.set_image(url=pet["midia"])

        await interaction.response.send_message(embed=embed)

    # 4. COMANDO: /masmorra (PVE)
    @app_commands.command(name="masmorra", description="Enfrente monstros em uma masmorra para ganhar XP!")
    @app_commands.choices(dificuldade=[
        app_commands.Choice(name="🟢 Caverna Tranquila (Fácil)", value="facil"),
        app_commands.Choice(name="🟡 Floresta Fechada (Média)", value="medio"),
        app_commands.Choice(name="🔴 Vulcão Infernal (Difícil)", value="dificil")
    ])
    async def masmorra(self, interaction: discord.Interaction, dificuldade: app_commands.Choice[str]):
        user_id = str(interaction.user.id)
        data = load_data()

        if user_id not in data:
            return await interaction.response.send_message("❌ Você precisa ter um Pet! Use `/pet_adotar` primeiro.", ephemeral=True)

        pet = data[user_id]
        st = pet["stats"]

        monstros = {
            "facil": {"nome": "Slime Solitário", "hp": 50, "atq": 12, "def": 3, "elemento": "agua", "xp_min": 25, "xp_max": 45},
            "medio": {"nome": "Lobo das Sombras", "hp": 100, "atq": 22, "def": 8, "elemento": "trovao", "xp_min": 55, "xp_max": 95},
            "dificil": {"nome": "Dragão Flamejante", "hp": 170, "atq": 35, "def": 15, "elemento": "fogo", "xp_min": 110, "xp_max": 200}
        }

        mob = monstros[dificuldade.value].copy()
        pet_hp = st["hp_max"]
        mob_hp = mob["hp"]
        
        vantagens = {"fogo": "trovao", "trovao": "agua", "agua": "fogo"}
        mult_pet = 1.3 if vantagens.get(pet["elemento"]) == mob["elemento"] else 1.0
        mult_mob = 1.3 if vantagens.get(mob["elemento"]) == pet["elemento"] else 1.0

        logs = []
        rodada = 1

        while pet_hp > 0 and mob_hp > 0 and rodada <= 8:
            # Turno do Pet
            dano_pet = max(3, int((st["atq"] * mult_pet) - (mob["def"] / 2)) + random.randint(-2, 3))
            mob_hp -= dano_pet
            
            if mob_hp <= 0:
                mob_hp = 0
                logs.append(f"⚔️ **R{rodada}:** Seu Pet causou `{dano_pet}` de dano e eliminou o **{mob['nome']}**!")
                break

            # Turno do Monstro
            dano_mob = max(3, int((mob["atq"] * mult_mob) - (st["defesa"] / 2)) + random.randint(-2, 3))
            pet_hp -= dano_mob
            
            if pet_hp <= 0:
                pet_hp = 0
                logs.append(f"💥 **R{rodada}:** **{mob['nome']}** te causou `{dano_mob}` de dano e te nocauteou!")
                break

            logs.append(f"⚔️ **R{rodada}:** Você deu `{dano_pet}` dano | **{mob['nome']}** deu `{dano_mob}` dano.")
            rodada += 1

        vitoria = mob_hp <= 0

        if "historico" not in pet:
            pet["historico"] = {"vitorias": 0, "derrotas": 0}

        if vitoria:
            xp_ganho = random.randint(mob["xp_min"], mob["xp_max"])
            pet["xp"] += xp_ganho
            pet["historico"]["vitorias"] += 1

            xp_necessario = pet["level"] * 100
            subiu = False
            while pet["xp"] >= xp_necessario:
                pet["xp"] -= xp_necessario
                pet["level"] += 1
                subiu = True
                pet["stats"]["hp_max"] += 10
                pet["stats"]["hp_atual"] = pet["stats"]["hp_max"]
                pet["stats"]["atq"] += 3
                pet["stats"]["defesa"] += 2
                xp_necessario = pet["level"] * 100

            save_data(data)

            embed = discord.Embed(
                title=f"🏰 VITÓRIA NA MASMORRA!",
                description=f"**Desafio:** {dificuldade.name}\n\n" + "\n".join(logs),
                color=discord.Color.green()
            )
            embed.add_field(name="🎁 Recompensa", value=f"**+{xp_ganho} XP**", inline=False)
            if subiu:
                embed.add_field(name="🎊 LEVEL UP!", value=f"Seu Pet subiu para o **Nível {pet['level']}**!", inline=False)
        else:
            pet["historico"]["derrotas"] += 1
            save_data(data)

            embed = discord.Embed(
                title=f"💀 DERROTA NA MASMORRA...",
                description=f"**Desafio:** {dificuldade.name}\n\n" + "\n".join(logs),
                color=discord.Color.red()
            )
            embed.set_footer(text="Use /foguinho para subir de nível e aumentar seu ATQ/DEF antes de tentar de novo!")

        await interaction.response.send_message(embed=embed)

    # 5. COMANDO: /duelar (PVP INTERATIVO)
    @app_commands.command(name="duelar", description="Desafie outro jogador para um duelo de Pets!")
    async def duelar(self, interaction: discord.Interaction, oponente: discord.Member):
        desafiante_id = str(interaction.user.id)
        oponente_id = str(oponente.id)

        if oponente.bot:
            return await interaction.response.send_message("❌ Você não pode duelar contra bots!", ephemeral=True)

        if desafiante_id == oponente_id:
            return await interaction.response.send_message("❌ Você não pode duelar contra você mesmo!", ephemeral=True)

        data = load_data()

        if desafiante_id not in data:
            return await interaction.response.send_message("❌ Você precisa ter um Pet para duelar! Use `/pet_adotar`.", ephemeral=True)

        if oponente_id not in data:
            return await interaction.response.send_message(f"❌ {oponente.mention} ainda não possui um Pet!", ephemeral=True)

        # Envia convite de duelo com botões
        embed_desafio = discord.Embed(
            title="⚔️ DESAFIO DE DUELO PVP!",
            description=f"{oponente.mention}, você foi desafiado por {interaction.user.mention} para um combate de Pets!\n\n**Aceita o duelo?**",
            color=discord.Color.gold()
        )

        view = DuelView(interaction.user, oponente)
        await interaction.response.send_message(content=oponente.mention, embed=embed_desafio, view=view)

        await view.wait()

        if not view.aceito:
            return

        # Recarrega dados atualizados
        data = load_data()
        p1 = data[desafiante_id]
        p2 = data[oponente_id]

        p1_st, p2_st = p1["stats"], p2["stats"]
        p1_hp, p2_hp = p1_st["hp_max"], p2_st["hp_max"]

        vantagens = {"fogo": "trovao", "trovao": "agua", "agua": "fogo"}
        mult1 = 1.3 if vantagens.get(p1["elemento"]) == p2["elemento"] else 1.0
        mult2 = 1.3 if vantagens.get(p2["elemento"]) == p1["elemento"] else 1.0

        logs = []
        rodada = 1

        while p1_hp > 0 and p2_hp > 0 and rodada <= 10:
            # Turno P1 -> P2
            dano1 = max(3, int((p1_st["atq"] * mult1) - (p2_st["defesa"] / 2)) + random.randint(-2, 3))
            p2_hp -= dano1
            if p2_hp <= 0:
                p2_hp = 0
                logs.append(f"⚔️ **R{rodada}:** {p1['nome']} deu `{dano1}` de dano e finalizou o pet de {oponente.display_name}!")
                break

            # Turno P2 -> P1
            dano2 = max(3, int((p2_st["atq"] * mult2) - (p1_st["defesa"] / 2)) + random.randint(-2, 3))
            p1_hp -= dano2
            if p1_hp <= 0:
                p1_hp = 0
                logs.append(f"💥 **R{rodada}:** {p2['nome']} deu `{dano2}` de dano e finalizou o pet de {interaction.user.display_name}!")
                break

            logs.append(f"⚔️ **R{rodada}:** {interaction.user.display_name} deu `{dano1}` | {oponente.display_name} deu `{dano2}`")
            rodada += 1

        # Definição do vencedor
        p1_venceu = p2_hp <= 0
        vencedor_user = interaction.user if p1_venceu else oponente
        vencedor_pet = p1 if p1_venceu else p2
        perdedor_pet = p2 if p1_venceu else p1

        # Atualiza histórico e concede bônus de XP ao vencedor
        vencedor_pet.setdefault("historico", {"vitorias": 0, "derrotas": 0})
        perdedor_pet.setdefault("historico", {"vitorias": 0, "derrotas": 0})

        vencedor_pet["historico"]["vitorias"] += 1
        perdedor_pet["historico"]["derrotas"] += 1

        xp_ganho = random.randint(30, 60)
        vencedor_pet["xp"] += xp_ganho

        # Level up check do vencedor
        xp_necessario = vencedor_pet["level"] * 100
        subiu = False
        while vencedor_pet["xp"] >= xp_necessario:
            vencedor_pet["xp"] -= xp_necessario
            vencedor_pet["level"] += 1
            subiu = True
            vencedor_pet["stats"]["hp_max"] += 10
            vencedor_pet["stats"]["hp_atual"] = vencedor_pet["stats"]["hp_max"]
            vencedor_pet["stats"]["atq"] += 3
            vencedor_pet["stats"]["defesa"] += 2
            xp_necessario = vencedor_pet["level"] * 100

        save_data(data)

        embed_resultado = discord.Embed(
            title=f"🏆 {vencedor_user.display_name} VENCEU O DUELO!",
            description="\n".join(logs),
            color=discord.Color.gold()
        )
        embed_resultado.add_field(name="🎁 Recompensa do Vencedor", value=f"**+{xp_ganho} XP** para {vencedor_pet['nome']}", inline=False)
        if subiu:
            embed_resultado.add_field(name="🎊 LEVEL UP!", value=f"{vencedor_pet['nome']} subiu para o **Nível {vencedor_pet['level']}**!", inline=False)

        await interaction.followup.send(embed=embed_resultado)

async def setup(bot):
    await bot.add_cog(PetRPG(bot))
