import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

players = []
tournament_message = None

update_queue = asyncio.Queue()


# -----------------------------
# 429防止 更新キュー
# -----------------------------

async def updater():
    await bot.wait_until_ready()
    while not bot.is_closed():

        message, embed, view = await update_queue.get()

        try:
            await message.edit(embed=embed, view=view)
        except Exception as e:
            print("Update error:", e)

        await asyncio.sleep(2)


# -----------------------------
# UI VIEW
# -----------------------------

class TournamentView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="参加", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer(ephemeral=True)

        user = interaction.user

        if user in players:
            await interaction.followup.send("既に参加しています", ephemeral=True)
            return

        players.append(user)

        await interaction.followup.send("参加しました", ephemeral=True)

        await update_embed(interaction.message)


    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.red)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer(ephemeral=True)

        user = interaction.user

        if user not in players:
            await interaction.followup.send("参加していません", ephemeral=True)
            return

        players.remove(user)

        await interaction.followup.send("キャンセルしました", ephemeral=True)

        await update_embed(interaction.message)


    @discord.ui.button(label="開始", style=discord.ButtonStyle.blurple)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("管理者のみ", ephemeral=True)
            return

        await interaction.response.defer()

        await interaction.followup.send("大会開始！")



    @discord.ui.button(label="リセット", style=discord.ButtonStyle.gray)
    async def reset(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("管理者のみ", ephemeral=True)
            return

        await interaction.response.defer()

        players.clear()

        await interaction.followup.send("大会をリセットしました")

        await update_embed(interaction.message)



# -----------------------------
# Embed作成
# -----------------------------

def create_embed():

    embed = discord.Embed(
        title="🏆 大会参加受付",
        description="ボタンを押して参加してください",
        color=0x00ffcc
    )

    if players:
        player_list = "\n".join([p.mention for p in players])
    else:
        player_list = "まだ参加者はいません"

    embed.add_field(
        name=f"参加者 ({len(players)})",
        value=player_list,
        inline=False
    )

    return embed


# -----------------------------
# 更新処理
# -----------------------------

async def update_embed(message):

    embed = create_embed()
    view = TournamentView()

    await update_queue.put((message, embed, view))


# -----------------------------
# コマンド
# -----------------------------

@bot.command()
async def 大会(ctx):

    global tournament_message

    embed = create_embed()
    view = TournamentView()

    tournament_message = await ctx.send(embed=embed, view=view)


# -----------------------------
# 起動
# -----------------------------

@bot.event
async def on_ready():

    print("BOT READY")

    bot.loop.create_task(updater())

    await asyncio.sleep(5)


bot.run(TOKEN)