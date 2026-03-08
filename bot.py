import discord
from discord import app_commands
from discord.ui import View, Button
import sqlite3
import os
import random
import datetime

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

conn = sqlite3.connect("players.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS players(
user_id INTEGER PRIMARY KEY,
name TEXT,
rate INTEGER
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS results(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
points INTEGER,
date TEXT
)
""")

conn.commit()

participants=[]
teams=[]

# UI

class CheckinView(View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="参加",style=discord.ButtonStyle.green)
    async def join(self,interaction,button):

        if interaction.user.id not in participants:
            participants.append(interaction.user.id)

        await interaction.response.send_message(
        "参加登録しました",
        ephemeral=True)

    @discord.ui.button(label="キャンセル",style=discord.ButtonStyle.red)
    async def leave(self,interaction,button):

        if interaction.user.id in participants:
            participants.remove(interaction.user.id)

        await interaction.response.send_message(
        "参加をキャンセルしました",
        ephemeral=True)

# checkin

@tree.command(
name="checkin_open",
description="大会参加ボタンを表示"
)
async def checkin_open(interaction:discord.Interaction):

    view=CheckinView()

    await interaction.response.send_message(
    "参加はこちら",
    view=view)

# profile

@tree.command(
name="profile",
description="レート登録"
)
@app_commands.describe(
rate="プレイヤーレート"
)
async def profile(interaction:discord.Interaction,rate:int):

    c.execute(
    "REPLACE INTO players VALUES(?,?,?)",
    (interaction.user.id,interaction.user.name,rate))

    conn.commit()

    await interaction.response.send_message("登録完了")

# team balance

def make_teams(team_count):

    plist=[]

    for uid in participants:

        c.execute("SELECT name,rate FROM players WHERE user_id=?",(uid,))
        data=c.fetchone()

        if data:
            plist.append((uid,data[0],data[1]))

    plist.sort(key=lambda x:x[2],reverse=True)

    teams=[[] for _ in range(team_count)]
    scores=[0]*team_count

    for p in plist:

        idx=scores.index(min(scores))
        teams[idx].append(p)
        scores[idx]+=p[2]

    return teams

# tournament

@tree.command(
name="tournament",
description="大会チーム生成"
)
@app_commands.describe(
teams="チーム数"
)
async def tournament(interaction:discord.Interaction,teams:int):

    global teams

    if len(participants)==0:

        await interaction.response.send_message("参加者なし")
        return

    teams=make_teams(teams)

    embed=discord.Embed(
    title="大会チーム",
    color=discord.Color.red())

    for i,t in enumerate(teams):

        txt=""

        for uid,name,rate in t:
            txt+=f"<@{uid}> ({rate})\n"

        embed.add_field(
        name=f"Team{i+1}",
        value=txt,
        inline=False)

    await interaction.response.send_message(embed=embed)

# result

@tree.command(
name="result",
description="大会ポイント登録"
)
@app_commands.describe(
user="プレイヤー",
points="ポイント"
)
async def result(
interaction:discord.Interaction,
user:discord.Member,
points:int
):

    c.execute(
    "INSERT INTO results VALUES(NULL,?,?,?)",
    (user.id,points,str(datetime.date.today()))
    )

    conn.commit()

    await interaction.response.send_message("結果登録")

# ranking

@tree.command(
name="ranking",
description="大会ランキング"
)
async def ranking(interaction:discord.Interaction):

    c.execute("""
    SELECT players.name,
    SUM(results.points)
    FROM results
    JOIN players
    ON players.user_id=results.user_id
    GROUP BY results.user_id
    ORDER BY SUM(points) DESC
    """)

    data=c.fetchall()

    txt=""

    for i,(name,pts) in enumerate(data,start=1):

        txt+=f"{i}. {name} - {pts}\n"

    embed=discord.Embed(
    title="大会ランキング",
    description=txt,
    color=discord.Color.gold())

    await interaction.response.send_message(embed=embed)

# sync

@tree.command(
name="sync",
description="コマンド同期（管理者用）"
)
async def sync(interaction:discord.Interaction):

    if not interaction.user.guild_permissions.administrator:

        await interaction.response.send_message("管理者のみ")
        return

    await tree.sync()

    await interaction.response.send_message("sync完了")

@client.event
async def on_ready():

    print(f"Bot起動: {client.user}")

client.run(TOKEN)