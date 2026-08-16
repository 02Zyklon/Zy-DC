import os
import json
import random
from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands

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
# CLASSE AUXILIAR DE ECONOMIA (Fallback Seguro)
# ==========================================
class SafeEconomy:
    @staticmethod
    def add_gold(user_id, amount):
        eco_file = "economy.json"
        data = {}
        if os.path.exists(eco_file):
            try:
                with open(eco_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except:
                pass
        uid = str(user_id)
        data[uid] = data.get(uid, 0) + amount
        with open(eco_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        return data[uid]

    @staticmethod
    def remove_gold(user_id, amount):
        eco_file = "economy.json"
        data = {}
        if os.path.exists(eco_file):
            try:
                with open(eco_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except:
                pass
        uid = str(user_id)
        current = data.get(uid, 0)
        if current < amount:
            return False
        data[uid] = current - amount
        with open(eco_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        return True

    @staticmethod
    def get_gold(user_id):
        eco_file = "economy.json"
        if os.path.exists(eco_file):
            try:
                with open(eco_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get(str(user_id), 0)
            except:
                pass
        return 0

economy = SafeEconomy()


# ==========================================
# INTERFACE DE NAVEGAÇÃO DA EXPLORAÇÃO
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

        await interaction.response.defer()

        st = self.pet_data.setdefault("stats", {"atq": 10, "def": 5, "hp_max": 100, "hp_atual": 100, "agi": 5, "defesa": 5})
        mob = self.cenario
        
        dano_pet = max(5, st.get("atq", 10) - mob["def"]) + random.randint(1, 10)
        self.pet_data["exploracao_hoje"] = self.progresso + 1
        
        if dano_pet >= (mob["hp"] / 3):
            xp_ganho = mob["xp"]
            gold_ganho = mob["gold"]
            
            self.pet_data["xp"] = self.pet_data.get("xp", 0) + xp_ganho
            lvl = self.pet_data.get("level", 1)
            xp_necessario = (lvl * 300) if lvl >= 20 else (lvl * 100)
            
            subiu = False
            if self.pet_data["xp"] >= xp_necessario:
                self.pet_data["xp"] -= xp_necessario
                self.pet_data["level"] = lvl + 1
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
                await interaction.edit_original_response(embed=embed_prox, view=prox_view)
            else:
                embed_fim = discord.Embed(
                    title="🏁 Exploração Diária Concluída!",
                    description=f"{txt_resultado}\n\n✨ Você atingiu o limite de **10/10 explorações hoje**. Volte amanhã!",
                    color=discord.Color.gold()
                )
                await interaction.edit_original_response(embed=embed_fim, view=None)
        else:
            data = load_data()
            data[self.user_id] = self.pet_data
            save_data(data)
            embed_derrota = discord.Embed(
                title="💀 Derrotado na Exploração...",
                description=f"O **{mob['mob']}** era forte demais! Seu pet recuou para se recuperar.",
                color=discord.Color.red()
            )
            await interaction.edit_original_response(embed=embed_derrota, view=None)

    @discord.ui.button(label="🧪 Usar Poção", style=discord.ButtonStyle.success)
    async def usar_pocao(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Esta exploração não é sua!", ephemeral=True)

        inv = self.pet_data.setdefault("inventario", {"pocao": 0})
        if inv.get("pocao", 0) <= 0:
            return await interaction.response.send_message("❌ Você não tem nenhuma **🧪 Poção de Cura** na sua mochila! Compre na `/loja`.", ephemeral=True)

        inv["pocao"] -= 1
        st = self.pet_data.setdefault("stats", {"hp_max": 100, "hp_atual": 100})
        st["hp_atual"] = min(st.get("hp_max", 100), st.get("hp_atual", 100) + 50)
        
        data = load_data()
        data[self.user_id] = self.pet_data
        save_data(data)

        await interaction.response.send_message(f"🧪 **Poção Usada!** O HP de {self.pet_data.get('nome', 'Pet')} foi restaurado para `{st['hp_atual']}/{st.get('hp_max', 100)}`! (Restantes: {inv['pocao']})", ephemeral=True)

    @discord.ui.button(label="🏃 Continuar Explorando", style=discord.ButtonStyle.secondary)
    async def pular(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Esta exploração não é sua!", ephemeral=True)

        await interaction.response.defer()

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
            await interaction.edit_original_response(embed=embed, view=prox_view)
        else:
            embed_fim = discord.Embed(
                title="🏁 Exploração Diária Concluída!",
                description="✨ Você ignorou o encontro e atingiu o limite de **10/10 explorações hoje**.",
                color=discord.Color.gold()
            )
            await interaction.edit_original_response(embed=embed_fim, view=None)


# ==========================================
# CLASSE PRINCIPAL PET RPG (COG)
# ==========================================
class PetRPG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _load_pets(self):
        return load_data()

    # 1. COMANDO: /foguinho (Protegido com bloqueio de 1 uso diário)
    @app_commands.command(name="foguinho", description="🔥 Invoca o poder e status diário do seu pet.")
    async def foguinho(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user_id = str(interaction.user.id)
        pets_data = self._load_pets()

        if user_id not in pets_data:
            return await interaction.followup.send("⚠️ Você ainda não possui um pet registrado no sistema!")

        pet = pets_data[user_id]

        # Trava de uso diário para o foguinho/recompensa
        data_atual = datetime.now().strftime("%Y-%m-%d")
        if pet.get("ultima_foguinho_data") == data_atual:
            return await interaction.followup.send("⏳ Você já consultou o `/foguinho` hoje! Volte amanhã para renovar as energias.")

        pet["ultima_foguinho_data"] = data_atual
        save_data(pets_data)

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

    @app_commands.command(name="pet_adotar", description="Adote um novo Pet para iniciar suas aventuras!")
    async def pet_adotar(self, interaction: discord.Interaction, nome: str, raca: str, elemento: str):
        # 1. Responde imediatamente ao Discord para evitar o erro de "Aplicativo não respondeu"
        await interaction.response.defer(ephemeral=True)

        user_id = str(interaction.user.id)
        pets_data = load_data()

        if user_id in pets_data:
            return await interaction.followup.send("❌ Você já possui um Pet registrado! Use `/foguinho` para ver seus status.")

        # 2. Criação do pet com atributos iniciais seguros
        pets_data[user_id] = {
            "nome": nome,
            "raça": raca,
            "elemento": elemento.lower(),
            "level": 1,
            "xp": 0,
            "stats": {
                "hp_max": 100,
                "hp_atual": 100,
                "atq": 15,
                "defesa": 5,
                "agi": 10
            },
            "inventario": {"pocao": 1},
            "historico": {"vitorias": 0, "derrotas": 0}
        }

        save_data(pets_data)

        # 3. Envia a resposta final com segurança via followup
        embed = discord.Embed(
            title="🎉 ADOÇÃO REALIZADA COM SUCESSO!",
            description=(
                f"Parabéns! Você adotou o seu novo companheiro:\n\n"
                f"🐾 **Nome:** `{nome}`\n"
                f"🧬 **Raça:** `{raca}`\n"
                f"🔮 **Elemento:** `{elemento.capitalize()}`\n\n"
                "Use `/foguinho` para ver os detalhes ou vá para `/masmorra`!"
            ),
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)

    # 2. COMANDO: /daily (Recompensa diária protegida contra fraude)
    @app_commands.command(name="daily", description="🎁 Coleta sua recompensa diária em Golds para o seu pet!")
    async def daily(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        pets_data = load_data()

        if user_id not in pets_data:
            return await interaction.response.send_message("❌ Você precisa adotar um Pet com `/pet_adotar` primeiro para resgatar o daily!", ephemeral=True)

        pet = pets_data[user_id]
        data_atual = datetime.now().strftime("%Y-%m-%d")

        if pet.get("ultimo_daily_data") == data_atual:
            return await interaction.response.send_message("⏳ Você já resgatou sua recompensa `/daily` hoje! Volte amanhã.", ephemeral=True)

        pet["ultimo_daily_data"] = data_atual
        save_data(pets_data)

        golds_ganhos = random.randint(200, 500)
        novo_saldo = economy.add_gold(interaction.user.id, golds_ganhos)

        embed = discord.Embed(
            title="🎁 RECOMPENSA DIÁRIA COLETADA!",
            description=f"Você resgatou com sucesso o seu **`/daily`**!\n\n💰 **Prêmio:** `+{golds_ganhos} Golds`\n💼 **Novo Saldo:** `{novo_saldo:,} Golds`",
            color=discord.Color.gold()
        )
        embed.set_footer(text="Volte amanhã para resgatar novamente!")
        await interaction.response.send_message(embed=embed)

    # 3. COMANDO: /masmorra
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
        st = pet.setdefault("stats", {"hp_max": 100, "hp_atual": 100, "atq": 10, "defesa": 5, "agi": 5})

        if st.get("hp_atual", st.get("hp_max", 100)) <= 0:
            return await interaction.response.send_message("💀 Seu Pet está desmaiado! Compre uma **🧪 Poção de Cura** na `/loja` antes de tentar batalhar.", ephemeral=True)

        await interaction.response.defer()

        monstros = {
            "facil": {"nome": "Slime Solitário", "hp": 50, "atq": 12, "def": 3, "elemento": "agua", "xp_min": 25, "xp_max": 45, "gold_min": 20, "gold_max": 40},
            "medio": {"nome": "Lobo das Sombras", "hp": 100, "atq": 22, "def": 8, "elemento": "trovao", "xp_min": 55, "xp_max": 95, "gold_min": 50, "gold_max": 90},
            "dificil": {"nome": "Dragão Flamejante", "hp": 170, "atq": 35, "def": 15, "elemento": "fogo", "xp_min": 110, "xp_max": 200, "gold_min": 120, "gold_max": 220}
        }

        mob = monstros[dificuldade].copy()
        pet_hp = st.get("hp_atual", st.get("hp_max", 100))
        mob_hp = mob["hp"]
        
        vantagens = {"fogo": "trovao", "trovao": "agua", "agua": "fogo"}
        mult_pet = 1.3 if vantagens.get(pet.get("elemento")) == mob["elemento"] else 1.0
        mult_mob = 1.3 if vantagens.get(mob["elemento"]) == pet.get("elemento") else 1.0

        logs = []
        rodada = 1

        while pet_hp > 0 and mob_hp > 0 and rodada <= 8:
            chance_crit = min(st.get("agi", 5), 50)
            is_crit = random.randint(1, 100) <= chance_crit
            dano_pet = max(3, int((st.get("atq", 10) * mult_pet) - (mob["def"] / 2)) + random.randint(-2, 3))
            
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
                dano_mob = max(3, int((mob["atq"] * mult_mob) - (st.get("defesa", 5) / 2)) + random.randint(-2, 3))
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
            pet["xp"] = pet.get("xp", 0) + xp_ganho
            pet["historico"]["vitorias"] += 1

            novo_saldo = economy.add_gold(interaction.user.id, golds_ganhos)
            
            lvl = pet.get("level", 1)
            xp_necessario = (lvl * 300) if lvl >= 20 else (lvl * 100)
            subiu = False
            while pet["xp"] >= xp_necessario:
                pet["xp"] -= xp_necessario
                pet["level"] = lvl + 1
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
            embed.set_footer(text=f"HP Restante do seu Pet: {pet_hp}/{st.get('hp_max', 100)}")
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

        await interaction.followup.send(embed=embed)

    # 4. COMANDO: /xplorar (Com Trava de Limite Diário Corrigida)
    @app_commands.command(name="xplorar", description="[GUILDA] Explore ecossistemas para batalhar e subir de nível rápido!")
    async def xplorar(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        pets = load_data()

        if user_id not in pets:
            return await interaction.response.send_message("❌ Adote um Pet com `/pet_adotar` primeiro!", ephemeral=True)

        pet = pets[user_id]
        pet.setdefault("inventario", {"pocao": 0})

        if pet.get("level", 1) < 15:
            return await interaction.response.send_message(
                f"🔒 **Acesso Negado!** A exploração da guilda é extrema. Seu Pet precisa ser **Nível 15+** (Nível atual: {pet.get('level', 1)}).", 
                ephemeral=True
            )

        data_atual = datetime.now().strftime("%Y-%m-%d")
        ultima_data = pet.get("ultima_exploracao_data", "")

        if ultima_data == data_atual and pet.get("exploracao_hoje", 0) >= 10:
            return await interaction.response.send_message("⏳ Você já completou suas **10 explorações diárias**. Volte amanhã!", ephemeral=True)

        if ultima_data != data_atual:
            pet["ultima_exploracao_data"] = data_atual
            pet["exploracao_hoje"] = 0
            save_data(pets)

        hoje = pet.get("exploracao_hoje", 0)

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

    # 5. COMANDO: /loja
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
        pet.setdefault("stats", {"hp_max": 100, "hp_atual": 100, "atq": 10, "defesa": 5, "agi": 5})
        
        precos = {
            "pocao": 129,
            "racao": 175,
            "elixir": 291,
            "amuleto": 348
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
            pet["xp"] = pet.get("xp", 0) + 150
            msg_extra = "🎉 Seu Pet recebeu **+150 XP**!"
            lvl = pet.get("level", 1)
            xp_necessario = (lvl * 300) if lvl >= 20 else (lvl * 100)
            
            if pet["xp"] >= xp_necessario:
                pet["xp"] -= xp_necessario
                pet["level"] = lvl + 1
                pet["stats"]["hp_max"] += 10
                pet["stats"]["hp_atual"] = pet["stats"]["hp_max"]
                pet["stats"]["atq"] += 3
                pet["stats"]["defesa"] += 2
                msg_extra += f"\n🎊 **LEVEL UP!** Seu Pet alcançou o **Nível {pet['level']}**!"

        elif item == "elixir":
            pet["stats"]["agi"] = pet["stats"].get("agi", 5) + 3
            msg_extra = f"💨 A Agilidade permanente do seu Pet aumentou para **{pet['stats']['agi']}**!"

        elif item == "amuleto":
            pet["stats"]["atq"] = pet["stats"].get("atq", 10) + 5
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
    
    # 6. COMANDO: /top_pets
    @app_commands.command(name="top_pets", description="Exibe o ranking global dos Pets mais fortes do servidor!")
    async def top_pets(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            data = load_data()

            if not data:
                return await interaction.followup.send("📊 Nenhum Pet encontrado em `pets.json`!", ephemeral=True)

            sorted_pets = sorted(
                data.items(), 
                key=lambda item: (item[1].get("level", 1), item[1].get("xp", 0)), 
                reverse=True
            )

            medals = ["🥇", "🥈", "🥉"]
            ranking_txt = []

            for index, (uid, pet) in enumerate(sorted_pets[:10], start=1):
                emoji = medals[index - 1] if index <= 3 else f"`#{index}`"
                
                user = self.bot.get_user(int(uid))
                if user:
                    dono_nome = user.display_name
                else:
                    try:
                        user = await self.bot.fetch_user(int(uid))
                        dono_nome = user.display_name
                    except Exception:
                        dono_nome = f"Treinador_{uid[-4:]}"
                
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

    # 7. COMANDOS DO WORLD BOSS
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
        st = pet.setdefault("stats", {"hp_max": 100, "hp_atual": 100, "atq": 10})

        if st.get("hp_atual", st.get("hp_max", 100)) <= 0:
            return await interaction.response.send_message("💀 Seu Pet está desmaiado! Use uma **🧪 Poção de Cura** na `/loja`.", ephemeral=True)

        boss = load_boss()
        if not boss or not boss.get("ativo", False):
            return await interaction.response.send_message("😴 Não há nenhum World Boss ativo no momento.", ephemeral=True)

        atq_val = st.get("atq", 10)
        dano_base = random.randint(atq_val, atq_val * 2)
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
                porcentagem = info["dano"] / total_dano if total_dano > 0 else 0
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
                f"{interaction.user.mention} enviou **{pet.get('nome', 'Pet')}** para a batalha!\n\n"
                f"{crit_msg}Dano Causado: `{dano_base:,}`\n"
                f"🩸 **HP Restante do Boss:** `{boss['hp_atual']:,}` / `{boss['hp_max']:,}` ({porcentagem_hp:.1f}%)\n"
                f"📊 **Seu Dano Acumulado:** `{dano_acumulado:,}`"
            ),
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(PetRPG(bot))
