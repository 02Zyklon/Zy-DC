import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import time
import random
import economy  # Importa o módulo centralizado de economia

BOSS_FILE = "boss_data.json"

def load_boss():
    if not os.path.exists(BOSS_FILE):
        return {}
    with open(BOSS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_boss(data):
    with open(BOSS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

DATA_FILE = "pets.json"

# --- AUXILIARES DO BANCO DE DADOS DE PETS (JSON) ---
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
        await interaction.response.edit_message(content=f"🏳️ {self.desafiado.mention} recusou o desafio de duelo.", view=self)

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

        # Adiciona o bônus inicial no banco centralizado de Golds
        economy.add_gold(interaction.user.id, 100)

        embed = discord.Embed(
            title="🐣 NOVO PET ADOTADO!",
            description=f"Parabéns {interaction.user.mention}! Você escolheu o elemento **{elem.upper()}**.\nSeu pet começou como **{base['nome_raça']}**!\n\n💰 **Bônus de Boas-Vindas:** +100 Golds adicionados à sua carteira!",
            color=discord.Color.brand_green()
        )
        embed.add_field(name="❤️ HP", value=str(base["hp"]), inline=True)
        embed.add_field(name="⚔️ ATQ", value=str(base["atq"]), inline=True)
        embed.add_field(name="🛡️ DEF", value=str(base["def"]), inline=True)

        await interaction.response.send_message(embed=embed)

    # 2. COMANDO: /foguinho (DAILY / CUIDAR DO PET)
    @app_commands.command(name="foguinho", description="Alimente seu Pet diariamente para ganhar XP e Golds!")
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
        golds_ganhos = random.randint(30, 70)

        if pet["streak"] >= 7:
            xp_ganho = int(xp_ganho * 1.25)
            golds_ganhos = int(golds_ganhos * 1.5)

        pet["xp"] += xp_ganho
        pet["last_daily"] = agora

        # Adiciona Golds na economia global
        novo_saldo = economy.add_gold(interaction.user.id, golds_ganhos)

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
            description=f"🎉 **+{xp_ganho} XP** | 💰 **+{golds_ganhos} Golds**\n🔥 **Sequência (Streak):** {pet['streak']} dia(s)",
            color=discord.Color.orange()
        )
        if subiu:
            embed.add_field(name="🎊 LEVEL UP!", value=f"Seu Pet subiu para o **Nível {pet['level']}**!", inline=False)

        embed.add_field(name="Nível", value=str(pet["level"]), inline=True)
        embed.add_field(name="XP", value=f"{pet['xp']} / {pet['level'] * 100}", inline=True)
        embed.add_field(name="💰 Saldo Geral", value=f"{novo_saldo:,} Golds", inline=True)

        await interaction.response.send_message(embed=embed)

    # 3. COMANDO: /pet_perfil
    @app_commands.command(name="pet_perfil", description="Veja os status, saldos e detalhes do seu Pet!")
    async def pet_perfil(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = load_data()

        if user_id not in data:
            return await interaction.response.send_message("❌ Você ainda não tem um Pet! Use `/pet_adotar`.", ephemeral=True)

        pet = data[user_id]
        st = pet["stats"]
        hist = pet.get("historico", {"vitorias": 0, "derrotas": 0})
        
        # Busca o saldo global do usuário
        saldo_golds = economy.get_gold(interaction.user.id)

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

        embed.add_field(name="💰 Carteira Central", value=f"**{saldo_golds:,}** Golds", inline=True)
        embed.add_field(name="📊 Histórico", value=f"🏆 Vitórias: `{hist['vitorias']}` | 💀 Derrotas: `{hist['derrotas']}`", inline=True)

        if pet["midia"]:
            embed.set_image(url=pet["midia"])

        await interaction.response.send_message(embed=embed)

    # 4. COMANDO: /masmorra (PVE) - COMBATE AVANÇADO
    @app_commands.command(name="masmorra", description="Enfrente monstros em uma masmorra para ganhar XP e Golds!")
    @app_commands.choices(dificuldade=[
        app_commands.Choice(name="🟢 Caverna Tranquila (Fácil)", value="facil"),
        app_commands.Choice(name="🟡 Floresta Fechada (Média)", value="medio"),
        app_commands.Choice(name="🔴 Vulcão Infernal (Difícil)", value="dificil")
    ])
    @app_commands.checks.cooldown(1, 1800, key=lambda i: i.user.id) # Cooldown de 30 minutos
    async def masmorra(self, interaction: discord.Interaction, dificuldade: app_commands.Choice[str]):
        user_id = str(interaction.user.id)
        data = load_data()

        if user_id not in data:
            return await interaction.response.send_message("❌ Você precisa ter um Pet! Use `/pet_adotar` primeiro.", ephemeral=True)

        pet = data[user_id]
        st = pet["stats"]

        # SISTEMA DE FERIMENTO: Impede o uso se o pet estiver desmaiado
        if st.get("hp_atual", st["hp_max"]) <= 0:
            return await interaction.response.send_message(
                "💀 Seu Pet está gravemente ferido e desmaiado! Compre uma **🧪 Poção de Cura** na `/loja` antes de tentar batalhar novamente.", 
                ephemeral=True
            )

        monstros = {
            "facil": {"nome": "Slime Solitário", "hp": 50, "atq": 12, "def": 3, "elemento": "agua", "xp_min": 25, "xp_max": 45, "gold_min": 20, "gold_max": 40},
            "medio": {"nome": "Lobo das Sombras", "hp": 100, "atq": 22, "def": 8, "elemento": "trovao", "xp_min": 55, "xp_max": 95, "gold_min": 50, "gold_max": 90},
            "dificil": {"nome": "Dragão Flamejante", "hp": 170, "atq": 35, "def": 15, "elemento": "fogo", "xp_min": 110, "xp_max": 200, "gold_min": 120, "gold_max": 220}
        }

        mob = monstros[dificuldade.value].copy()
        
        # O HP agora puxa a vida atual, não a máxima. Não há cura grátis.
        pet_hp = st.get("hp_atual", st["hp_max"]) 
        mob_hp = mob["hp"]
        
        vantagens = {"fogo": "trovao", "trovao": "agua", "agua": "fogo"}
        mult_pet = 1.3 if vantagens.get(pet["elemento"]) == mob["elemento"] else 1.0
        mult_mob = 1.3 if vantagens.get(mob["elemento"]) == pet["elemento"] else 1.0

        logs = []
        rodada = 1

        while pet_hp > 0 and mob_hp > 0 and rodada <= 8:
            # --- TURNO DO PET (Ataque + Crítico) ---
            chance_crit = min(st["agi"], 50) # Cap de 50% de chance
            is_crit = random.randint(1, 100) <= chance_crit
            
            dano_pet = max(3, int((st["atq"] * mult_pet) - (mob["def"] / 2)) + random.randint(-2, 3))
            
            crit_msg = ""
            if is_crit:
                dano_pet = int(dano_pet * 1.5)
                crit_msg = "🎯 **CRÍTICO!** "

            mob_hp -= dano_pet
            
            if mob_hp <= 0:
                mob_hp = 0
                logs.append(f"⚔️ **R{rodada}:** {crit_msg}Seu Pet causou `{dano_pet}` de dano e eliminou o **{mob['nome']}**!")
                break

            # --- TURNO DO MONSTRO (Ataque + Esquiva do Pet) ---
            chance_esquiva = min(st["agi"], 40) # Cap de 40% de chance
            is_esquiva = random.randint(1, 100) <= chance_esquiva
            
            if is_esquiva:
                logs.append(f"💨 **R{rodada}:** Seu Pet usou sua agilidade e **ESQUIVOU** do ataque!")
                dano_mob = 0
            else:
                dano_mob = max(3, int((mob["atq"] * mult_mob) - (st["defesa"] / 2)) + random.randint(-2, 3))
                pet_hp -= dano_mob
                
                if pet_hp <= 0:
                    pet_hp = 0
                    logs.append(f"💥 **R{rodada}:** **{mob['nome']}** te causou `{dano_mob}` de dano e te nocauteou!")
                    break

            if not is_esquiva:
                logs.append(f"⚔️ **R{rodada}:** {crit_msg}Pet deu `{dano_pet}` dano | **Mob** deu `{dano_mob}` dano.")
            
            rodada += 1

        # Salva o HP pós-batalha para evitar farm sem cura
        pet["stats"]["hp_atual"] = pet_hp
        vitoria = mob_hp <= 0
        pet.setdefault("historico", {"vitorias": 0, "derrotas": 0})

        if vitoria:
            xp_ganho = random.randint(mob["xp_min"], mob["xp_max"])
            golds_ganhos = random.randint(mob["gold_min"], mob["gold_max"])
            
            pet["xp"] += xp_ganho
            pet["historico"]["vitorias"] += 1

            novo_saldo = economy.add_gold(interaction.user.id, golds_ganhos)

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
            embed.add_field(name="🎁 Recompensas", value=f"**+{xp_ganho} XP** | 💰 **+{golds_ganhos} Golds**\n*(Saldo total: {novo_saldo:,} Golds)*", inline=False)
            embed.set_footer(text=f"HP Restante do seu Pet: {pet_hp}/{st['hp_max']}")
            
            if subiu:
                embed.add_field(name="🎊 LEVEL UP!", value=f"Seu Pet subiu para o **Nível {pet['level']}** e curou o HP!", inline=False)
        else:
            pet["historico"]["derrotas"] += 1
            
            # PUNIÇÃO HARDCORE
            punicao_txt = ""
            if dificuldade.value == "dificil":
                saldo_atual = economy.get_gold(interaction.user.id)
                punicao_gold = int(saldo_atual * 0.05) # Perde 5% do ouro total
                if punicao_gold > 0:
                    economy.remove_gold(interaction.user.id, punicao_gold)
                    punicao_txt = f"\n\n💀 **MORTE BRUTAL:** Você desmaiou no Vulcão Infernal e perdeu **{punicao_gold} Golds** do seu banco!"

            save_data(data)

            embed = discord.Embed(
                title=f"💀 DERROTA NA MASMORRA...",
                description=f"**Desafio:** {dificuldade.name}\n\n" + "\n".join(logs) + punicao_txt,
                color=discord.Color.dark_red()
            )
            embed.set_footer(text="Acesse a /loja e compre uma poção para reanimar seu Pet!")

        await interaction.response.send_message(embed=embed)

        # ==========================================
    # 🐉 SISTEMA DE WORLD BOSS (RAID EVENT)
    # ==========================================

    @app_commands.command(name="set_boss", description="[ADMIN] Invoca um novo World Boss para o servidor!")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_boss(self, interaction: discord.Interaction, nome: str, hp_total: int, premio_golds: int):
        boss_data = {
            "nome": nome,
            "hp_max": hp_total,
            "hp_atual": hp_total,
            "premio_golds": premio_golds,
            "ativo": True,
            "dano_jogadores": {} # {user_id: {"nome": display_name, "dano": int}}
        }
        save_boss(boss_data)

        embed = discord.Embed(
            title="🔥 UM NOVO WORLD BOSS APARECEU!",
            description=(
                f" Um inimigo colossal despertou em Yggdrasil!\n\n"
                f"👹 **Boss:** `{nome}`\n"
                f"❤️ **Vida Total:** `{hp_total:,}` HP\n"
                f"💰 **Pool de Recompensas:** `{premio_golds:,}` Golds\n\n"
                "⚔️ Use o comando `/atacar_boss` para dar dano e garantir sua fatia do prêmio!"
            ),
            color=discord.Color.dark_red()
        )
        await interaction.response.send_message(embed=embed)


    @app_commands.command(name="atacar_boss", description="Ataque o World Boss ativo e acumule dano no ranking!")
    @app_commands.checks.cooldown(1, 600, key=lambda i: i.user.id) # Cooldown de 10 minutos
    async def atacar_boss(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        pets = load_data() # Carrega o banco dos pets

        if user_id not in pets:
            return await interaction.response.send_message("❌ Você precisa adotar um Pet primeiro com `/pet_adotar`!", ephemeral=True) #[span_0](start_span)[span_0](end_span)

        pet = pets[user_id]
        st = pet["stats"]

        # Checa se o pet não está zerado de vida[span_1](start_span)[span_1](end_span)
        if st.get("hp_atual", st["hp_max"]) <= 0:
            return await interaction.response.send_message("💀 Seu Pet está desmaiado! Use uma **🧪 Poção de Cura** na `/loja` antes de encarar o Boss.", ephemeral=True) #[span_2](start_span)[span_2](end_span)

        boss = load_boss()
        if not boss or not boss.get("ativo", False):
            return await interaction.response.send_message("😴 Não há nenhum World Boss ativo no momento. Aguarde a administração invocar um!", ephemeral=True)

        # Cálculo do Ataque com chance de Crítico[span_3](start_span)[span_3](end_span)
        dano_base = random.randint(st["atq"], st["atq"] * 2)
        chance_crit = min(st["agi"], 50) #[span_4](start_span)[span_4](end_span)
        is_crit = random.randint(1, 100) <= chance_crit
        
        crit_msg = ""
        if is_crit:
            dano_base = int(dano_base * 1.5)
            crit_msg = "🎯 **CRÍTICO!** "

        # Aplica o dano no Boss
        boss["hp_atual"] -= dano_base
        
        # Registra no ranking individual
        if user_id not in boss["dano_jogadores"]:
            boss["dano_jogadores"][user_id] = {"nome": interaction.user.display_name, "dano": 0}
        
        boss["dano_jogadores"][user_id]["dano"] += dano_base

        # Morte do Boss
        if boss["hp_atual"] <= 0:
            boss["hp_atual"] = 0
            boss["ativo"] = False
            save_boss(boss)

            # Distribuição dos Golds proporcional ao dano causado
            total_dano = sum(p["dano"] for p in boss["dano_jogadores"].values())
            premio_pool = boss["premio_golds"]

            resumo_recompensas = []
            for uid, info in boss["dano_jogadores"].items():
                porcentagem = info["dano"] / total_dano
                golds_ganhos = int(premio_pool * porcentagem)
                economy.add_gold(int(uid), golds_ganhos) #[span_5](start_span)[span_5](end_span)
                resumo_recompensas.append(f"• **{info['nome']}**: `{info['dano']:,}` dano ({porcentagem:.1%}) ➔ **+{golds_ganhos:,} Golds** 💰")

            embed_vitoria = discord.Embed(
                title=f"🎉 O WORLD BOSS {boss['nome'].upper()} FOI DERROTADO!",
                description=(
                    f"⚔️ **Ataque Final por:** {interaction.user.mention} ({crit_msg}`{dano_base:,}` de dano!)\n\n"
                    "🏆 **DISTRIBUIÇÃO DE RECOMPENSAS:**\n" + "\n".join(resumo_recompensas)
                ),
                color=discord.Color.gold()
            )
            return await interaction.response.send_message(embed=embed_vitoria)

        # Se o Boss ainda estiver vivo
        save_boss(boss)

        porcentagem_hp = (boss["hp_atual"] / boss["hp_max"]) * 100
        dano_acumulado = boss["dano_jogadores"][user_id]["dano"]

        embed = discord.Embed(
            title=f"⚔️ ATAQUE AO WORLD BOSS!",
            description=(
                f"{interaction.user.mention} enviou **{pet['nome']}** para a batalha!\n\n"
                f"{crit_msg}Dano Causado: `{dano_base:,}`\n"
                f"🩸 **HP Restante do Boss:** `{boss['hp_atual']:,}` / `{boss['hp_max']:,}` ({porcentagem_hp:.1f}%)\n"
                f"📊 **Seu Dano Acumulado:** `{dano_acumulado:,}`"
            ),
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

import random
import discord
from discord import app_commands
from discord.ext import commands

# BANCO EXPANDIDO COM 40 CENÁRIOS E MONSTROS DE GUILDA
CENARIOS_GUILDA = [
    # --- CENÁRIOS ORIGINAIS (1 a 20) ---
    {"bioma": "Pântano Viscoso", "mob": "Goblin do Pântano", "hp": 120, "atq": 25, "def": 5, "xp": 120, "gold": 90},
    {"bioma": "Floresta dos Cogumelos", "mob": "Esporo Mutante", "hp": 100, "atq": 28, "def": 3, "xp": 110, "gold": 80},
    {"bioma": "Caverna de Cristal", "mob": "Besouro Geoda", "hp": 180, "atq": 20, "def": 15, "xp": 140, "gold": 110},
    {"bioma": "Ruínas Esquecidas", "mob": "Guardião de Pedra", "hp": 220, "atq": 30, "def": 20, "xp": 180, "gold": 150},
    {"bioma": "Vale dos Trovões", "mob": "Águia Elétrica", "hp": 110, "atq": 35, "def": 4, "xp": 130, "gold": 100},
    {"bioma": "Cemitério Abandonado", "mob": "Esqueleto Cavaleiro", "hp": 140, "atq": 27, "def": 8, "xp": 125, "gold": 95},
    {"bioma": "Mina Abandonada", "mob": "Kobold Minerador", "hp": 90, "atq": 22, "def": 4, "xp": 95, "gold": 120},
    {"bioma": "Cume Gelado", "mob": "Lobo das Neves", "hp": 130, "atq": 29, "def": 6, "xp": 135, "gold": 100},
    {"bioma": "Ninho de Serpes", "mob": "Filhote de Serpe", "hp": 160, "atq": 33, "def": 10, "xp": 160, "gold": 130},
    {"bioma": "Esgotos da Cidade", "mob": "Rato Gigante Mutado", "hp": 85, "atq": 20, "def": 2, "xp": 85, "gold": 70},
    {"bioma": "Abismo das Sombras", "mob": "Sombra Vagante", "hp": 150, "atq": 36, "def": 7, "xp": 170, "gold": 140},
    {"bioma": "Deserto Escaldante", "mob": "Escorpião do Deserto", "hp": 140, "atq": 31, "def": 12, "xp": 145, "gold": 115},
    {"bioma": "Manguezal Escuro", "mob": "Jacaré-Tigre", "hp": 170, "atq": 34, "def": 11, "xp": 165, "gold": 135},
    {"bioma": "Templo Profanado", "mob": "Cultista das Sombras", "hp": 125, "atq": 38, "def": 5, "xp": 150, "gold": 160},
    {"bioma": "Vulcão Ativo", "mob": "Elementar de Magma", "hp": 200, "atq": 40, "def": 14, "xp": 210, "gold": 180},
    {"bioma": "Santuário Antigo", "mob": "Treant Corrompido", "hp": 240, "atq": 25, "def": 18, "xp": 190, "gold": 140},
    {"bioma": "Litoral Esquecido", "mob": "Sereia Abissal", "hp": 135, "atq": 32, "def": 8, "xp": 140, "gold": 125},
    {"bioma": "Planalto dos Ecos", "mob": "Harpia Sorrateira", "hp": 115, "atq": 30, "def": 5, "xp": 120, "gold": 105},
    {"bioma": "Masmorra Esquecida", "mob": "Golem de Ferro", "hp": 250, "atq": 28, "def": 22, "xp": 220, "gold": 170},
    {"bioma": "Portal do Vazio", "mob": "Aberração Estelar", "hp": 210, "atq": 42, "def": 12, "xp": 240, "gold": 200},

    # --- NOVOS CENÁRIOS (21 a 40) ---
    {"bioma": "Labirinto de Espinhos", "mob": "Mímico Vegetal", "hp": 165, "atq": 33, "def": 9, "xp": 155, "gold": 130},
    {"bioma": "Vale dosOssos", "mob": "Quimera Reanimada", "hp": 230, "atq": 39, "def": 16, "xp": 225, "gold": 175},
    {"bioma": "Pico Tempestuoso", "mob": "Roc dos Céus", "hp": 190, "atq": 37, "def": 11, "xp": 195, "gold": 145},
    {"bioma": "Abismo Coralino", "mob": "Kraken Juvenil", "hp": 260, "atq": 31, "def": 20, "xp": 230, "gold": 190},
    {"bioma": "Catacumbas Reais", "mob": "Mumia do Faraó", "hp": 175, "atq": 35, "def": 13, "xp": 180, "gold": 210},
    {"bioma": "Floresta Espectral", "mob": "Fogo-Fátuo Ancião", "hp": 110, "atq": 44, "def": 4, "xp": 165, "gold": 120},
    {"bioma": "Forja Obscura", "mob": "Autômato Defeituoso", "hp": 215, "atq": 36, "def": 17, "xp": 205, "gold": 165},
    {"bioma": "Tundra Iluminada", "mob": "Yeti das Cavernas", "hp": 240, "atq": 38, "def": 15, "xp": 220, "gold": 160},
    {"bioma": "Pântano de Ácido", "mob": "Lesma Devoradora", "hp": 280, "atq": 24, "def": 21, "xp": 210, "gold": 140},
    {"bioma": "Ninho de Aracnídeos", "mob": "Aranha Viúva Tântrica", "hp": 130, "atq": 41, "def": 7, "xp": 175, "gold": 150},
    {"bioma": "Ilha Voadora", "mob": "Gárgula do Vento", "hp": 185, "atq": 32, "def": 14, "xp": 185, "gold": 155},
    {"bioma": "Deserto de Cristal", "mob": "Serpente das Dunas", "hp": 155, "atq": 36, "def": 10, "xp": 160, "gold": 135},
    {"bioma": "Jardim Corrompido", "mob": "Planta Carnívora Gigante", "hp": 200, "atq": 34, "def": 12, "xp": 190, "gold": 125},
    {"bioma": "Caverna Ecoante", "mob": "Morcego Sônico", "hp": 105, "atq": 39, "def": 5, "xp": 145, "gold": 115},
    {"bioma": "Templo da Névoa", "mob": "Monge Fantasma", "hp": 145, "atq": 37, "def": 8, "xp": 170, "gold": 180},
    {"bioma": " cratera Meteórica", "mob": "Verme Estelar", "hp": 250, "atq": 43, "def": 19, "xp": 250, "gold": 220},
    {"bioma": "Fenda Marítima", "mob": "Tubarão Martelo Mutante", "hp": 205, "atq": 40, "def": 13, "xp": 215, "gold": 170},
    {"bioma": "Vilarejo Fantasma", "mob": "Banshee Lacerante", "hp": 120, "atq": 45, "def": 6, "xp": 180, "gold": 165},
    {"bioma": "Fortaleza Esquecida", "mob": "Cavaleiro sem Cabeça", "hp": 220, "atq": 42, "def": 18, "xp": 240, "gold": 200},
    {"bioma": "Núcleo de Yggdrasil", "mob": "Avatar Corrompido", "hp": 300, "atq": 48, "def": 25, "xp": 300, "gold": 280}
]

# INTERFACE COM BOTÕES PARA DECISÃO RÁPIDA
class ExplorarView(discord.ui.View):
    def __init__(self, user_id, pet_data, cenario, progresso_diario):
        super().__init__(timeout=60)
        self.user_id = str(user_id)
        self.pet_data = pet_data
        self.cenario = cenario
        self.progresso = progresso_diario

    @discord.ui.button(label="⚔️ Atacar Monstro", style=discord.ButtonStyle.danger)
    async def atacar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Esta exploração não é sua!", ephemeral=True)

        st = self.pet_data["stats"]
        mob = self.cenario
        
        # Sistema de Batalha Simulado
        dano_pet = max(5, st["atq"] - mob["def"]) + random.randint(1, 10)
        dano_mob = max(5, mob["atq"] - st["defesa"]) + random.randint(1, 10)

        # Atualiza uso diário
        self.pet_data["exploracao_hoje"] = self.progresso + 1
        
        if dano_pet >= (mob["hp"] / 3): # Pet venceu a rodada de exploração
            xp_ganho = mob["xp"]
            gold_ganho = mob["gold"]
            
            self.pet_data["xp"] += xp_ganho
            
            # --- NOVA ESCALA DE XP PÓS-NÍVEL 20 ---
            lvl = self.pet_data["level"]
            xp_necessario = (lvl * 300) if lvl >= 20 else (lvl * 100) #[span_1](start_span)[span_1](end_span)
            
            subiu = False
            if self.pet_data["xp"] >= xp_necessario:
                self.pet_data["xp"] -= xp_necessario
                self.pet_data["level"] += 1
                subiu = True

            economy.add_gold(interaction.user.id, gold_ganho) #[span_2](start_span)[span_2](end_span)
            save_data(data) # Salva estado dos pets

            txt_resultado = f"✅ **Vitória!** Você derrotou o **{mob['mob']}**!\n🎁 **Recompensas:** +{xp_ganho} XP | +{gold_ganho} Golds"
            if subiu:
                txt_resultado += f"\n🎊 **LEVEL UP!** Seu pet alcançou o **Nível {self.pet_data['level']}**!"
            
            # Se ainda não bateu o limite de 10, puxa o próximo encontro automaticamente
            if self.pet_data["exploracao_hoje"] < 10:
                novo_cenario = random.choice(CENARIOS_GUILDA)
                prox_view = ExplorarView(self.user_id, self.pet_data, novo_cenario, self.pet_data["exploracao_hoje"])
                
                embed_prox = discord.Embed(
                    title=f"🗺️ Exploração em Cadeia [{self.pet_data['exploracao_hoje']}/10]",
                    description=f"{txt_resultado}\n\n---\n🌳 **Novo Bioma Encontrado:** `{novo_cenario['bioma']}`\n👹 **Monstro:** `{novo_cenario['mob']}` (XP: {novo_cenario['xp']} | Gold: {novo_cenario['gold']})\n\nO que deseja fazer?",
                    color=discord.Color.green()
                )
                await interaction.response.edit_message(embed=embed_prox, view=prox_view)
            else:
                embed_fim = discord.Embed(
                    title="🏁 Exploração Diária Concluída!",
                    description=f"{txt_resultado}\n\n✨ Você atingiu o limite de **10/10 explorações hoje**. Volte amanhã!",
                    color=discord.Color.gold()
                )
                await interaction.response.edit_message(embed=embed_fim, view=None)

        else: # Derrota na exploração
            save_data(data)
            embed_derrota = discord.Embed(
                title="💀 Derrotado na Exploração...",
                description=f"O **{mob['mob']}** era forte demais! Seu pet recuou para a guilda para se recuperar.",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed_derrota, view=None)

    @discord.ui.button(label="🏃 Continuar Explorando", style=discord.ButtonStyle.secondary)
    async def pular(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Esta exploração não é sua!", ephemeral=True)

        self.pet_data["exploracao_hoje"] = self.progresso + 1
        save_data(data)

        if self.pet_data["exploracao_hoje"] < 10:
            novo_cenario = random.choice(CENARIOS_GUILDA)
            prox_view = ExplorarView(self.user_id, self.pet_data, novo_cenario, self.pet_data["exploracao_hoje"])
            
            embed = discord.Embed(
                title=f"🗺️ Exploração em Cadeia [{self.pet_data['exploracao_hoje']}/10]",
                description=f"🏃 Você ignorou o perigo anterior e avançou no caminho...\n\n🌳 **Novo Bioma:** `{novo_cenario['bioma']}`\n👹 **Monstro:** `{novo_cenario['mob']}` (XP: {novo_cenario['xp']} | Gold: {novo_cenario['gold']})\n\nO que deseja fazer?",
                color=discord.Color.blue()
            )
            await interaction.response.edit_message(embed=embed, view=prox_view)
        else:
            embed_fim = discord.Embed(
                title="🏁 Exploração Diária Concluída!",
                description="✨ Você ignorou o encontro e atingiu o limite de **10/10 explorações hoje**.",
                color=discord.Color.gold()
            )
            await interaction.response.edit_message(embed=embed_fim, view=None)


# COMANDO PRINCIPAL SLASH
@app_commands.command(name="xplorar", description="[GUILDA] Explore ecossistemas para batalhar e subir de nível rápido!")
async def xplorar(self, interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    pets = load_data()

    if user_id not in pets:
        return await interaction.response.send_message("❌ Adote um Pet com `/pet_adotar` primeiro!", ephemeral=True)[span_3](start_span)[span_3](end_span)

    pet = pets[user_id]
    
    # REQUIREMENT 1: REQUISITO DE NÍVEL 15
    if pet["level"] < 15:
        return await interaction.response.send_message(
            f"🔒 **Acesso Negado!** A exploração da guilda é extrema. Seu Pet precisa ser **Nível 15+** (Nível atual: {pet['level']}).", 
            ephemeral=True
        )

    # REQUISITO 2: VERIFICAÇÃO DO LIMITE DIÁRIO
    hoje = pet.get("exploracao_hoje", 0)
    if hoje >= 10:
        return await interaction.response.send_message("⏳ Você já completou suas **10 explorações diárias**. Volte amanhã!", ephemeral=True)

    cenario_inicial = random.choice(CENARIOS_GUILDA)
    view = ExplorarView(user_id, pet, cenario_inicial, hoje)

    embed = discord.Embed(
        title=f"🗺️ Exploração da Guilda [{hoje + 1}/10]",
        description=(
            f"📍 **Ambiente:** `{cenario_inicial['bioma']}`\n"
            f"👹 **Monstro Localizado:** `{cenario_inicial['mob']}`\n"
            f"⭐ **XP Estimado:** `{cenario_inicial['xp']}` | 💰 **Gold Estimado:** `{cenario_inicial['gold']}`\n\n"
            "Escolha se deseja batalhar agora ou continuar explorando o mapa:"
        ),
        color=discord.Color.dark_purple()
    )

    await interaction.response.send_message(embed=embed, view=view)
    
    # 5. COMANDO: /duelar (PVP INTERATIVO)
    @app_commands.command(name="duelar", description="Desafie outro jogador para um duelo de Pets valendo Golds!")
    async def duelar(self, interaction: discord.Interaction, oponente: discord.Member):
        desafiante_id = str(interaction.user.id)
        oponente_id = str(oponente.id)

        if oponente.bot or desafiante_id == oponente_id:
            return await interaction.response.send_message("❌ Oponente inválido para duelo!", ephemeral=True)

        data = load_data()

        if desafiante_id not in data or oponente_id not in data:
            return await interaction.response.send_message("❌ Ambos os jogadores precisam ter um Pet para duelar!", ephemeral=True)

        embed_desafio = discord.Embed(
            title="⚔️ DESAFIO DE DUELO PVP!",
            description=f"{oponente.mention}, você foi desafiado por {interaction.user.mention}!\nO vencedor levará **+50 Golds** bônus!\n\n**Aceita o duelo?**",
            color=discord.Color.gold()
        )

        view = DuelView(interaction.user, oponente)
        await interaction.response.send_message(content=oponente.mention, embed=embed_desafio, view=view)

        await view.wait()

        if not view.aceito:
            return

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
            dano1 = max(3, int((p1_st["atq"] * mult1) - (p2_st["defesa"] / 2)) + random.randint(-2, 3))
            p2_hp -= dano1
            if p2_hp <= 0:
                p2_hp = 0
                logs.append(f"⚔️ **R{rodada}:** {p1['nome']} deu `{dano1}` de dano e finalizou o duelo!")
                break

            dano2 = max(3, int((p2_st["atq"] * mult2) - (p1_st["defesa"] / 2)) + random.randint(-2, 3))
            p1_hp -= dano2
            if p1_hp <= 0:
                p1_hp = 0
                logs.append(f"💥 **R{rodada}:** {p2['nome']} deu `{dano2}` de dano e finalizou o duelo!")
                break

            logs.append(f"⚔️ **R{rodada}:** {interaction.user.display_name} deu `{dano1}` | {oponente.display_name} deu `{dano2}`")
            rodada += 1

        p1_venceu = p2_hp <= 0
        vencedor_user = interaction.user if p1_venceu else oponente
        vencedor_pet = p1 if p1_venceu else p2
        perdedor_pet = p2 if p1_venceu else p1

        vencedor_pet.setdefault("historico", {"vitorias": 0, "derrotas": 0})
        perdedor_pet.setdefault("historico", {"vitorias": 0, "derrotas": 0})

        vencedor_pet["historico"]["vitorias"] += 1
        perdedor_pet["historico"]["derrotas"] += 1

        xp_ganho = random.randint(30, 60)
        golds_ganhos = 50
        vencedor_pet["xp"] += xp_ganho

        # Adiciona os Golds no sistema central para o vencedor
        novo_saldo_vencedor = economy.add_gold(vencedor_user.id, golds_ganhos)

        save_data(data)

        embed_resultado = discord.Embed(
            title=f"🏆 {vencedor_user.display_name} VENCEU O DUELO!",
            description="\n".join(logs),
            color=discord.Color.gold()
        )
        embed_resultado.add_field(
            name="🎁 Recompensa do Vencedor", 
            value=f"**+{xp_ganho} XP** | 💰 **+{golds_ganhos} Golds**\n*(Saldo atual: {novo_saldo_vencedor:,} Golds)*", 
            inline=False
        )

        await interaction.followup.send(embed=embed_resultado)

    # 6. COMANDO: /loja (COMPRA DE ITENS)
    @app_commands.command(name="loja", description="Compre itens com seus Golds para melhorar seu Pet!")
    @app_commands.choices(item=[
        app_commands.Choice(name="🧪 Poção de Cura (+50 HP Atual) - 60 Golds", value="pocao"),
        app_commands.Choice(name="🥩 Super Ração (+150 XP) - 100 Golds", value="racao"),
        app_commands.Choice(name="⚔️ Amuleto de Força (+5 ATQ Permanente) - 250 Golds", value="amuleto")
    ])
    async def loja(self, interaction: discord.Interaction, item: app_commands.Choice[str]):
        user_id = str(interaction.user.id)
        data = load_data()

        if user_id not in data:
            return await interaction.response.send_message("❌ Você precisa ter um Pet para usar a loja! Use `/pet_adotar`.", ephemeral=True)

        pet = data[user_id]
        precos = {"pocao": 60, "racao": 100, "amuleto": 250}
        custo = precos[item.value]

        # Tenta debitar o valor do banco central de Golds
        if not economy.remove_gold(interaction.user.id, custo):
            saldo_atual = economy.get_gold(interaction.user.id)
            return await interaction.response.send_message(
                f"❌ Você não tem Golds suficientes! Seu saldo atual é de **{saldo_atual:,} Golds**.", 
                ephemeral=True
            )

        msg_extra = ""

        # Aplica efeito do item
        if item.value == "pocao":
            pet["stats"]["hp_atual"] = min(pet["stats"]["hp_max"], pet["stats"]["hp_atual"] + 50)
            msg_extra = f"❤️ O HP do seu Pet foi restaurado para **{pet['stats']['hp_atual']}/{pet['stats']['hp_max']}**!"

        elif item.value == "racao":
            pet["xp"] += 150
            msg_extra = "🎉 Seu Pet recebeu **+150 XP**!"
            # Checa level up
            xp_necessario = pet["level"] * 100
            if pet["xp"] >= xp_necessario:
                pet["xp"] -= xp_necessario
                pet["level"] += 1
                pet["stats"]["hp_max"] += 10
                pet["stats"]["atq"] += 3
                pet["stats"]["defesa"] += 2
                msg_extra += f"\n🎊 **LEVEL UP!** Seu Pet alcançou o **Nível {pet['level']}**!"

        elif item.value == "amuleto":
            pet["stats"]["atq"] += 5
            msg_extra = f"⚔️ O Ataque permanente do seu Pet aumentou para **{pet['stats']['atq']}**!"

        save_data(data)

        saldo_restante =  economy.get_gold(interaction.user.id)

        embed = discord.Embed(
            title="🛒 COMPRA REALIZADA COM SUCESSO!",
            description=f"Você comprou **{item.name.split(' - ')[0]}** por **{custo} Golds**!\n\n{msg_extra}",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Saldo restante na carteira: {saldo_restante:,} Golds")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(PetRPG(bot))
