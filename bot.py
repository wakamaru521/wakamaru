import discord
from discord import app_commands
from discord.ui import Button, View
import sqlite3
import random
import datetime
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

conn = sqlite3.connect("players.db")
c = conn.cursor()

# DB
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

conn.commit()

participants=[]
current_teams=[]

# profile
@tree.command(name="profile")
async def profile(interaction:discord.Interaction,
switch_name:str,
friend_code:str,
casual_rate:int,
lounge12:int,
lounge24:int,
memo:str="なし"):

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

    await interaction.response.send_message("登録完了")

# show
@tree.command(name="show")
async def show(interaction:discord.Interaction,user:discord.Member=None):

    if user is None:
        user=interaction.user

    c.execute("SELECT * FROM players WHERE user_id=?",(user.id,))
    data=c.fetchone()

    if not data:
        await interaction.response.send_message("未登録")
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

# checkin
@tree.command(name="checkin")
async def checkin(interaction:discord.Interaction):

    if interaction.user.id not in participants:
        participants.append(interaction.user.id)

    await interaction.response.send_message("参加登録")

# tournament
@tree.command(name="tournament")
async def tournament(interaction:discord.Interaction,teams:int):

    global current_teams

    players=[]

    for uid in participants:

        c.execute("SELECT lounge12,discord_name FROM players WHERE user_id=?",(uid,))
        data=c.fetchone()

        if data:
            players.append((uid,data[1],data[0]))

    players.sort(key=lambda x:x[2],reverse=True)

    team_list=[[] for _ in range(teams)]
    team_score=[0]*teams

    for uid,name,rate in players:

        idx=team_score.index(min(team_score))

        team_list[idx].append((uid,name,rate))
        team_score[idx]+=rate

    current_teams=team_list

    embed=discord.Embed(title="Tournament Teams",color=discord.Color.red())

    for i,team in enumerate(team_list):

        txt=""

        for uid,name,rate in team:
            txt+=f"<@{uid}> ({rate})\n"

        embed.add_field(name=f"Team{i+1}",value=txt)

    await interaction.response.send_message(embed=embed)

# sync command (手動)
@tree.command(name="sync")
async def sync(interaction:discord.Interaction):

    await tree.sync()

    await interaction.response.send_message("コマンド同期完了")

@client.event
async def on_ready():

    print(f"Bot起動: {client.user}")

client.run(TOKEN)