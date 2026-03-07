import discord
from discord import app_commands
from discord.ui import Button, View
import sqlite3
import random
import datetime

TOKEN = "MTQ3OTc1NDg4MjY3MDkxOTgwNA.G_SPhm.Rph06JqL6NqLCChX4_31qY-yDRJgp8BMXd_KwU"

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

conn = sqlite3.connect("players.db")
c = conn.cursor()

# =================
# DB
# =================

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

# =================
# プロフィール
# =================

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

# =================
# show
# =================

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

# =================
# レート更新
# =================

@tree.command(name="update_rate")
async def update_rate(interaction:discord.Interaction,
user:discord.Member,
casual_rate:int=None,
lounge12:int=None,
lounge24:int=None):

    if casual_rate:
        c.execute("UPDATE players SET casual_rate=? WHERE user_id=?",(casual_rate,user.id))

    if lounge12:
        c.execute("UPDATE players SET lounge12=? WHERE user_id=?",(lounge12,user.id))

    if lounge24:
        c.execute("UPDATE players SET lounge24=? WHERE user_id=?",(lounge24,user.id))

    c.execute("INSERT INTO rate_history(user_id,lounge12,lounge24,date) VALUES(?,?,?,?)",
    (user.id,lounge12,lounge24,str(datetime.date.today())))

    conn.commit()

    await interaction.response.send_message("レート更新")

# =================
# FC
# =================

@tree.command(name="fc")
async def fc(interaction:discord.Interaction,user:discord.Member):

    c.execute("SELECT friend_code FROM players WHERE user_id=?",(user.id,))
    data=c.fetchone()

    if not data:
        await interaction.response.send_message("未登録")
        return

    await interaction.response.send_message(data[0])

# =================
# チェックイン
# =================

@tree.command(name="checkin")
async def checkin(interaction:discord.Interaction):

    if interaction.user.id not in participants:
        participants.append(interaction.user.id)

    await interaction.response.send_message("参加登録")

# =================
# トーナメント
# =================

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

# =================
# チームシャッフル
# =================

@tree.command(name="shuffle_teams")
async def shuffle_teams(interaction:discord.Interaction):

    global current_teams

    flat=[p for team in current_teams for p in team]

    random.shuffle(flat)

    size=len(current_teams)

    teams=[[] for _ in range(size)]

    for i,p in enumerate(flat):
        teams[i%size].append(p)

    current_teams=teams

    await interaction.response.send_message("チームシャッフル完了")

# =================
# ランキングUI
# =================

class RankView(View):

    def __init__(self,mode,offset=0):

        super().__init__(timeout=None)
        self.mode=mode
        self.offset=offset

    async def update(self,interaction):

        if self.mode=="lounge12":
            c.execute("SELECT discord_name,lounge12 FROM players ORDER BY lounge12 DESC LIMIT 10 OFFSET ?",(self.offset,))
            title="Lounge12 Ranking"

        elif self.mode=="lounge24":
            c.execute("SELECT discord_name,lounge24 FROM players ORDER BY lounge24 DESC LIMIT 10 OFFSET ?",(self.offset,))
            title="Lounge24 Ranking"

        else:
            c.execute("SELECT discord_name,casual_rate FROM players ORDER BY casual_rate DESC LIMIT 10 OFFSET ?",(self.offset,))
            title="Casual Rate Ranking"

        results=c.fetchall()

        txt=""

        for i,(name,rate) in enumerate(results,start=self.offset+1):
            txt+=f"{i}. {name} - {rate}\n"

        embed=discord.Embed(title=title,description=txt,color=discord.Color.gold())

        await interaction.response.edit_message(embed=embed,view=self)

    @discord.ui.button(label="1-10")
    async def p1(self,interaction,button):
        self.offset=0
        await self.update(interaction)

    @discord.ui.button(label="11-20")
    async def p2(self,interaction,button):
        self.offset=10
        await self.update(interaction)

    @discord.ui.button(label="21-30")
    async def p3(self,interaction,button):
        self.offset=20
        await self.update(interaction)

# =================
# rank
# =================

@tree.command(name="rank")
async def rank(interaction:discord.Interaction,mode:str):

    view=RankView(mode)

    await view.update(interaction)

# =================
# レート履歴
# =================

@tree.command(name="rate_history")
async def rate_history(interaction:discord.Interaction,user:discord.Member):

    c.execute("SELECT lounge12,lounge24,date FROM rate_history WHERE user_id=?",(user.id,))
    data=c.fetchall()

    txt=""

    for r in data:
        txt+=f"{r[2]} 12:{r[0]} 24:{r[1]}\n"

    embed=discord.Embed(title="Rate History",description=txt)

    await interaction.response.send_message(embed=embed)

# =================

@client.event
async def on_ready():

    await tree.sync()
    print("Bot起動")

client.run(TOKEN)