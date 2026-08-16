import os
import json
import random
import discord
from discord import app_commands
from discord.ext import commands

# Presumindo que 'economy' esteja importado no seu ecossistema
# import economy

# ==========================================
# GERENCIAMENTO DE DADOS DO WORLD BOSS
# ==========================================
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


# ==========================================
# GERENCIAMENTO DE DADOS DOS PETS (pets.json)
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PETS_FILE = os.path.join(BASE_DIR, "pets.json")

def load_data():
    if not os.path.exists(PETS_FILE):
        return {}
    with open(PETS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_data(data):
    with open(PETS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ==========================================
# BANCO DE 40 CENÁRIOS E MONSTROS DE GUILDA
# ==========================================
CENARIOS_GUILDA = [
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
    {"bioma": "Labirinto de Espinhos", "mob": "Mímico Vegetal", "hp": 165, "atq": 33, "def": 9, "xp": 155, "gold": 130},
    {"bioma": "Vale dos Ossos", "mob": "Quimera Reanimada", "hp": 230, "atq": 39, "def": 16, "xp": 225, "gold": 175},
    {"bioma": "Pico Tempestuoso", "mob": "Roc dos Céus", "hp": 190, "atq": 37, "def": 11, "xp": 195, "gold": 145},
    {"bioma": "Abismo Coralino", "mob": "Kraken Juvenil", "hp": 260, "atq": 31, "def": 20, "xp": 230, "gold": 190},
    {"bioma": "Catacumbas Reais", "mob": "Múmia do Faraó", "hp": 175, "atq": 35, "def": 13, "xp": 180, "gold": 210},
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
    {"bioma": "Cratera Meteórica", "mob": "Verme Estelar", "hp": 250, "atq": 43, "def": 19, "xp": 250, "gold": 220},
    {"bioma": "Fenda Marítima", "mob": "Tubarão Martelo Mutante", "hp": 205, "atq": 40, "def": 13, "xp": 215, "gold": 170},
    {"bioma": "Vilarejo Fantasma", "mob": "Banshee Lacerante", "hp": 120, "atq": 45, "def": 6, "xp": 180, "gold": 165},
    {"bioma": "Fortaleza Esquecida", "mob": "Cavaleiro sem Cabeça", "hp": 220, "atq": 42, "def": 18, "xp": 240, "gold": 200},
    {"bioma": "Núcleo de Yggdrasil", "mob": "Avatar Corrompido", "hp": 300, "atq": 48, "def": 25, "xp": 300, "gold": 280}
]


# ==========================================
# INTERFACE DE NAVEGAÇÃO DA EXPLORAÇÃO (COM CURA RÁPIDA)
# ==========================================
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
        
        dano_pet = max(5, st["atq"] - mob["def"]) + random.randint(1, 10)
        self.pet_data["exploracao_hoje"] = self.progresso + 1
        
        if dano_pet >= (mob["hp"] / 3):
            xp_ganho = mob["xp"]
            gold_ganho = mob["gold"]
            
            self.pet_data["xp"] += xp_ganho
            lvl = self.pet_data["level"]
            xp_necessario = (lvl * 300) if lvl >= 20 else (lvl * 100)
            
            subiu = False
            if self.pet_data["xp"] >= xp_necessario:
                self.pet_data["xp"] -= xp_necessario
                self.pet_data["level"] += 1
                subiu = True

            economy.add_gold(interaction.user.id, gold_ganho)
            data = load_data()
            data[self.user_id] = self.pet_data
            save_data(data)

            txt_resultado = f"✅ **Vitória!** Você derrotou o **{mob['mob']}**!\n🎁 **Recompensas:** +{xp_ganho} XP | +{gold_ganho} Golds"
            if subiu:
                txt_resultado += f"\n🎊 **LEVEL UP!** Seu pet alcançou o **Nível {self.pet_data['level']}**!"
            
            if self.pet_data["exploracao_hoje"] < 10:
                novo_cenario = random.choice(CENARIOS_GUILDA)
                prox_view = ExplorarView(self.user_id, self.pet_data, novo_cenario, self.pet_data["exploracao_hoje"])
                
                embed_prox = discord.Embed(
                    title=f"🗺️ Exploração em Cadeia [{self.pet_data['exploracao_hoje']}/10]",
                    description=f"{txt_resultado}\n\n---\n🌳 **Novo Bioma:** `{novo_cenario['bioma']}`\n👹 **Monstro:** `{novo_cenario['mob']}` (XP: {novo_cenario['xp']} | Gold: {novo_cenario['gold']})\n\nO que deseja fazer?",
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
        else:
            data = load_data()
            data[self.user_id] = self.pet_data
            save_data(data)
            embed_derrota = discord.Embed(
                title="💀 Derrotado na Exploração...",
                description=f"O **{mob['mob']}** era forte demais! Seu pet recuou para se recuperar.",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed_derrota, view=None)

    @discord.ui.button(label="🧪 Usar Poção", style=discord.ButtonStyle.success)
    async def usar_pocao(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Esta exploração não é sua!", ephemeral=True)

        inv = self.pet_data.setdefault("inventario", {"pocao": 0})
        if inv.get("pocao", 0) <= 0:
            return await interaction.response.send_message("❌ Você não tem nenhuma **🧪 Poção de Cura** na sua mochila! Compre na `/loja`.", ephemeral=True)

        inv["pocao"] -= 1
        st = self.pet_data["stats"]
        st["hp_atual"] = min(st["hp_max"], st["hp_atual"] + 50)
        
        data = load_data()
        data[self.user_id] = self.pet_data
        save_data(data)

        await interaction.response.send_message(f"🧪 **Poção Usada!** O HP de {self.pet_data['nome']} foi restaurado para `{st['hp_atual']}/{st['hp_max']}`! (Restantes: {inv['pocao']})", ephemeral=True)

    @discord.ui.button(label="🏃 Continuar Explorando", style=discord.ButtonStyle.secondary)
    async def pular(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Esta exploração não é sua!", ephemeral=True)

        self.pet_data["exploracao_hoje"] = self.progresso + 1
        data = load_data()
        data[self.user_id] = self.pet_data
        save_data(data)

        if self.pet_data["exploracao_hoje"] < 10:
            novo_cenario = random.choice(CENARIOS_GUILDA)
            prox_view = ExplorarView(self.user_id, self.pet_data, novo_cenario, self.pet_data["exploracao_hoje"])
            
            embed = discord.Embed(
                title=f"🗺️ Exploração em Cadeia [{self.pet_data['exploracao_hoje']}/10]",
                description=f"🏃 Você ignorou o perigo anterior e avançou...\n\n🌳 **Novo Bioma:** `{novo_cenario['bioma']}`\n👹 **Monstro:** `{novo_cenario['mob']}` (XP: {novo_cenario['xp']} | Gold: {novo_cenario['gold']})\n\nO que deseja fazer?",
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


# ==========================================
# CLASSE PRINCIPAL PET RPG (COG)
# ==========================================
class PetRPG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="foguinho", description="🔥 Invoca o poder do pet Foguinho/Faisquinha.")
    async def foguinho(self, interaction: discord.Interaction):
        # Evita o erro de timeout do Discord enquanto processa os dados
        await interaction.response.defer()

        user_id = str(interaction.user.id)
        pets_data = self._load_pets()

        # Verifica se o usuário tem o pet cadastrado
        if user_id not in pets_data:
            return await interaction.followup.send("⚠️ Você ainda não possui um pet registrado no sistema!")

        pet = pets_data[user_id]

        embed = discord.Embed(
            title=f"🔥 Painel do Pet: {pet.get('nome', 'Foguinho')}",
            description=f"**Raça:** {pet.get('raça', 'Faisquinha')}\n**Elemento:** `{pet.get('elemento', 'fogo')}`",
            color=discord.Color.orange()
        )
        
        if pet.get('midia'):
            embed.set_thumbnail(url=pet.get('midia'))

        stats = pet.get("stats", {})
        embed.add_field(name="⭐ Nível", value=str(pet.get("level", 1)), inline=True)
        embed.add_field(name="✨ XP", value=str(pet.get("xp", 0)), inline=True)
        embed.add_field(name="❤️ HP", value=f"{stats.get('hp_atual', 100)}/{stats.get('hp_max', 100)}", inline=True)
        embed.add_field(name="⚔️ Ataque", value=str(stats.get('atq', 0)), inline=True)
        embed.add_field(name="🛡️ Defesa", value=str(stats.get('defesa', 0)), inline=True)
        embed.add_field(name="💨 Agilidade", value=str(stats.get('agi', 0)), inline=True)

        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(FoguinhoCog(bot))

    # 1. COMANDO: /masmorra
    @app_commands.command(name="masmorra", description="Enfrente monstros em uma masmorra para ganhar XP e Golds!")
    @app_commands.choices(dificuldade=[
        app_commands.Choice(name="🟢 Caverna Tranquila (Fácil)", value="facil"),
        app_commands.Choice(name="🟡 Floresta Fechada (Média)", value="medio"),
        app_commands.Choice(name="🔴 Vulcão Infernal (Difícil)", value="dificil")
    ])
    @app_commands.checks.cooldown(1, 1800, key=lambda i: i.user.id)
    async def masmorra(self, interaction: discord.Interaction, dificuldade: str):
        user_id = str(interaction.user.id)
        data = load_data()

        if user_id not in data:
            return await interaction.response.send_message("❌ Você precisa ter um Pet! Use `/pet_adotar` primeiro.", ephemeral=True)

        pet = data[user_id]
        st = pet["stats"]

        if st.get("hp_atual", st["hp_max"]) <= 0:
            return await interaction.response.send_message("💀 Seu Pet está desmaiado! Compre uma **🧪 Poção de Cura** na `/loja` antes de tentar batalhar.", ephemeral=True)

        monstros = {
            "facil": {"nome": "Slime Solitário", "hp": 50, "atq": 12, "def": 3, "elemento": "agua", "xp_min": 25, "xp_max": 45, "gold_min": 20, "gold_max": 40},
            "medio": {"nome": "Lobo das Sombras", "hp": 100, "atq": 22, "def": 8, "elemento": "trovao", "xp_min": 55, "xp_max": 95, "gold_min": 50, "gold_max": 90},
            "dificil": {"nome": "Dragão Flamejante", "hp": 170, "atq": 35, "def": 15, "elemento": "fogo", "xp_min": 110, "xp_max": 200, "gold_min": 120, "gold_max": 220}
        }

        mob = monstros[dificuldade].copy()
        pet_hp = st.get("hp_atual", st["hp_max"])
        mob_hp = mob["hp"]
        
        vantagens = {"fogo": "trovao", "trovao": "agua", "agua": "fogo"}
        mult_pet = 1.3 if vantagens.get(pet["elemento"]) == mob["elemento"] else 1.0
        mult_mob = 1.3 if vantagens.get(mob["elemento"]) == pet["elemento"] else 1.0

        logs = []
        rodada = 1

        while pet_hp > 0 and mob_hp > 0 and rodada <= 8:
            chance_crit = min(st.get("agi", 5), 50)
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

            chance_esquiva = min(st.get("agi", 5), 40)
            is_esquiva = random.randint(1, 100) <= chance_esquiva
            
            if is_esquiva:
                logs.append(f"💨 **R{rodada}:** Seu Pet usou sua agilidade e **ESQUIVOU** do ataque!")
            else:
                dano_mob = max(3, int((mob["atq"] * mult_mob) - (st["defesa"] / 2)) + random.randint(-2, 3))
                pet_hp -= dano_mob
                if pet_hp <= 0:
                    pet_hp = 0
                    logs.append(f"💥 **R{rodada}:** **{mob['nome']}** te causou `{dano_mob}` de dano e te nocauteou!")
                    break
                logs.append(f"⚔️ **R{rodada}:** {crit_msg}Pet deu `{dano_pet}` dano | **Mob** deu `{dano_mob}` dano.")
            
            rodada += 1

        pet["stats"]["hp_atual"] = pet_hp
        vitoria = mob_hp <= 0
        pet.setdefault("historico", {"vitorias": 0, "derrotas": 0})

        if vitoria:
            xp_ganho = random.randint(mob["xp_min"], mob["xp_max"])
            golds_ganhos = random.randint(mob["gold_min"], mob["gold_max"])
            pet["xp"] += xp_ganho
            pet["historico"]["vitorias"] += 1

            novo_saldo = economy.add_gold(interaction.user.id, golds_ganhos)
            
            lvl = pet["level"]
            xp_necessario = (lvl * 300) if lvl >= 20 else (lvl * 100)
            subiu = False
            while pet["xp"] >= xp_necessario:
                pet["xp"] -= xp_necessario
                pet["level"] += 1
                subiu = True
                pet["stats"]["hp_max"] += 10
                pet["stats"]["hp_atual"] = pet["stats"]["hp_max"]
                pet["stats"]["atq"] += 3
                pet["stats"]["defesa"] += 2
                lvl = pet["level"]
                xp_necessario = (lvl * 300) if lvl >= 20 else (lvl * 100)

            save_data(data)

            embed = discord.Embed(
                title=f"🏰 VITÓRIA NA MASMORRA!",
                description=f"**Desafio:** {dificuldade.capitalize()}\n\n" + "\n".join(logs),
                color=discord.Color.green()
            )
            embed.add_field(name="🎁 Recompensas", value=f"**+{xp_ganho} XP** | 💰 **+{golds_ganhos} Golds**\n*(Saldo total: {novo_saldo:,} Golds)*", inline=False)
            embed.set_footer(text=f"HP Restante do seu Pet: {pet_hp}/{st['hp_max']}")
            if subiu:
                embed.add_field(name="🎊 LEVEL UP!", value=f"Seu Pet subiu para o **Nível {pet['level']}** e curou o HP!", inline=False)
        else:
            pet["historico"]["derrotas"] += 1
            punicao_txt = ""
            if dificuldade == "dificil":
                saldo_atual = economy.get_gold(interaction.user.id)
                punicao_gold = int(saldo_atual * 0.05)
                if punicao_gold > 0:
                    economy.remove_gold(interaction.user.id, punicao_gold)
                    punicao_txt = f"\n\n💀 **MORTE BRUTAL:** Você desmaiou no Vulcão Infernal e perdeu **{punicao_gold} Golds**!"

            save_data(data)

            embed = discord.Embed(
                title=f"💀 DERROTA NA MASMORRA...",
                description=f"**Desafio:** {dificuldade.capitalize()}\n\n" + "\n".join(logs) + punicao_txt,
                color=discord.Color.dark_red()
            )
            embed.set_footer(text="Acesse a /loja e compre uma poção para reanimar seu Pet!")

        await interaction.response.send_message(embed=embed)

    # 2. COMANDO: /xplorar
    @app_commands.command(name="xplorar", description="[GUILDA] Explore ecossistemas para batalhar e subir de nível rápido!")
    async def xplorar(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        pets = load_data()

        if user_id not in pets:
            return await interaction.response.send_message("❌ Adote um Pet com `/pet_adotar` primeiro!", ephemeral=True)

        pet = pets[user_id]
        pet.setdefault("inventario", {"pocao": 0})

        if pet["level"] < 15:
            return await interaction.response.send_message(
                f"🔒 **Acesso Negado!** A exploração da guilda é extrema. Seu Pet precisa ser **Nível 15+** (Nível atual: {pet['level']}).", 
                ephemeral=True
            )

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
                f"🎒 **Sua Mochila:** `🧪 {pet['inventario'].get('pocao', 0)} Poções`\n"
                "Escolha se deseja batalhar agora ou continuar explorando o mapa:"
            ),
            color=discord.Color.dark_purple()
        )

        await interaction.response.send_message(embed=embed, view=view)

    # 3. COMANDO: /loja (LOJA DE ITENS COM REAJUSTE DE +60 GOLDS)
    @app_commands.command(name="loja", description="Compre itens com seus Golds para melhorar seu Pet!")
    @app_commands.choices(item=[
        app_commands.Choice(name="🧪 Poção de Cura (+50 HP) - 129 Golds", value="pocao"),
        app_commands.Choice(name="🥩 Super Ração (+150 XP) - 175 Golds", value="racao"),
        app_commands.Choice(name="🛡️ Elixir de Agilidade (+3 AGI Perman.) - 291 Golds", value="elixir"),
        app_commands.Choice(name="⚔️ Amuleto de Força (+5 ATQ Perman.) - 348 Golds", value="amuleto")
    ])
    async def loja(self, interaction: discord.Interaction, item: str):
        user_id = str(interaction.user.id)
        data = load_data()

        if user_id not in data:
            return await interaction.response.send_message("❌ Você precisa ter um Pet para usar a loja! Use `/pet_adotar`.", ephemeral=True)

        pet = data[user_id]
        pet.setdefault("inventario", {"pocao": 0})
        
        # Tabela de preços com +60 Golds aplicados aos valores anteriores
        precos = {
            "pocao": 129,    # Antes: 69
            "racao": 175,    # Antes: 115
            "elixir": 291,   # Antes: 231
            "amuleto": 348   # Antes: 288
        }
        
        nomes_itens = {
            "pocao": "🧪 Poção de Cura",
            "racao": "🥩 Super Ração",
            "elixir": "🛡️ Elixir de Agilidade",
            "amuleto": "⚔️ Amuleto de Força"
        }

        custo = precos.get(item)
        if not custo:
            return await interaction.response.send_message("❌ Item inválido.", ephemeral=True)

        if not economy.remove_gold(interaction.user.id, custo):
            saldo_atual = economy.get_gold(interaction.user.id)
            return await interaction.response.send_message(
                f"❌ Você não tem Golds suficientes! O item custa **{custo} Golds** e seu saldo é de **{saldo_atual:,} Golds**.", 
                ephemeral=True
            )

        msg_extra = ""

        if item == "pocao":
            pet["inventario"]["pocao"] = pet["inventario"].get("pocao", 0) + 1
            msg_extra = f"🧪 **Poção adicionada ao seu inventário!** Você agora possui `{pet['inventario']['pocao']}` poções para usar na exploração!"

        elif item == "racao":
            pet["xp"] += 150
            msg_extra = "🎉 Seu Pet recebeu **+150 XP**!"
            lvl = pet["level"]
            xp_necessario = (lvl * 300) if lvl >= 20 else (lvl * 100)
            
            if pet["xp"] >= xp_necessario:
                pet["xp"] -= xp_necessario
                pet["level"] += 1
                pet["stats"]["hp_max"] += 10
                pet["stats"]["hp_atual"] = pet["stats"]["hp_max"]
                pet["stats"]["atq"] += 3
                pet["stats"]["defesa"] += 2
                msg_extra += f"\n🎊 **LEVEL UP!** Seu Pet alcançou o **Nível {pet['level']}**!"

        elif item == "elixir":
            pet["stats"].setdefault("agi", 5)
            pet["stats"]["agi"] += 3
            msg_extra = f"💨 A Agilidade permanente do seu Pet aumentou para **{pet['stats']['agi']}**!"

        elif item == "amuleto":
            pet["stats"]["atq"] += 5
            msg_extra = f"⚔️ O Ataque permanente do seu Pet aumentou para **{pet['stats']['atq']}**!"

        save_data(data)
        saldo_restante = economy.get_gold(interaction.user.id)

        embed = discord.Embed(
            title="🛒 COMPRA REALIZADA COM SUCESSO!",
            description=f"Você comprou **{nomes_itens[item]}** por **{custo} Golds**!\n\n{msg_extra}",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Saldo restante na carteira: {saldo_restante:,} Golds")

        await interaction.response.send_message(embed=embed)
    
   # 4. COMANDO: /top_pets (LENDO DIRECTAMENTE DE PETS.JSON)
    @app_commands.command(name="top_pets", description="Exibe o ranking global dos Pets mais fortes do servidor!")
    async def top_pets(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            data = load_data()

            if not data:
                return await interaction.followup.send("📊 Nenhum Pet encontrado em `pets.json`!", ephemeral=True)

            # Ordena pelos pets de maior Level e XP
            sorted_pets = sorted(
                data.items(), 
                key=lambda item: (item[1].get("level", 1), item[1].get("xp", 0)), 
                reverse=True
            )

            medals = ["🥇", "🥈", "🥉"]
            ranking_txt = []

            for index, (uid, pet) in enumerate(sorted_pets[:10], start=1):
                emoji = medals[index - 1] if index <= 3 else f"`#{index}`"
                
                # Resgate do dono no Discord
                user = self.bot.get_user(int(uid))
                if user:
                    dono_nome = user.display_name
                else:
                    try:
                        user = await self.bot.fetch_user(int(uid))
                        dono_nome = user.display_name
                    except Exception:
                        dono_nome = f"Treinador_{uid[-4:]}"
                
                # Dados lidos do JSON
                nome = pet.get("nome", "Pet sem nome")
                raca = pet.get("raça", "Desconhecida")
                elemento = pet.get("elemento", "Nenhum").capitalize()
                level = pet.get("level", 1)
                xp = pet.get("xp", 0)
                
                stats = pet.get("stats", {})
                atq = stats.get("atq", 0)
                defesa = stats.get("defesa", 0)
                agi = stats.get("agi", 0)

                ranking_txt.append(
                    f"{emoji} **{nome}** *(Lv. {level})* — Dono: **{dono_nome}**\n"
                    f"└ 🐾 Raça: `{raca}` | 🔮 Elemento: `{elemento}`\n"
                    f"└ ⚔️ ATQ: `{atq:,}` | 🛡️ DEF: `{defesa:,}` | 💨 AGI: `{agi:,}` | ⭐ XP: `{xp:,}`"
                )

            embed = discord.Embed(
                title="🏆 RANKING GLOBAL DE PETS",
                description="\n\n".join(ranking_txt),
                color=discord.Color.gold()
            )
            embed.set_footer(text="Treine seu Pet na /masmorra e no /xplorar para subir no ranking!")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao ler `pets.json`: `{e}`", ephemeral=True)

    # 5. COMANDOS DO WORLD BOSS
    @app_commands.command(name="set_boss", description="[ADMIN] Invoca um novo World Boss para o servidor!")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_boss(self, interaction: discord.Interaction, nome: str, hp_total: int, premio_golds: int):
        boss_data = {
            "nome": nome,
            "hp_max": hp_total,
            "hp_atual": hp_total,
            "premio_golds": premio_golds,
            "ativo": True,
            "dano_jogadores": {}
        }
        save_boss(boss_data)

        embed = discord.Embed(
            title="🔥 UM NOVO WORLD BOSS APARECEU!",
            description=(
                f"Um inimigo colossal despertou em Yggdrasil!\n\n"
                f"👹 **Boss:** `{nome}`\n"
                f"❤️ **Vida Total:** `{hp_total:,}` HP\n"
                f"💰 **Pool de Recompensas:** `{premio_golds:,}` Golds\n\n"
                "⚔️ Use o comando `/atacar_boss` para dar dano e garantir sua fatia do prêmio!"
            ),
            color=discord.Color.dark_red()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="atacar_boss", description="Ataque o World Boss ativo e acumule dano no ranking!")
    @app_commands.checks.cooldown(1, 600, key=lambda i: i.user.id)
    async def atacar_boss(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        pets = load_data()

        if user_id not in pets:
            return await interaction.response.send_message("❌ Você precisa adotar um Pet primeiro com `/pet_adotar`!", ephemeral=True)

        pet = pets[user_id]
        st = pet["stats"]

        if st.get("hp_atual", st["hp_max"]) <= 0:
            return await interaction.response.send_message("💀 Seu Pet está desmaiado! Use uma **🧪 Poção de Cura** na `/loja`.", ephemeral=True)

        boss = load_boss()
        if not boss or not boss.get("ativo", False):
            return await interaction.response.send_message("😴 Não há nenhum World Boss ativo no momento.", ephemeral=True)

        dano_base = random.randint(st["atq"], st["atq"] * 2)
        chance_crit = min(st.get("agi", 5), 50)
        is_crit = random.randint(1, 100) <= chance_crit
        
        crit_msg = ""
        if is_crit:
            dano_base = int(dano_base * 1.5)
            crit_msg = "🎯 **CRÍTICO!** "

        boss["hp_atual"] -= dano_base
        
        if user_id not in boss["dano_jogadores"]:
            boss["dano_jogadores"][user_id] = {"nome": interaction.user.display_name, "dano": 0}
        boss["dano_jogadores"][user_id]["dano"] += dano_base

        if boss["hp_atual"] <= 0:
            boss["hp_atual"] = 0
            boss["ativo"] = False
            save_boss(boss)

            total_dano = sum(p["dano"] for p in boss["dano_jogadores"].values())
            premio_pool = boss["premio_golds"]

            resumo_recompensas = []
            for uid, info in boss["dano_jogadores"].items():
                porcentagem = info["dano"] / total_dano
                golds_ganhos = int(premio_pool * porcentagem)
                economy.add_gold(int(uid), golds_ganhos)
                resumo_recompensas.append(f"• **{info['nome']}**: `{info['dano']:,}` dano ({porcentagem:.1%}) ➔ **+{golds_ganhos:,} Golds** 💰")

            embed_vitoria = discord.Embed(
                title=f"🎉 O WORLD BOSS {boss['nome'].upper()} FOI DERROTADO!",
                description=(
                    f"⚔️ **Ataque Final por:** {interaction.user.mention} ({crit_msg}`{dano_base:,}` de dano!)\n\n"
                    "🏆 **DISTRIBUIÇÃO DE RECOMPENSAS:**\n" + "\n".join(resumo_recompensas)
                ),
                color=discord.Color.gold()
            )
            return await interaction.response.send_message(embed_vitoria)

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


async def setup(bot):
    await bot.add_cog(PetRPG(bot))
