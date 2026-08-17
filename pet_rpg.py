import os
import json
import random
import datetime
import time
import discord
from discord.ext import commands
from discord import app_commands
import economy  # Certifique-se de que o economy.py está na mesma pasta

DB_RPG = "config_rpg.json"

# IDs configurados para o sistema de Aventureiro
CARGO_AVENTUREIRO_ID = 1538666697849045092
CANAL_ESPECIFICO_ID = 1538229136898662500

def load_rpg_db():
    if not os.path.exists(DB_RPG):
        return {"pets": {}, "masmorras": {}, "boss_atual": {"nome": "Zé pilintra", "vida": 699903, "vida_max": 700000, "nivel": 1}}
    try:
        with open(DB_RPG, "r", encoding="utf-8") as f:
            conteudo = f.read().strip()
            if not conteudo:
                return {"pets": {}, "masmorras": {}, "boss_atual": {"nome": "Zé pilintra", "vida": 699903, "vida_max": 700000, "nivel": 1}}
            data = json.loads(conteudo)
            if "pets" not in data:
                data["pets"] = {}
            if "masmorras" not in data:
                data["masmorras"] = {}
            if "boss_atual" not in data:
                data["boss_atual"] = {"nome": "Zé pilintra", "vida": 699903, "vida_max": 700000, "nivel": 1}
            return data
    except Exception:
        return {"pets": {}, "masmorras": {}, "boss_atual": {"nome": "Zé pilintra", "vida": 699903, "vida_max": 700000, "nivel": 1}}

def save_rpg_db(data):
    with open(DB_RPG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

class AventureiroConfirmView(discord.ui.View):
    def __init__(self, cargo_aventureiro_id: int, canal_liberar_id: int):
        super().__init__(timeout=180) # Expira em 3 minutos
        self.cargo_aventureiro_id = cargo_aventureiro_id
        self.canal_liberar_id = canal_liberar_id

    @discord.ui.button(label="Sim, quero ser Aventureiro!", style=discord.ButtonStyle.green, emoji="⚔️")
    async def btn_sim(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        if not guild:
            return await interaction.response.send_message("❌ Este comando deve ser usado em um servidor.", ephemeral=True)
            
        cargo = guild.get_role(self.cargo_aventureiro_id)
        canal = guild.get_channel(self.canal_liberar_id)

        if not cargo:
            return await interaction.response.send_message("❌ Erro interno: O cargo de aventureiro não foi encontrado pelo ID.", ephemeral=True)

        # Adiciona o cargo ao usuário
        await interaction.user.add_roles(cargo)

        # Configura permissão para ver e enviar mensagens no canal específico
        if canal:
            await canal.set_permissions(interaction.user, view_channel=True, send_messages=True)

        for child in self.children:
            child.disabled = True
        
        embed = discord.Embed(
            title="🎉 Parabéns, Novo Aventureiro!",
            description=f"Você aceitou o chamado! O cargo **{cargo.name}** foi adicionado e o canal {canal.mention if canal else ''} foi desbloqueado para você.",
            color=discord.Color.gold()
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Agora não", style=discord.ButtonStyle.red, emoji="❌")
    async def btn_nao(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        
        await interaction.response.edit_message(content="❌ Oferta recusada. Quando mudar de ideia, você poderá tentar novamente!", embed=None, view=self)


class PetRPG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="daily", description="Coleta sua recompensa diária de Golds.")
    @app_commands.checks.cooldown(1, 86400, key=lambda i: i.user.id) # 24 horas de cooldown
    async def daily(self, interaction: discord.Interaction):
        await interaction.response.defer()

        db = load_rpg_db()
        user_id = str(interaction.user.id)

        if user_id not in db["pets"]:
            return await interaction.followup.send("⚠️ Você precisa adotar um pet primeiro para resgatar o seu daily! Use `/pet_adotar`.", ephemeral=True)

        recompensa = random.randint(100, 300)
        economy.add_gold(interaction.user.id, recompensa)

        embed = discord.Embed(
            title="🎁 Recompensa Diária Resgatada!",
            description=f"Parabéns! Você resgatou o seu bônus diário e ganhou **{recompensa:,} Golds** 📀.",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Saldo atual: {economy.get_gold(interaction.user.id):,} Golds")
        await interaction.followup.send(embed=embed)

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
            "vitorias": 0,
            "convite_enviado": False,
            "inventario": {"cura": 0, "racao": 0, "elixir": 0, "amuleto": 0},
            "stats": {
                "hp_atual": 100,
                "hp_max": 100,
                "atq": 25,
                "defesa": 10,
                "agi": 10
            }
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
        stats = pet.get("stats", {"hp_atual": pet.get("vida", 100), "hp_max": pet.get("vida", 100), "atq": 25, "defesa": 10, "agi": 10})
        
        embed = discord.Embed(
            title=f"🐾 Perfil do Pet — {pet.get('nome', 'Pet')}",
            description=f"Dono: {interaction.user.mention}",
            color=discord.Color.purple()
        )
        embed.add_field(name="Elemento", value=pet.get("elemento", "neutro").capitalize(), inline=True)
        embed.add_field(name="Nível", value=f"`{pet.get('nivel', 1)}`", inline=True)
        embed.add_field(name="XP", value=f"`{pet.get('xp', 0)}/150`", inline=True)
        embed.add_field(name="Vida (HP)", value=f"`{stats.get('hp_atual', 100)} / {stats.get('hp_max', 100)}`", inline=True)
        embed.add_field(name="Ataque", value=f"`{stats.get('atq', 25)}`", inline=True)
        embed.add_field(name="Defesa", value=f"`{stats.get('defesa', 10)}`", inline=True)
        embed.add_field(name="Vitórias", value=f"`{pet.get('vitorias', 0)}`", inline=True)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="inventario", description="Veja os itens e consumíveis guardados na sua mochila.")
    async def inventario(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        db = load_rpg_db()
        user_id = str(interaction.user.id)

        if user_id not in db["pets"]:
            return await interaction.followup.send("⚠️ Você precisa adotar um pet primeiro para ter um inventário! Use `/pet_adotar`.", ephemeral=True)

        pet = db["pets"][user_id]
        
        if "inventario" not in pet:
            pet["inventario"] = {"cura": 0, "racao": 0, "elixir": 0, "amuleto": 0}
            save_rpg_db(db)

        inv = pet["inventario"]

        embed = discord.Embed(
            title=f"🎒 Mochila de {interaction.user.display_name}",
            description="Aqui estão os itens que você guarda para auxiliar o seu pet nas aventuras:",
            color=discord.Color.blue()
        )
        embed.add_field(name="🧪 Poção de Cura", value=f"` {inv.get('cura', 0)}x `", inline=True)
        embed.add_field(name="🍖 Super Ração", value=f"` {inv.get('racao', 0)}x `", inline=True)
        embed.add_field(name="⚡ Elixir de Agilidade", value=f"` {inv.get('elixir', 0)}x `", inline=True)
        embed.add_field(name="🛡️ Amuleto de Força", value=f"` {inv.get('amuleto', 0)}x `", inline=True)
        
        embed.set_footer(text="Use os itens estrategicamente antes de explorar ou entrar nas masmorras!")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="loja", description="Adquira itens especiais para guardar na mochila usando seus Golds.")
    @app_commands.choices(item=[
        app_commands.Choice(name="🧪 Poção de Cura (129 Golds)", value="cura"),
        app_commands.Choice(name="🍖 Super Ração (175 Golds)", value="racao"),
        app_commands.Choice(name="⚡ Elixir de Agilidade (291 Golds)", value="elixir"),
        app_commands.Choice(name="🛡️ Amuleto de Força (348 Golds)", value="amuleto")
    ])
    async def loja(self, interaction: discord.Interaction, item: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=True)

        db = load_rpg_db()
        user_id = str(interaction.user.id)

        if user_id not in db["pets"]:
            return await interaction.followup.send("⚠️ Você precisa adotar um pet primeiro para comprar itens! Use `/pet_adotar`.", ephemeral=True)

        pet = db["pets"][user_id]

        precos = {
            "cura": 129,
            "racao": 175,
            "elixir": 291,
            "amuleto": 348
        }

        custo = precos[item.value]
        saldo_atual = economy.get_gold(interaction.user.id)

        if saldo_atual < custo:
            return await interaction.followup.send(
                f"❌ **Saldo Insuficiente!** Você tem `{saldo_atual:,} Golds`, mas este item custa `{custo:,} Golds`.",
                ephemeral=True
            )

        if not economy.remove_gold(interaction.user.id, custo):
            return await interaction.followup.send("❌ Erro ao processar o pagamento na sua carteira.", ephemeral=True)

        if "inventario" not in pet:
            pet["inventario"] = {"cura": 0, "racao": 0, "elixir": 0, "amuleto": 0}
        
        pet["inventario"][item.value] = pet["inventario"].get(item.value, 0) + 1
        save_rpg_db(db)

        embed = discord.Embed(
            title="🛒 Compra Realizada com Sucesso!",
            description=f"Você adquiriu **{item.name}** por **{custo} Golds**.\nO item foi guardado com segurança na sua mochila (`/inventario`).",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Saldo restante: {economy.get_gold(interaction.user.id):,} Golds")
        
        await interaction.followup.send(embed=embed, ephemeral=True)

        # Log automático para a staff em itens de alto valor
        if custo >= 250:
            try:
                log_channel = discord.utils.get(interaction.guild.text_channels, name="📡・bot-logs")
                if log_channel:
                    log_embed = discord.Embed(
                        title="📊 Log de Economia / Loja",
                        description=f"O usuário **{interaction.user}** (`{interaction.user.id}`) comprou um item de alto valor.",
                        color=discord.Color.orange()
                    )
                    log_embed.add_field(name="Item", value=item.name, inline=True)
                    log_embed.add_field(name="Valor Gasto", value=f"{custo} Golds", inline=True)
                    log_embed.set_timestamp()
                    await log_channel.send(embed=log_embed)
            except Exception as e:
                print(f"Erro ao enviar log de loja: {e}")

    @app_commands.command(name="foguinho", description="Testa sua sorte no clássico jogo do foguinho apostando Golds.")
    @app_commands.describe(aposta="Quantidade de Golds que você deseja apostar")
    async def foguinho(self, interaction: discord.Interaction, aposta: int):
        await interaction.response.defer()

        if aposta <= 0:
            return await interaction.followup.send("❌ A aposta deve ser maior que 0 Golds!", ephemeral=True)

        saldo_atual = economy.get_gold(interaction.user.id)
        if saldo_atual < aposta:
            return await interaction.followup.send(
                f"❌ **Saldo Insuficiente!** Você tem `{saldo_atual:,} Golds`, mas tentou apostar `{aposta:,} Golds`.",
                ephemeral=True
            )

        ganhou = random.choice([True, False])

        if ganhou:
            lucro = aposta
            economy.add_gold(interaction.user.id, lucro)
            embed = discord.Embed(
                title="🔥 Foguinho — Vitória!",
                description=(
                    f"As chamas brilharam a seu favor, {interaction.user.mention}!\n\n"
                    f"💰 **Aposta:** `{aposta:,} Golds`\n"
                    f"✨ **Lucro Obtido:** `+{lucro:,} Golds`\n"
                    f"🪙 **Novo Saldo:** `{economy.get_gold(interaction.user.id):,} Golds`"
                ),
                color=discord.Color.green()
            )
        else:
            economy.remove_gold(interaction.user.id, aposta)
            embed = discord.Embed(
                title="💥 Foguinho — Queimado!",
                description=(
                    f"O fogo consumiu sua aposta, {interaction.user.mention}...\n\n"
                    f"💸 **Valor Perdido:** `-{aposta:,} Golds`\n"
                    f"🪙 **Saldo Restante:** `{economy.get_gold(interaction.user.id):,} Golds`"
                ),
                color=discord.Color.red()
            )

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
            db["pets"][user_id]["vitorias"] = db["pets"][user_id].get("vitorias", 0) + 1
            db["pets"][user_id]["xp"] = db["pets"][user_id].get("xp", 0) + 35

            # Subir de nível simples
            lvl_up_txt = ""
            if db["pets"][user_id]["xp"] >= 150:
                db["pets"][user_id]["nivel"] = db["pets"][user_id].get("nivel", 1) + 1
                db["pets"][user_id]["xp"] -= 150
                lvl_up_txt = "\n🎉 **Seu pet subiu de nível!**"

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
        
        
    @app_commands.command(name="boss", description="Enfrente o Chefe atual para ganhar recompensas épicas de Golds e XP!")
    async def boss(self, interaction: discord.Interaction):
        await interaction.response.defer()

        db = load_rpg_db()
        user_id = str(interaction.user.id)

        if user_id not in db["pets"]:
            return await interaction.followup.send("⚠️ Você precisa adotar um pet primeiro para enfrentar o Boss! Use `/pet_adotar`.", ephemeral=True)

        boss_data = db.get("boss_atual", {"nome": "Zé pilintra", "vida": 699903, "vida_max": 700000, "nivel": 1})
        
        if boss_data["vida"] <= 0:
            return await interaction.followup.send("🏆 O Boss atual já foi derrotado! Aguarde um administrador invocar o próximo com `/set_boss`.", ephemeral=True)

        dano_causado = random.randint(50, 150)
        boss_data["vida"] -= dano_causado
        if boss_data["vida"] < 0:
            boss_data["vida"] = 0

        db["boss_atual"] = boss_data
        save_rpg_db(db)

        embed = discord.Embed(
            title=f"⚔️ Batalha contra o Boss: {boss_data['nome']}",
            description=(
                f"{interaction.user.mention} atacou ferozmente o chefe com seu pet!\n\n"
                f"💥 **Dano Causado:** `{dano_causado:,}`\n"
                f"❤️ **HP do Boss:** `{boss_data['vida']:,} / {boss_data['vida_max']:,}`\n"
            ),
            color=discord.Color.dark_red()
        )

        if boss_data["vida"] == 0:
            recompensa = random.randint(500, 1000)
            economy.add_gold(interaction.user.id, recompensa)
            embed.add_field(
                name="🎉 VITÓRIA ÉPICA!",
                value=f"O Boss foi derrotado! {interaction.user.mention} desferiu o golpe final e ganhou **{recompensa:,} Golds** 📀!",
                inline=False
            )
        else:
            embed.set_footer(text="Continue atacando para derrubá-lo!")

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="set_boss", description="[Admin] Invoca ou configura um novo Boss para o servidor.")
    @app_commands.describe(nome="Nome do Boss", vida="Quantidade de vida (HP)", nivel="Nível do Boss")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_boss(self, interaction: discord.Interaction, nome: str, vida: int, nivel: int = 1):
        await interaction.response.defer(ephemeral=True)

        db = load_rpg_db()
        db["boss_atual"] = {
            "nome": nome,
            "vida": vida,
            "vida_max": vida,
            "nivel": nivel
        }
        save_rpg_db(db)

        embed = discord.Embed(
            title="⚠️ Novo Boss Invocado!",
            description=f"O administrador {interaction.user.mention} convocou um novo desafio!\n\n👹 **Nome:** `{nome}`\n❤️ **HP:** `{vida:,}`\n⭐ **Nível:** `{nivel}`",
            color=discord.Color.orange()
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="explorar", description="Explore os biomas perigosos de Yggdrasil (Requer Nível 20 ou superior).")
    @app_commands.choices(bioma=[
        app_commands.Choice(name="🌲 Floresta Sombria", value="floresta"),
        app_commands.Choice(name="🌋 Cavernas de Magma", value="magma"),
        app_commands.Choice(name="❄️ Tundra Gelada", value="tundra"),
        app_commands.Choice(name="🏰 Ruínas Ancestrais", value="ruinas")
    ])
    @app_commands.checks.cooldown(1, 60, key=lambda i: i.user.id)
    async def explorar(self, interaction: discord.Interaction, bioma: app_commands.Choice[str]):
        await interaction.response.defer()

        db = load_rpg_db()
        user_id = str(interaction.user.id)

        if user_id not in db["pets"]:
            return await interaction.followup.send("⚠️ Você precisa de um pet para explorar! Use `/pet_adotar` primeiro.", ephemeral=True)

        pet = db["pets"][user_id]

        if pet.get("nivel", 1) < 20:
            return await interaction.followup.send(
                f"❌ **Acesso Negado!** O seu pet está no **Nível {pet.get('nivel', 1)}**.\n"
                "Para explorar as áreas perigosas de Yggdrasil e farmar Golds, seu pet precisa ser no **mínimo Nível 20**!", 
                ephemeral=True
            )

        vida_atual = pet.get("vida", pet.get("stats", {}).get("hp_atual", 100))
        if vida_atual <= 0:
            return await interaction.followup.send("💀 O seu pet está esgotado e sem vida! Cure-o antes de voltar a explorar.", ephemeral=True)
        
        dados_bioma = {
            "floresta": {
                "nome": "🌲 Floresta Sombria",
                "cor": discord.Color.dark_green(),
                "mobs": [
                    "Goblin Arruaceiro", "Lobisomem Feroz", "Aranha Gigante da Bruma", "Ent Corrompido",
                    "Javali Espinhoso", "Slime Venenoso", "Bruxa dos Pântanos", "Ladrão da Mata", 
                    "Pantera Sombria", "Líder dos Trolls da Floresta"
                ],
                "chance_perigo": 0.65
            },
            "magma": {
                "nome": "🌋 Cavernas de Magma",
                "cor": discord.Color.dark_red(),
                "mobs": [
                    "Elemental de Fogo", "Salamandra das Cinzas", "Golem de Obsidiana", "Draconato Guardião",
                    "Morcego Vulcânico", "Esqueleto Magmático", "Dramon Menor", "Lorde das Chamas",
                    "Serpente de Lava", "Titã do Núcleo Fundido"
                ],
                "chance_perigo": 0.75
            },
            "tundra": {
                "nome": "❄️ Tundra Gelada",
                "cor": discord.Color.blue(),
                "mobs": [
                    "Lobo do Ártico", "Espectro de Gelo", "Yeti Selvagem", "Gigante de Frost",
                    "Urso Polar Corrompido", "Elemental de Neve", "Arpia das Neves", "Besta Glacial",
                    "Cavaleiro da Névoa Branca", "Dragão de Gelo Ancestral"
                ],
                "chance_perigo": 0.70
            },
            "ruinas": {
                "nome": "🏰 Ruínas Ancestrais",
                "cor": discord.Color.dark_purple(),
                "mobs": [
                    "Esqueleto Guerreiro", "Cavaleiro Sombrio", "Gárgula de Pedra", "Lich Ancestral",
                    "Fantasma Errante", "Zumbi Desenterrado", "Golem de Ruína", "Sombra Vingativa",
                    "Múmia Guardiã", "Rei Esqueleto Despedaçado"
                ],
                "chance_perigo": 0.85
            }
        }

        info = dados_bioma[bioma.value]
        evento_perigo = random.random() < info["chance_perigo"]

        if evento_perigo:
            monstro = random.choice(info["mobs"])
            chance_vitoria = min(0.35 + (pet.get("nivel", 1) * 0.02), 0.75)  
            vitoria = random.random() < chance_vitoria

            if vitoria:
                ouro_ganho = random.randint(15 * pet.get("nivel", 1), 40 * pet.get("nivel", 1))
                xp_ganho = random.randint(15, 35)
                economy.add_gold(interaction.user.id, ouro_ganho)
                
                pet["vitorias"] = pet.get("vitorias", 0) + 1
                pet["xp"] = pet.get("xp", 0) + xp_ganho
                
                lvl_up = False
                if pet["xp"] >= 150:
                    pet["nivel"] = pet.get("nivel", 1) + 1
                    pet["xp"] -= 150
                    lvl_up = True
                    pet["vida"] = 100

                save_rpg_db(db)

                embed = discord.Embed(
                    title=f"⚔️ Vitória Difícil em {info['nome']}!",
                    description=(
                        f"Após um combate duríssimo, seu pet superou o feroz **{monstro}**!\n\n"
                        f"💰 **Recompensa:** `{ouro_ganho:,}` Golds\n"
                        f"✨ **XP Obtido:** `+{xp_ganho} XP`"
                        f"{' \n\n🎉 **LEVEL UP! Seu pet alcançou o nível ' + str(pet['nivel']) + '!**' if lvl_up else ''}"
                    ),
                    color=discord.Color.green()
                )
            else:
                dano_sofrido = random.randint(35, 65)
                nova_vida = max(0, vida_atual - dano_sofrido)
                pet["vida"] = nova_vida
                if "stats" in pet:
                    pet["stats"]["hp_atual"] = nova_vida
                save_rpg_db(db)

                embed = discord.Embed(
                    title=f"💀 Derrota Brutal em {info['nome']}!",
                    description=(
                        f"O **{monstro}** era impiedoso! Seu pet foi massacrado na batalha e teve que fugir para sobreviver.\n\n"
                        f"💔 **Dano Sofrido:** `-{dano_sofrido} HP`\n"
                        f"❤️ **Vida Atual do Pet:** `{nova_vida}/100 HP`"
                    ),
                    color=discord.Color.red()
                )
        else:
            ouro_ganho = random.randint(10, 25)
            economy.add_gold(interaction.user.id, ouro_ganho)
            pet["xp"] = pet.get("xp", 0) + 10
            
            save_rpg_db(db)

            embed = discord.Embed(
                title=f"🧭 Calmaria em {info['nome']}",
                description=(
                    f"Por sorte, nenhum monstro mortal atacou. Seu pet encontrou restos de provisões:\n\n"
                    f"💰 **Achado:** `{ouro_ganho}` Golds\n"
                    f"✨ **Experiência:** `+10 XP`"
                ),
                color=info["cor"]
            )

        if pet.get("nivel", 1) >= 20 and not pet.get("convite_enviado", False):
            pet["convite_enviado"] = True
            save_rpg_db(db)

            convite_embed = discord.Embed(
                title="🌟 Seu Pet Alcançou o Nível 20!",
                description=(
                    f"O companheiro de {interaction.user.mention} ficou forte o suficiente para se tornar um **Aventureiro Oficial** de Yggdrasil!\n\n"
                    "Deseja aceitar o título de Aventureiro para desbloquear **canais exclusivos** e provar seu valor?"
                ),
                color=discord.Color.blurple()
            )
            view = AventureiroConfirmView(CARGO_AVENTUREIRO_ID, CANAL_ESPECIFICO_ID)
            
            ID_CANAL_AVISO = 1537883858467430552
            canal_aviso = interaction.guild.get_channel(ID_CANAL_AVISO)

            if canal_aviso:
                await canal_aviso.send(content=interaction.user.mention, embed=convite_embed, view=view)
            else:
                await interaction.followup.send(f"{interaction.user.mention}", embed=convite_embed, view=view, ephemeral=False)

        embed.set_footer(text=f"Explorador: {interaction.user.display_name} • 🐾 Pet: {pet.get('nome', 'Pet')} (Nv. {pet.get('nivel', 1)})")
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PetRPG(bot))
