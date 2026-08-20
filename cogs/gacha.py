import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import random
import asyncio

# --- MOCK DE BANCO DE DADOS PARA COLEÇÃO E CLAIMS ---
# Estrutura: { user_id: [ {"id": 1, "name": "Naruto", "image": "url", "anime": "Naruto"} ] }
HAREM_DB = {}
# Registra quem tem o claim ativo de cada personagem sorteado recentemente no chat
# Estrutura: { message_id: {"character": dict, "claimed": False} }
ROLLS_ATIVOS = {}

class ClaimButton(discord.ui.Button):
    def __init__(self, char_data: dict, msg_id: int):
        super().__init__(style=discord.ButtonStyle.green, label="💍 Casar / Reivindicar", custom_id=f"claim_{msg_id}")
        self.char_data = char_data
        self.msg_id = msg_id

    async def callback(self, interaction: discord.Interaction):
        roll_info = ROLLS_ATIVOS.get(self.msg_id)
        
        if not roll_info:
            await interaction.response.send_message("❌ Este card expirou!", ephemeral=True)
            return

        if roll_info["claimed"]:
            await interaction.response.send_message("❌ Alguém já reivindicou este personagem!", ephemeral=True)
            return

        user_id = interaction.user.id
        user_harem = HAREM_DB.setdefault(user_id, [])

        # Verifica se o usuário já tem o personagem
        if any(c["id"] == self.char_data["id"] for c in user_harem):
            await interaction.response.send_message("⚠️ Você já tem esse personagem na sua coleção!", ephemeral=True)
            return

        # Registra o claim
        user_harem.append(self.char_data)
        roll_info["claimed"] = True
        self.disabled = True
        self.label = f"Reivindicado por {interaction.user.display_name}"
        self.style = discord.ButtonStyle.secondary

        embed = interaction.message.embeds[0]
        embed.set_footer(text=f"💖 Reivindicado por {interaction.user.display_name}!")
        
        await interaction.response.edit_message(embed=embed, view=self.view)
        await interaction.followup.send(f"🎉 {interaction.user.mention} casou com **{self.char_data['name']}**!")


class TrocaView(discord.ui.View):
    def __init__(self, p1: discord.Member, p2: discord.Member, char1: dict, char2: dict):
        super().__init__(timeout=60.0)
        self.p1 = p1
        self.p2 = p2
        self.char1 = char1
        self.char2 = char2
        self.aceito_p2 = False

    @discord.ui.button(label="Aceitar Troca ✅", style=discord.ButtonStyle.green)
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.p2:
            await interaction.response.send_message("❌ Apenas o usuário desafiado pode aceitar a troca!", ephemeral=True)
            return

        # Executa a troca nos inventários
        harem_p1 = HAREM_DB.get(self.p1.id, [])
        harem_p2 = HAREM_DB.get(self.p2.id, [])

        if self.char1 in harem_p1 and self.char2 in harem_p2:
            harem_p1.remove(self.char1)
            harem_p2.remove(self.char2)
            harem_p1.append(self.char2)
            harem_p2.append(self.char1)

            for child in self.children:
                child.disabled = True

            await interaction.response.edit_message(
                content=f"🤝 **Troca Concluída!**\n{self.p1.mention} recebeu **{self.char2['name']}**.\n{self.p2.mention} recebeu **{self.char1['name']}**.",
                view=self
            )
        else:
            await interaction.response.send_message("❌ Um dos jogadores não possui mais o personagem indicado!", ephemeral=True)


class Gacha(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 1. COMANDO ROLL (SORTEIO DE PERSONAGEM VIA JIKAN API)
    @app_commands.command(name="roll", description="Sorteia um personagem de anime aleatório para sua coleção.")
    @app_commands.checks.cooldown(1, 30, key=lambda i: (i.guild_id, i.user.id))  # Cooldown de 30s
    async def roll(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # ID aleatório de personagem no MyAnimeList (Jikan API)
        random_id = random.randint(1, 10000)
        url = f"https://api.jikan.moe/v4/characters/{random_id}/full"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    # Tenta um ID secundário caso o primeiro falhe
                    random_id = random.randint(1, 2000)
                    async with session.get(f"https://api.jikan.moe/v4/characters/{random_id}/full") as resp2:
                        if resp2.status != 200:
                            await interaction.followup.send("❌ Erro ao buscar personagem. Tente novamente!")
                            return
                        data = (await resp2.json())["data"]
                else:
                    data = (await resp.json())["data"]

        char_name = data.get("name", "Desconhecido")
        char_image = data.get("images", {}).get("jpg", {}).get("image_url", "")
        
        # Pega a obra/anime principal do personagem
        anime_list = data.get("anime", [])
        anime_name = anime_list[0]["anime"]["title"] if anime_list else "Obra Desconhecida"

        char_data = {
            "id": data.get("mal_id"),
            "name": char_name,
            "image": char_image,
            "anime": anime_name
        }

        embed = discord.Embed(
            title=f"🎴 {char_name}",
            description=f"**Anime/Origem:** {anime_name}",
            color=discord.Color.purple()
        )
        if char_image:
            embed.set_image(url=char_image)
        embed.set_footer(text="Clique no botão abaixo para reivindicar este personagem!")

        view = discord.ui.View(timeout=60.0)
        # O ID temporário é vinculado ao envio da mensagem
        msg = await interaction.followup.send(embed=embed, view=view)
        
        btn = ClaimButton(char_data, msg.id)
        view.add_item(btn)
        await msg.edit(view=view)

        ROLLS_ATIVOS[msg.id] = {"character": char_data, "claimed": False}

    @roll.error
    async def roll_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"⏳ Aguarde `{error.retry_after:.1f}s` para rodar o `/roll` novamente!",
                ephemeral=True
            )

    # 2. COMANDO HAREM / COLEÇÃO
    @app_commands.command(name="harem", description="Exibe os personagens que você já colecionou.")
    async def harem(self, interaction: discord.Interaction, membro: discord.Member = None):
        target = membro or interaction.user
        colecao = HAREM_DB.get(target.id, [])

        if not colecao:
            await interaction.response.send_message(
                f"📂 {target.mention} ainda não possui nenhum personagem na coleção! Use `/roll`.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"💖 Harém de {target.display_name} ({len(colecao)} Personagens)",
            color=discord.Color.magenta()
        )

        # Lista os últimos 10 personagens reivindicados
        lista_txt = ""
        for idx, char in enumerate(colecao[-10:], 1):
            lista_txt += f"**{idx}.** {char['name']} — *{char['anime']}*\n"

        embed.description = lista_txt
        if colecao[-1].get("image"):
            embed.set_thumbnail(url=colecao[-1]["image"])

        await interaction.response.send_message(embed=embed)

    # 3. COMANDO TROCAR
    @app_commands.command(name="trocar", description="Troque um personagem seu por um de outro membro.")
    async def trocar(self, interaction: discord.Interaction, oponente: discord.Member, seu_personagem: str, personagem_dele: str):
        if oponente == interaction.user or oponente.bot:
            await interaction.response.send_message("❌ Alvo inválido para troca!", ephemeral=True)
            return

        harem_p1 = HAREM_DB.get(interaction.user.id, [])
        harem_p2 = HAREM_DB.get(oponente.id, [])

        # Busca os cards nos inventários pelo nome
        char1 = next((c for c in harem_p1 if seu_personagem.lower() in c["name"].lower()), None)
        char2 = next((c for c in harem_p2 if personagem_dele.lower() in c["name"].lower()), None)

        if not char1:
            await interaction.response.send_message(f"❌ Você não possui o personagem `{seu_personagem}`!", ephemeral=True)
            return
        if not char2:
            await interaction.response.send_message(f"❌ {oponente.mention} não possui o personagem `{personagem_dele}`!", ephemeral=True)
            return

        view = TrocaView(interaction.user, oponente, char1, char2)
        await interaction.response.send_message(
            content=f"🔄 {oponente.mention}, {interaction.user.mention} quer trocar o personagem **{char1['name']}** pelo seu **{char2['name']}**. Aceita?",
            view=view
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Gacha(bot))
