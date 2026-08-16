import os
import json
import random
import datetime
import discord
from discord.ext import commands
from discord import app_commands
import economy  # Certifique-se de que o economy.py está na mesma pasta

DB_RPG = "config_rpg.json"

def load_rpg_db():
    if not os.path.exists(DB_RPG):
        return {"pets": {}, "masmorras": {}}
    with open(DB_RPG, "r", encoding="utf-8") as f:
        return json.load(f)

def save_rpg_db(data):
    with open(DB_RPG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

class PetRPG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="pet_adotar", description="Escolha e adote o seu Pet inicial (Fogo, Água ou Trovão).")
    @app_commands.choices(elemento=[
        app_commands.Choice(name="🔥 Fogo", value="fogo"),
        app_commands.Choice(name="💧 Água", value="agua"),
        app_commands.Choice(name="⚡ Trovão", value="trovao")
    ])
    async def pet_adotar(self, interaction: discord.Interaction, elemento: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=True)
        
        db = load_rpg_db()
        user_id = str(interaction.user.id)

        if user_id in db["pets"]:
            return await interaction.followup.send("⚠️ Você já possui um pet adotado! Use `/pet_perfil` para vê-lo.", ephemeral=True)

        nomes_iniciais = {
            "fogo": "Salamandra Ignis",
            "agua": "Spiritus Aqua",
            "trovao": "Fulgur Beast"
        }

        db["pets"][user_id] = {
            "nome": nomes_iniciais[elemento.value],
            "elemento": elemento.value,
            "nivel": 1,
            "xp": 0,
            "vida": 100,
            "vitorias": 0
        }
        save_rpg_db(db)

        embed = discord.Embed(
            title="🐾 Pet Adotado com Sucesso!",
            description=f"Parabéns {interaction.user.mention}! Você adotou um pet do elemento **{elemento.name}** chamado **{nomes_iniciais[elemento.value]}**.",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="pet_perfil", description="Exibe os status, vida e vitórias do seu Pet.")
    async def pet_perfil(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        db = load_rpg_db()
        user_id = str(interaction.user.id)

        if user_id not in db["pets"]:
            return await interaction.followup.send("⚠️ Você ainda não tem um pet! Use `/pet_adotar` primeiro.")

        pet = db["pets"][user_id]
        embed = discord.Embed(
            title=f"🐾 Perfil do Pet — {pet['nome']}",
            description=f"Dono: {interaction.user.mention}",
            color=discord.Color.purple()
        )
        embed.add_field(name="Elemento", value=pet["elemento"].capitalize(), inline=True)
        embed.add_field(name="Nível", value=f"`{pet['nivel']}`", inline=True)
        embed.add_field(name="XP", value=f"`{pet['xp']}/100`", inline=True)
        embed.add_field(name="Vida", value=f"`{pet['vida']} HP`", inline=True)
        embed.add_field(name="Vitórias", value=f"`{pet['vitorias']}`", inline=True)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="masmorra", description="Enfrente monstros nas profundezas de Yggdrasil por recompensas.")
    @app_commands.checks.cooldown(1, 300, key=lambda i: i.user.id) # 5 minutos de cooldown
    async def masmorra(self, interaction: discord.Interaction):
        await interaction.response.defer()

        db = load_rpg_db()
        user_id = str(interaction.user.id)

        if user_id not in db["pets"]:
            return await interaction.followup.send("⚠️ Você precisa de um pet para entrar na masmorra! Use `/pet_adotar`.")

        monstros = ["Goblin das Cavernas", "Lobisomem Sombrio", "Dragão Menor", "Esqueleto Guerreiro"]
        monstro_escolhido = random.choice(monstros)
        vitoria = random.choice([True, False])

        if vitoria:
            recompensa_gold = random.randint(50, 200)
            economy.add_gold(interaction.user.id, recompensa_gold)
            db["pets"][user_id]["vitorias"] += 1
            db["pets"][user_id]["xp"] += 35

            # Subir de nível simples
            if db["pets"][user_id]["xp"] >= 100:
                db["pets"][user_id]["nivel"] += 1
                db["pets"][user_id]["xp"] = 0
                lvl_up_txt = "\n🎉 **Seu pet subiu de nível!**"
            else:
                lvl_up_txt = ""

            save_rpg_db(db)

            embed = discord.Embed(
                title="⚔️ Vitória na Masmorra!",
                description=f"Seu pet derrotou um **{monstro_escolhido}**!\n\n💰 Recompensa: **{recompensa_gold} Golds**{lvl_up_txt}",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="💀 Derrota na Masmorra...",
                description=f"O **{monstro_escolhido}** era muito forte e seu pet foi derrotado! Tente novamente mais tarde.",
                color=discord.Color.red()
            )

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PetRPG(bot))
