import discord
from discord.ext import commands
import asyncio
import json
import random
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"


# ----------------
# データ保存
# ----------------

def load_data():

    if not os.path.exists(DATA_FILE):

        return {"players": []}

    with open(DATA_FILE) as f:

        return json.load(f)


def save_data(data):

    with open(DATA_FILE, "w") as f:

        json.dump(data, f, indent=2)


# ----------------
# 429対策キュー
# ----------------

update_queue = asyncio.Queue()


async def queue_worker():

    await bot.wait_until_ready()

    while True:

        message, embed, view = await update_queue.get()

        try:
            await message.edit(embed=embed, view=view)
        except:
            pass

        await asyncio.sleep(2)


# ----------------
# トーナメント生成
# ----------------

def make_teams(players):

    random.shuffle(players)

    teams = []

    for i in range(0, len(players), 2):

        teams.append(players[i:i+2])

    return teams


def make_bracket(teams):

    bracket = []

    for i in range(0, len(teams), 2):

        if i+1 < len(teams):

            bracket.append((teams[i], teams[i+1]))

    return bracket


# ----------------
# Embed
# ----------------

def create_embed(guild):

    data = load_data()

    players = data["players"]

    embed = discord.Embed(
        title="🏆大会参加",
        description="ボタンで参加",
        color=0x00ffcc
    )

    if not players:

        embed.add_field(name="参加者", value="なし")

    else:

        text = ""

        for p in players:

            m = guild.get_member(p)

            if m:

                text += m.mention + "\n"

        embed.add_field(
            name=f"参加者 ({len(players)})",
            value=text,
            inline=False
        )

    return embed


# ----------------
# UI
# ----------------

class TournamentView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)


    @discord.ui.button(label="参加", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = load_data()

        players = data["players"]

        if interaction.user.id in players:

            await interaction.response.send_message(
                "既に参加しています",
                ephemeral=True
            )
            return

        players.append(interaction.user.id)

        save_data(data)

        await interaction.response.send_message(
            "参加しました",
            ephemeral=True
        )

        await update_message(interaction.message)


    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.red)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = load_data()

        players = data["players"]

        if interaction.user.id not in players:

            await interaction.response.send_message(
                "参加していません",
                ephemeral=True
            )
            return

        players.remove(interaction.user.id)

        save_data(data)

        await interaction.response.send_message(
            "キャンセルしました",
            ephemeral=True
        )

        await update_message(interaction.message)


    @discord.ui.button(label="チーム生成", style=discord.ButtonStyle.blurple)
    async def teams(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                "管理者のみ",
                ephemeral=True
            )
            return

        data = load_data()

        members = [interaction.guild.get_member(p) for p in data["players"]]

        teams = make_teams(members)

        text = ""

        for i, t in enumerate(teams):

            names = " , ".join([m.display_name for m in t])

            text += f"Team{i+1}: {names}\n"

        await interaction.response.send_message(text)


    @discord.ui.button(label="トーナメント", style=discord.ButtonStyle.gray)
    async def bracket(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                "管理者のみ",
                ephemeral=True
            )
            return

        data = load_data()

        members = [interaction.guild.get_member(p) for p in data["players"]]

        teams = make_teams(members)

 ブラケット = make_bracket(サン)

 ガァンガァ = 「🏆ガァン\n\n」

 いちゃいちゃ、いちゃいちゃ 列挙い(カワサワ):

 t1 = 「 」。参加([エム。じょしゃんしゃんしゃん_名割 じょしゃんしゃく m ち 試合[0]])

 t2 = 「 」。参加([エム。じょしゃんしゃんしゃん_名割 じょしゃんしゃく m ち 試合[1]])

 ガツガツ += f"マ{i+1}\ん{t1}\nVS\n{t2}\n\n"

 得つ 交流。応答。send_サササ(ゆううううう)


# ----------------
# UI更新
# ----------------

非同期 def 更水_ガンガン(サン・トゥ・トゥ・):

 看込す = create_embed(・・・・・。カロン)

 ・・・・ = ウォンテガンロガン()

 得つ update_queue。置く((・〜〜〜〜〜))


# ----------------
# みかん
# ----------------

@・ガンガンガンガンガン()
非同期 def 大会(ctx):

 看込す = create_embed(ctx。カロン)

 ・・・・ = ウォンテガンロガン()

 得つ ctx。送信(埋座込き=埋座込き、表示=表示)


# ----------------
# 起動
# ----------------

@〜〜〜〜〜
非同期 def サ_準備完了():

    印刷(「工準備完了」)

 ・・・・。・・・・。create_task(サロン_サロン())


・・・・。看る(よぉ〜ん)
