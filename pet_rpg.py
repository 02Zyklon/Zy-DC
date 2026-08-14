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

        # Status Base dependendo do Elemento
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

    # 2. COMANDO: /foguinho (DAILY / CUIR DO PET)
    @app_commands.command(name="foguinho", description="Alimente seu Pet diariamente para ganhar XP e subir de nível!")
    async def foguinho(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = load_data()

        if user_id not in data:
            return await interaction.response.send_message("❌ Você ainda não tem um Pet! Use `/pet_adotar` primeiro.", ephemeral=True)

        pet = data[user_id]
        agora = int(time.time())
        tempo_24h = 86400

        # Checa tempo restante
        tempo_passado = agora - pet["last_daily"]
        if tempo_passado < tempo_24h:
            restante = tempo_24h - tempo_passado
            horas = restante // 3600
            minutos = (restante % 3600) // 60
            return await interaction.response.send_message(f"⏳ Seu Pet já está alimentado! Volte em **{horas}h {minutos}m**.", ephemeral=True)

        # Lógica de Streak (se passar de 48h reseta o streak)
        if tempo_passado > (tempo_24h * 2):
            pet["streak"] = 1
        else:
            pet["streak"] += 1

        # XP Base + Bônus de Streak
        xp_ganho = random.randint(20, 50)
        if pet["streak"] >= 7:
            xp_ganho = int(xp_ganho * 1.25)

        pet["xp"] += xp_ganho
        pet["last_daily"] = agora

        # Level Up Check
        xp_necessario = pet["level"] * 100
        subiu = False
        while pet["xp"] >= xp_necessario:
            pet["xp"] -= xp_necessario
            pet["level"] += 1
            subiu = True
            
            # Bônus de Atributos ao subir de nível
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

        if pet["midia"]:
            embed.set_image(url=pet["midia"])

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(PetRPG(bot))
