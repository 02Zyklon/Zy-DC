import discord
from discord.ext import commands
from discord import app_commands
import random
import aiohttp
import json
import os

CAMINHO_HAREM = "harem_db.json"

# --- FUNÇÕES DE PERSISTÊNCIA NO DISCO (JSON) ---
def carregar_harem() -> dict:
    if not os.path.exists(CAMINHO_HAREM):
        with open(CAMINHO_HAREM, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
        return {}
    
    try:
        with open(CAMINHO_HAREM, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Erro ao carregar {CAMINHO_HAREM}: {e}")
        return {}

def salvar_harem(dados: dict):
    try:
        with open(CAMINHO_HAREM, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Erro ao salvar {CAMINHO_HAREM}: {e}")

def adicionar_personagem(user_id: int, personagem: dict):
    harem = carregar_harem()
    user_str = str(user_id)
    
    if user_str not in harem:
        harem[user_str] = []
    
    if not any(p.get("mal_id") == personagem.get("mal_id") for p in harem[user_str]):
        harem[user_str].append(personagem)
        salvar_harem(harem)
        return True
    return False

def obter_harem_usuario(user_id: int) -> list:
    harem = carregar_harem()
    return harem.get(str(user_id), [])

# --- VIEW DO COMANDO ROLL ---
class ReivindicarView(discord.ui.View):
    def __init__(self, personagem: dict):
        super().__init__(timeout=60.0)
        self.personagem = personagem

    @discord.ui.button(label="❤️ Reivindicar (Claim)", style=discord.ButtonStyle.green)
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        sucesso = adicionar_personagem(interaction.user.id, self.personagem)
        
        if sucesso:
            button.disabled = True
            button.label = f"Reivindicado por {interaction.user.display_name}!"
            button.style = discord.ButtonStyle.secondary
            
            embed = interaction.message.embeds[0]
            embed.set_footer(text=f"👑 Dono(a): {interaction.user.display_name}")
            await interaction.response.edit_message(embed=embed, view=self)
            await interaction.followup.send(f"🎉 {interaction.user.mention} adicionou **{self.personagem['name']}** à sua coleção!", ephemeral=False)
            self.stop()
        else:
            await interaction.response.send_message("❌ Você já possui este personagem no seu harém!", ephemeral=True)

# --- COG DE GACHA ---
class Gacha(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="roll", description="Sorteie um personagem de anime aleatório!")
    @app_commands.checks.cooldown(1, 300, key=lambda i: (i.user.id))
    async def roll(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        pagina_aleatoria = random.randint(1, 100)
        url = f"https://api.jikan.moe/v4/top/characters?page={pagina_aleatoria}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 429:
                        await interaction.followup.send("⏳ A API de animes está sobrecarregada no momento. Tente novamente em alguns segundos!")
                        return
                    if resp.status != 200:
                        await interaction.followup.send("⚠️ Erro ao buscar personagens no momento. Tente novamente!")
                        return
                    
                    data = await resp.json()
                    personagens = data.get("data", [])
                    
                    if not personagens:
                        await interaction.followup.send("⚠️ Nenhum personagem encontrado. Tente novamente!")
                        return
                    
                    p_data = random.choice(personagens)
                    
                    personagem = {
                        "mal_id": p_data.get("mal_id"),
                        "name": p_data.get("name"),
                        "image": p_data.get("images", {}).get("jpg", {}).get("image_url"),
                        "url": p_data.get("url")
                    }

            embed = discord.Embed(
                title=f"✨ {personagem['name']}",
                url=personagem["url"],
                color=discord.Color.purple()
            )
            if personagem["image"]:
                embed.set_image(url=personagem["image"])
                
            embed.set_footer(text="Clique no botão abaixo para reivindicar!")

            view = ReivindicarView(personagem)
            await interaction.followup.send(embed=embed, view=view)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao realizar o roll: `{e}`")

    @roll.error
    async def roll_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            minutos = int(error.retry_after // 60)
            segundos = int(error.retry_after % 60)
            msg = f"⏳ Aguarde **{minutos}m {segundos}s** para dar outro roll!"
            
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="harem", description="Veja sua coleção de personagens.")
    async def harem(self, interaction: discord.Interaction, membro: discord.Member = None):
        target = membro or interaction.user
        colecao = obter_harem_usuario(target.id)
        
        if not colecao:
            txt = "Você ainda não possui personagens." if target == interaction.user else f"{target.display_name} não possui personagens."
            await interaction.response.send_message(f"📜 **Harém de {target.display_name}:**\n{txt}")
            return

        linhas = [f"• **{p['name']}** ([MAL]({p['url']}))" for p in colecao[:15]]
        
        embed = discord.Embed(
            title=f"💖 Harém de {target.display_name} ({len(colecao)} personagens)",
            description="\n".join(linhas),
            color=discord.Color.magenta()
        )
        if len(colecao) > 15:
            embed.set_footer(text=f"E mais {len(colecao) - 15} personagens...")
            
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Gacha(bot))
