import discord
from discord import app_commands
from discord.ui import View, Button
import sqlite3
import random
import datetime
import asyncio
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# =========================
# DATABASE
# =========================

conn = sqlite3.connect("players.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS players(
user_id INTEGER PRIMARY KEY,
discord_name TEXT,
switch_name TEXT,
friend_code TEXT,
casual_rate INTEGER,
lounge12 INTEGER,
lounge24 INTEGER,
memo TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS rate_history(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
lounge12 INTEGER,
lounge24 INTEGER,
date TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS tournament_results(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
points INTEGER,
date TEXT
)
""")

conn.commit()

participants=[]
current_teams=[]

# =========================
# PROFILE
# =========================

@tree.command(
name="profile",
description="プレイヤープロフィールを登録または更新します"
)
@app_commands.describe(
switch_name="Switchのユーザー名",
friend_code="フレンドコード",
casual_rate="野良レート",
lounge12="Lounge12レート",
lounge24="Lounge24レート",
memo="メモ（任意）"
)
async def profile(
interaction:discord.Interaction,
switch_name:str,
friend_code:str,
casual_rate:int,
lounge12:int,
lounge24:int,
memo:str="なし"
):

    c.execute("REPLACE INTO players VALUES(?,?,?,?,?,?,?,?)",
    (interaction.user.id,
     interaction.user.name,
     switch_name,
     friend_code,
     casual_rate,
     lounge12,
     lounge24,
     memo))

    conn.commit()

    await interaction.response.send_message("プロフィール登録完了")

# =========================
# SHOW PROFILE
# =========================

@tree.command(
name="show",
description="プロフィールを表示します"
)
@app_commands.describe(
user="表示するユーザー"
)
async def show(
interaction:discord.Interaction,
user:discord.Member=None
):

    if user is None:
        user=interaction.user

    c.execute("SELECT * FROM players WHERE user_id=?",(user.id,))
    data=c.fetchone()

    if not data:
        await interaction.response.send_message("未登録です")
        return

    embed=discord.Embed(
    title=f"{data[1]} のプロフィール",
    color=discord.Color.blue())

    embed.add_field(name="Switch名",value=data[2],inline=False)
    embed.add_field(name="FC",value=data[3])
    embed.add_field(name="野良レート",value=data[4])
    embed.add_field(name="Lounge12",value=data[5])
    embed.add_field(name="Lounge24",value=data[6])
    embed.add_field(name="メモ",value=data[7],inline=False)

    await interaction.response.send_message(embed=embed)

# =========================
# CHECKIN UI
# =========================

class CheckinView(View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="参加",style=discord.ButtonStyle.green)
    async def join(self,interaction,button):

        if interaction.user.id not in participants:
            participants.append(interaction.user.id)

        await interaction.response.send_message(
        "参加登録しました",
        ephemeral=True
        )

    @discord.ui.button(label="キャンセル",style=discord.ButtonStyle.red)
    async def leave(self,interaction,button):

        if interaction.user.id in participants:
            participants.remove(interaction.user.id)

        await interaction.response.send_message(
        "参加をキャンセルしました",
        ephemeral=True
        )

# =========================
# OPEN CHECKIN
# =========================

@tree.command(
name="checkin_open",
description="大会参加ボタンを表示します"
)
async def checkin_open(interaction:discord.Interaction):

    view=CheckinView()

    await interaction.response.send_message(
    "大会参加はこちら",
    view=view
    )

# =========================
# TEAM BALANCE
# =========================

def create_balanced_teams(team_count):

    players=[]

    for uid in participants:

        c.execute("SELECT lounge12,discord_name FROM players WHERE user_id=?",(uid,))
        data=c.fetchone()

        if data:
            players.append((uid,data[1],data[0]))

    players.sort(key=lambda x:x[2],reverse=True)

    teams=[[] for _ in range(team_count)]
    scores=[0]*team_count

    for p in players:

        idx=scores.index(min(scores))
        teams[idx].append(p)
        scores[idx]+=p[2]

    return teams

# =========================
# TOURNAMENT CREATE
# =========================

@tree.command(
name="tournament",
description="大会チームを自動生成します"
)
@app_commands.describe(
teams="チーム数"
)
async def tournament(
interaction:discord.Interaction,
teams:int
):

    global current_teams

    if len(participants)<teams:

        await interaction.response.send_message("人数不足")
        return

    current_teams=create_balanced_teams(teams)

    embed=discord.Embed(
    title="大会チーム",
    color=discord.Color.red()
    )

    for i,team in enumerate(current_teams):

        txt=""

        for uid,name,rate in team:

            txt+=f"<@{uid}> ({rate})\n"

        embed.add_field(
        name=f"Team{i+1}",
        value=txt,
        inline=False
        )

    await interaction.response.send_message(embed=embed)

# =========================
# SHUFFLE
# =========================

@tree.command(
name="shuffle",
description="チームをシャッフルします"
)
async def shuffle(interaction:discord.Interaction):

    global current_teams

    flat=[p for team in current_teams for p in team]

    random.shuffle(flat)

    size=len(current_teams)

    teams=[[] for _ in range(size)]

    for i,p in enumerate(flat):

        teams[i%size].append(p)

    current_teams=teams

    await interaction.response.send_message("シャッフル完了")

# =========================
# RESULT
# =========================

@tree.command(
name="result",
description="大会結果ポイントを登録"
)
@app_commands.describe(
user="プレイヤー",
points="獲得ポイント"
)
async def result(
interaction:discord.Interaction,
user:discord.Member,
points:int
):

    c.execute(
    "INSERT INTO tournament_results VALUES(NULL,?,?,?)",
    (user.id,points,str(datetime.date.today()))
    )

    conn.commit()

    await interaction.response.send_message("結果登録完了")

# =========================
# RANKING
# =========================

@tree.command(
name="tournament_rank",
description="大会ランキング表示"
)
async def tournament_rank(interaction:discord.Interaction):

    c.execute("""
    SELECT players.discord_name,
    SUM(tournament_results.points)
    FROM tournament_results
    JOIN players
    ON players.user_id=tournament_results.user_id
    GROUP BY tournament_results.user_id
    ORDER BY SUM(points) DESC
    LIMIT 10
    """)

    data=c.fetchall()

    txt=""

    for i,(name,pts) in enumerate(data,start=1):

        txt+=f"{i}. {name} - {pts}\n"

    embed=discord.Embed(
    title="大会ランキング",
    description=txt,
    color=discord.Color.gold()
    )

    await interaction.response.send_message(embed=embed)

# =========================
# RATE HISTORY
# =========================

@tree.command(
name="rate_history",
description="レート履歴表示"
)
@app_commands.describe(
user="プレイヤー"
)
async def rate_history(
interaction:discord.Interaction,
user:discord.Member
):

    c.execute(
    "SELECT lounge12,lounge24,date FROM rate_history WHERE user_id=?",
    (user.id,)
    )

    data=c.fetchall()

    txt=""

    for r in data:

        txt+=f"{r[2]} 12:{r[0]} 24:{r[1]}\n"

    embed=discord.Embed(
    title="レート履歴",
    description=txt
    )

    await interaction.response.send_message(embed=embed)

# =========================
# SYNC
# =========================

@tree.command(
name="sync",
description="スラッシュコマンド同期"
)
async def sync(interaction:discord.Interaction):

    await tree.sync()

    await interaction.response.send_message("同期完了")

# =========================

@client.event
async def on_ready():

    print(f"Bot起動: {client.user}")

client.run(TOKEN)