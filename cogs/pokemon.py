import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import random
import asyncio
import logging

# --- INTERFACE DE CAPTURA (VIEW COM BOTÃO) ---
class CaptureView(discord.ui.View):
    def __init__(self, pokemon_data: dict):
        super().__init__(timeout=60.0)  # O botão expira em 60 segundos
        self.pokemon = pokemon_data
        self.captured = False

    @discord.ui.button(label="Capturar!", style=discord.ButtonStyle.success, emoji="🔴")
    async def capture_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.captured:
            await interaction.response.send_message("❌ Este Pokémon já foi capturado!", ephemeral=True)
            return

        # Taxa de captura simples (70% de chance)
        sucesso = random.random() < 0.70

        if sucesso:
            self.captured = True
            button.disabled = True
            button.label = "Capturado!"
            button.style = discord.ButtonStyle.secondary

            # Atualiza a mensagem original desativando o botão
            await interaction.response.edit_message(view=self)

            embed_vitoria = discord.Embed(
                title="🎉 Parabéns!",
                description=f"{interaction.user.mention} capturou um **{self.pokemon['name'].capitalize()}**!",
                color=discord.Color.green()
            )
            embed_vitoria.set_thumbnail(url=self.pokemon["sprite"])
            await interaction.followup.send(embed=embed_vitoria)

            # TODO: Conectar ao seu banco de dados para salvar a captura
        else:
            await interaction.response.send_message(
                f"❌ Ah não! O **{self.pokemon['name'].capitalize()}** escapou da sua Pokébola!", 
                ephemeral=True
            )

    async def on_timeout(self):
        # Desativa o botão automaticamente quando os 60s expirarem
        for child in self.children:
            child.disabled = True
        try:
            if hasattr(self, 'message') and self.message:
                await self.message.edit(view=self)
        except Exception:
            pass


# --- COG PRINCIPAL DE POKÉMON ---
class PokemonCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spawn_cooldown = {}  # Limita tempo entre spawns por servidor

    async def buscar_pokemon_api(self, pokemon_id_ou_nome):
        """Busca dados de um Pokémon diretamente na PokéAPI com timeout e try/except"""
        url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id_ou_nome}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "id": data["id"],
                            "name": data["name"],
                            "sprite": data["sprites"]["front_default"],
                            "type": [t["type"]["name"] for t in data["types"]],
                            "hp": data["stats"][0]["base_stat"],
                            "attack": data["stats"][1]["base_stat"]
                        }
                    return None
        except Exception as e:
            logging.error(f"Erro ao acessar PokéAPI: {e}")
            return None

    # --- EVENTO DE SPAWN ALEATÓRIO ---
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # 🎯 FILTRO DE CANAL: Garante spawn APENAS no canal do Pokémon
        nome_canal = message.channel.name.lower()
        if not ("pokémon" in nome_canal or "pokemon" in nome_canal):
            return

        guild_id = message.guild.id
        agora = asyncio.get_event_loop().time()
        ultimo_spawn = self.spawn_cooldown.get(guild_id, 0)

        # 10% de chance por mensagem com intervalo de 30s por servidor
        if agora - ultimo_spawn > 30 and random.random() < 0.10:
            self.spawn_cooldown[guild_id] = agora

            pokemon_id = random.randint(1, 386)
            pokemon = await self.buscar_pokemon_api(pokemon_id)

            if pokemon:
                embed = discord.Embed(
                    title="⚡ Um Pokémon selvagem apareceu!",
                    description="Clique no botão abaixo para tentar capturá-lo!",
                    color=discord.Color.gold()
                )
                embed.set_image(url=pokemon["sprite"])
                embed.add_field(name="Tipo", value=", ".join(pokemon["type"]).capitalize(), inline=True)

                view = CaptureView(pokemon_data=pokemon)
                msg = await message.channel.send(embed=embed, view=view)
                view.message = msg

    # --- COMANDOS SLASH ---
    @app_commands.command(name="pokedex", description="Busca as informações de um Pokémon específico.")
    @app_commands.describe(nome_ou_id="Nome ou ID do Pokémon (ex: pikachu ou 25)")
    async def pokedex(self, interaction: discord.Interaction, nome_ou_id: str):
        # 🎯 FILTRO DE CANAL: Permite usar apenas nos canais autorizados
        canais_permitidos = ["pokedex", "pokebot", "pokemon", "pokémon"]
        nome_canal = interaction.channel.name.lower()

        if not any(c in nome_canal for c in canais_permitidos):
            await interaction.response.send_message(
                "❌ Esse comando só pode ser usado nos canais de Pokémon!", 
                ephemeral=True
            )
            return

        await interaction.response.defer()  # Evita erro de timeout no Discord

        pokemon = await self.buscar_pokemon_api(nome_ou_id.lower())

        if not pokemon:
            await interaction.followup.send("❌ Pokémon não encontrado! Verifique o nome ou ID.")
            return

        embed = discord.Embed(
            title=f"#{pokemon['id']} - {pokemon['name'].capitalize()}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=pokemon["sprite"])
        embed.add_field(name="Tipos", value=", ".join(pokemon["type"]).capitalize(), inline=False)
        embed.add_field(name="HP Base", value=str(pokemon["hp"]), inline=True)
        embed.add_field(name="Ataque Base", value=str(pokemon["attack"]), inline=True)

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PokemonCog(bot))
