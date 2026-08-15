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
