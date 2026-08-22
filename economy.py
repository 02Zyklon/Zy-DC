import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import random
import asyncio
import logging
import sqlite3

# -------------------------------------------------------------------
# 🔗 INTEGRAÇÃO COM SEU SISTEMA DE ECONOMIA (database_golds.py)
# -------------------------------------------------------------------
try:
    from database_golds import get_gold_safe, remove_gold_safe
except ImportError:
    # Import alternativo caso o arquivo de economia esteja dentro da pasta 'cogs'
    from cogs.database_golds import get_gold_safe, remove_gold_safe

# --- CONFIGURAÇÕES DE POKÉBOLAS ---
POKEBOLAS = {
    "pokeball": {"nome": "Pokébola", "preco": 100, "taxa": 0.50, "emoji": "🔴"},
    "superball": {"nome": "Superbola", "preco": 300, "taxa": 0.70, "emoji": "🔵"},
    "ultraball": {"nome": "Ultrabola", "preco": 800, "taxa": 0.85, "emoji": "🟡"},
    "masterball": {"nome": "Masterbola", "preco": 5000, "taxa": 1.00, "emoji": "🟣"}
}

DB_NAME = "pokemon_bot.db"

# --- BANCO DE DADOS (SQLITE) ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pokemon_inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            pokemon_id INTEGER NOT NULL,
            pokemon_name TEXT NOT NULL,
            sprite_url TEXT NOT NULL,
            data_captura TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pokemon_mochila_bolas (
            user_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            quantidade INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, item_id)
        )
    """)
    conn.commit()
    conn.close()

def salvar_pokemon(user_id: int, pokemon_id: int, pokemon_name: str, sprite_url: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO pokemon_inventario (user_id, pokemon_id, pokemon_name, sprite_url)
        VALUES (?, ?, ?, ?)
    """, (user_id, pokemon_id, pokemon_name, sprite_url))
    conn.commit()
    conn.close()

def obter_mochila_pokemons(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pokemon_id, pokemon_name, COUNT(*) as quantidade
        FROM pokemon_inventario
        WHERE user_id = ?
        GROUP BY pokemon_id
        ORDER BY pokemon_id ASC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def obter_bolas_usuario(user_id: int) -> dict:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT item_id, quantidade FROM pokemon_mochila_bolas WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    bolas = {key: 0 for key in POKEBOLAS.keys()}
    for item_id, qtd in rows:
        if item_id in bolas:
            bolas[item_id] = qtd
    return bolas

def adicionar_bola(user_id: int, item_id: str, qtd: int = 1):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO pokemon_mochila_bolas (user_id, item_id, quantidade)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, item_id) DO UPDATE SET quantidade = quantidade + ?
    """, (user_id, item_id, qtd, qtd))
    conn.commit()
    conn.close()

def usar_bola(user_id: int, item_id: str) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT quantidade FROM pokemon_mochila_bolas WHERE user_id = ? AND item_id = ?", (user_id, item_id))
    row = cursor.fetchone()
    
    if not row or row[0] <= 0:
        conn.close()
        return False
        
    cursor.execute("UPDATE pokemon_mochila_bolas SET quantidade = quantidade - 1 WHERE user_id = ? AND item_id = ?", (user_id, item_id))
    conn.commit()
    conn.close()
    return True


# --- SELECT MENU DE POKÉBOLAS ---
class SelectPokeballMenu(discord.ui.Select):
    def __init__(self, user_id: int, pokemon_data: dict, parent_view):
        self.user_id = user_id
        self.pokemon = pokemon_data
        self.parent_view = parent_view

        bolas_usuario = obter_bolas_usuario(user_id)
        options = []

        for key, info in POKEBOLAS.items():
            qtd = bolas_usuario.get(key, 0)
            options.append(discord.SelectOption(
                label=f"{info['nome']} (Possui: {qtd})",
                value=key,
                emoji=info["emoji"],
                description=f"Taxa de captura: {int(info['taxa']*100)}%"
            ))

        super().__init__(placeholder="Selecione a Pokébola para arremessar...", options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Apenas quem iniciou a captura pode escolher!", ephemeral=True)
            return

        item_id = self.values[0]
        info_bola = POKEBOLAS[item_id]

        if not usar_bola(self.user_id, item_id):
            await interaction.response.send_message(
                f"❌ Você não tem nenhuma **{info_bola['nome']}**! Compre na `/pokeloja`.",
                ephemeral=True
            )
            return

        sucesso = random.random() < info_bola["taxa"]

        if sucesso:
            self.parent_view.captured = True
            salvar_pokemon(self.user_id, self.pokemon["id"], self.pokemon["name"], self.pokemon["sprite"])

            embed_vitoria = discord.Embed(
                title="🎉 Capturado com sucesso!",
                description=f"{interaction.user.mention} usou uma {info_bola['emoji']} **{info_bola['nome']}** e capturou o **{self.pokemon['name'].capitalize()}**!",
                color=discord.Color.green()
            )
            embed_vitoria.set_thumbnail(url=self.pokemon["sprite"])
            await interaction.response.edit_message(content="✅ **Pokémon Capturado!**", embed=None, view=None)
            await interaction.followup.send(embed=embed_vitoria)
        else:
            await interaction.response.send_message(
                f"❌ Ah não! A {info_bola['emoji']} **{info_bola['nome']}** balançou... mas o **{self.pokemon['name'].capitalize()}** escapou!",
                ephemeral=True
            )


# --- INTERFACE DE CAPTURA ---
class CaptureView(discord.ui.View):
    def __init__(self, pokemon_data: dict):
        super().__init__(timeout=60.0)
        self.pokemon = pokemon_data
        self.captured = False

    @discord.ui.button(label="Capturar!", style=discord.ButtonStyle.success, emoji="🔴")
    async def capture_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.captured:
            await interaction.response.send_message("❌ Este Pokémon já foi capturado!", ephemeral=True)
            return

        menu_view = discord.ui.View(timeout=30.0)
        menu_view.add_item(SelectPokeballMenu(interaction.user.id, self.pokemon, self))

        await interaction.response.send_message(
            f"🎒 {interaction.user.mention}, escolha qual bola quer lançar no **{self.pokemon['name'].capitalize()}**:",
            view=menu_view,
            ephemeral=True
        )

    async def on_timeout(self):
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
        self.spawn_cooldown = {}
        init_db()

    async def buscar_pokemon_api(self, pokemon_id_ou_nome):
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

        nome_canal = message.channel.name.lower()
        if not ("pokémon" in nome_canal or "pokemon" in nome_canal):
            return

        guild_id = message.guild.id
        agora = asyncio.get_event_loop().time()
        ultimo_spawn = self.spawn_cooldown.get(guild_id, 0)

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

    # --- COMANDO SLASH: POKEDEX ---
    @app_commands.command(name="pokedex", description="Busca as informações de um Pokémon específico.")
    @app_commands.describe(nome_ou_id="Nome ou ID do Pokémon (ex: pikachu ou 25)")
    async def pokedex(self, interaction: discord.Interaction, nome_ou_id: str):
        canais_permitidos = ["pokedex", "pokebot", "pokemon", "pokémon"]
        if not any(c in interaction.channel.name.lower() for c in canais_permitidos):
            await interaction.response.send_message("❌ Use nos canais de Pokémon!", ephemeral=True)
            return

        await interaction.response.defer()
        pokemon = await self.buscar_pokemon_api(nome_ou_id.lower())

        if not pokemon:
            await interaction.followup.send("❌ Pokémon não encontrado!")
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

    # --- COMANDO SLASH: MOCHILA ---
    @app_commands.command(name="mochila", description="Exibe a sua lista de Pokémons e Pokébolas.")
    async def mochila(self, interaction: discord.Interaction):
        canais_permitidos = ["pokedex", "pokebot", "pokemon", "pokémon"]
        if not any(c in interaction.channel.name.lower() for c in canais_permitidos):
            await interaction.response.send_message("❌ Use nos canais de Pokémon!", ephemeral=True)
            return

        await interaction.response.defer()
        user_id = interaction.user.id
        pokemons = obter_mochila_pokemons(user_id)
        bolas = obter_bolas_usuario(user_id)

        embed = discord.Embed(
            title=f"🎒 Mochila de Treinador - {interaction.user.display_name}",
            color=discord.Color.dark_purple()
        )

        # Seção de Itens (Pokébolas)
        bolas_txt = ""
        for key, info in POKEBOLAS.items():
            qtd = bolas.get(key, 0)
            bolas_txt += f"{info['emoji']} **{info['nome']}:** {qtd}\n"
        embed.add_field(name="📦 Itens de Captura", value=bolas_txt, inline=False)

        # Seção de Pokémons
        if not pokemons:
            embed.add_field(name="🔴 Pokémons Capturados", value="*Nenhum Pokémon capturado ainda.*", inline=False)
        else:
            lista_txt = ""
            total_capturas = 0
            for poke_id, poke_name, qtd in pokemons:
                lista_txt += f"• **#{poke_id:03d} {poke_name.capitalize()}** — x{qtd}\n"
                total_capturas += qtd
            embed.add_field(name=f"🔴 Pokémons ({total_capturas} no total)", value=lista_txt, inline=False)

        await interaction.followup.send(embed=embed)

    # --- COMANDO SLASH: POKELOJA ---
    @app_commands.command(name="pokeloja", description="Compre Pokébolas utilizando seus Golds.")
    @app_commands.describe(
        item="Tipo de Pokébola para comprar",
        quantidade="Quantidade desejada"
    )
    @app_commands.choices(item=[
        app_commands.Choice(name="🔴 Pokébola - 100 Golds (50% Taxa)", value="pokeball"),
        app_commands.Choice(name="🔵 Superbola - 300 Golds (70% Taxa)", value="superball"),
        app_commands.Choice(name="🟡 Ultrabola - 800 Golds (85% Taxa)", value="ultraball"),
        app_commands.Choice(name="🟣 Masterbola - 5000 Golds (100% Taxa)", value="masterball"),
    ])
    async def pokeloja(self, interaction: discord.Interaction, item: str, quantidade: int = 1):
        if quantidade <= 0:
            await interaction.response.send_message("❌ A quantidade precisa ser pelo menos 1!", ephemeral=True)
            return

        info_item = POKEBOLAS[item]
        custo_total = info_item["preco"] * quantidade
        user_id = interaction.user.id

        # Consulta o saldo atual de forma assíncrona/thread-safe
        saldo_atual = await get_gold_safe(user_id)

        if saldo_atual < custo_total:
            await interaction.response.send_message(
                f"❌ Saldo insuficiente! Você precisa de **{custo_total} Golds** mas possui **{saldo_atual} Golds**.",
                ephemeral=True
            )
            return

        # Tenta remover o valor dos golds
        removido = await remove_gold_safe(user_id, custo_total)
        if not removido:
            await interaction.response.send_message("❌ Ocorreu um erro ao processar o débito dos seus Golds.", ephemeral=True)
            return

        # Adiciona a bola no inventário
        adicionar_bola(user_id, item, quantidade)

        embed = discord.Embed(
            title="🛒 PokéLoja - Compra Concluída!",
            description=f"Você comprou **{quantidade}x {info_item['emoji']} {info_item['nome']}** por **{custo_total} Golds**!",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(PokemonCog(bot))
