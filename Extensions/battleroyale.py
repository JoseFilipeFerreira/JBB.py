import discord
from discord.ext import commands
import random
import datetime
from random import randint
from random import choice
import asyncio
import json
import operator

class BattleRoyale():
    def __init__(self, bot):
        self.bot = bot
        self.listAction = ["kill", "die", "event", "meet"]
        self.listReactions=[]
        with open(bot.BATTLEROYALE_PATH, 'r') as file:
            self.listReactions = json.load(file)
        with open(bot.BATTLEROYALEWINS_PATH, 'r') as file:
            self.listWinners = json.load(file)
        with open(bot.BATTLEROYALEKDR_PATH, 'r') as file:
            self.listKdr = json.load(file)

    @commands.command(name='battleroyale',
                      description="create server battle royale",
                      brief="server battle royale",
                      pass_context=True)
    async def battleroyale(self, ctx):
    #TODO: make it so that people don't cry by seeing this piece of code
    #create battle royale
        if ctx.message.channel.name not in ['nsfw', 'bot-commands']:
            await self.bot.say(
                "This command must be done in #nsfw or #bot-commands"
            )
            return
        await self.bot.delete_message(ctx.message)
        msg = await sendChallenge(self, ctx)
        await thirtysecondtyping(self, ctx)
        users = await getListUsers(self, ctx, msg.reactions[0])
        
        if len(users["alive"]) < 2:
            await self.bot.say("Not enough players for a Battle Royale")
            return

        await sendAllDailyReports(self, ctx, users)

        embed = victoryEmbed(self, users["alive"][0])
        await self.bot.say(embed=embed)

        updateWinners(self, users["alive"][0])
        updateKDR(self, users)
    
    @commands.command(name='battleroyaleWinners',
                      description="battleroyale leaderboard",
                      brief="battleroyale leaderboard",
                      pass_context=True)
    async def battleroyaleWinners(self, ctx):
    #TODO IMPROVE THIS HOT PIECE OF GARBAGE ASAP
        winner = self.listWinners.copy()

        embed = discord.Embed(
            title = 'Battleroyale no DI',
            description="Wins Leaderboard",
            color=self.bot.embed_color
        )
        for i in range(3):
            win = max(winner.items(), key=operator.itemgetter(1))
            winner.pop(win[0])
            member = ctx.message.server.get_member(win[0])
            name = member.name
            if member.nick != None:
                name = member.nick

            embed.add_field(
                name="{0}. {1}".format(i + 1, name),
                value="Number of Wins: {0}".format(win[1]),
                inline=False
            )
            
            embed.set_thumbnail(
                url="https://mbtskoudsalg.com/images/pubg-lvl-3-helmet-png-7.png"
            )

        await self.bot.say(embed=embed)

    @commands.command(name='battleroyaleKDR',
                      description="battleroyale Kill/Death Ratio",
                      brief="battleroyale Kill/Death Ratio",
                      pass_context=True)
    async def battleroyaleKDR(self, ctx):

        if len(ctx.message.mentions) > 0:
            for user in ctx.message.mentions:
                member = ctx.message.server.get_member(user.id)
                win = self.listKdr[user.id]
                embed = discord.Embed(
                    title = 'Battleroyale no DI',
                    description="KDR Leaderboard",
                    color=self.bot.embed_color
                )
                name = member.name
                if member.nick != None:
                    name = member.nick
                embed.add_field(
                    name=name,
                    value="KDR: {0}/{1}".format(win["kills"], win["death"]),
                inline=False
                )
                await self.bot.say(embed=embed)
            return

        arrayKDR = []

        for id in self.listKdr.keys():
            kdr = {"id": id,
            "kills": self.listKdr[id]["kills"],
            "death": self.listKdr[id]["death"]}

            arrayKDR.append(kdr)
        
        def compare(kdr):
            return kdr["kills"] / kdr["death"]
        
        arrayKDR.sort(key=compare, reverse=True)


        embed = discord.Embed(
            title = 'Battleroyale no DI',
            description="KDR Leaderboard",
            color=self.bot.embed_color
        )
        for i in range(3):
            win = arrayKDR[i]
            member = ctx.message.server.get_member(win["id"])
            name = member.name
            if member.nick != None:
                name = member.nick

            embed.add_field(
                name="{0}. {1}".format(i + 1, name),
                value="KDR: {0}/{1}".format(win["kills"], win["death"]),
                inline=False
            )
            
            embed.set_thumbnail(
                url="https://mbtskoudsalg.com/images/pubg-lvl-3-helmet-png-7.png"
            )

        await self.bot.say(embed=embed)
    @commands.command(name='addBattleroyale',
                      description="add a Battleroyale event to the json [OWNER ONLY]",
                      brief="add a Battleroyale event",
                      pass_context=True)
    async def addBattleroyale(self, ctx, action, time,*, description):
        appInfo = await self.bot.application_info()
        owner = appInfo.owner
        action = action.lower()
        time = round(float(time), 1)
        time = round_down(time * 10, 5)
        time = time /10
        #TODO optimize one day
        if ctx.message.author != owner:
            await self.bot.say('Invalid user')

        elif len(description) < 1:
            await self.bot.say('Invalid description')
        
        elif action not in self.listAction:
            await self.bot.say('Invalid action')

        elif time <= 0 or time > 12:
            await self.bot.say('Invalid time')

        else:
            event = {
                "action":self.listAction.index(action),
                "time":time,
                "description":description
            }
            print(event)
            self.listReactions.append(event)
            updateListReactions(self)
            await self.bot.say("**action:**`{0}`\n**time:**`{1}`h\n**description:**`{2}`".format(action, time, description))  

    @commands.command(name='deleteBattleroyale',
                      description="delete the last Battleroyale event on the json [OWNER ONLY]",
                      brief="remove last Battleroyale event",
                      aliases=['removeBattleroyale'],
                      pass_context=True)
    async def deleteBattleroyale(self, ctx):
        appInfo = await self.bot.application_info()
        owner = appInfo.owner
        #TODO optimize one day
        if ctx.message.author != owner:
            await self.bot.say('Invalid user')
        else:
            deleted = self.listReactions.pop()
            updateListReactions(self)
            await self.bot.say(
                "__**DELETED**__\n**action:**`{0}`\n**time:**`{1}`h\n**description:**`{2}`"
                    .format(
                        deleted["action"],
                        deleted["time"],
                        deleted["description"]
                    )
            )  

async def sendAllDailyReports(self, ctx, users):
#gets a list of all users and sends all days
    #check if enough users
    await sendInitialReport(self, ctx)

    day = 1
    time = getCurrentHour()
    while(len(users["alive"]) > 1):
        figthTrailer, users = generateDailyReport(self, ctx, users, time)
        await sendDaylyReport(self, ctx, day, figthTrailer)
        time = 24
        day = day + 1

def getCurrentHour():
#gets current hour irl
    now = datetime.datetime.now()
    time = 24 - now.hour
    if now.minute > 30:
        time = time - 1
    elif now.minute > 0:
        time = time - 0.5
    return time

def generateDailyReport(self, ctx, users, time):
#generates a string with a daily report and returns a list containing survivors
    figthTrailer = ""
    while(len(users["alive"]) > 1 and time > 0):
        match = choice(self.listReactions)
        if time - match["time"] <= 0:
            break
        elif match["action"] == 0: #kill
            p1 = choice(users["alive"])
            users["alive"].remove(p1)
            users["dead"].append(p1)

            p2 = choice(users["alive"])
            p2["kills"] += 1

            figthResult = match["description"].format(p1["name"], p2["name"])

        elif match["action"] == 1: #die
            p1 = choice(users["alive"])
            users["alive"].remove(p1)
            users["dead"].append(p1)

            figthResult = match["description"].format(p1["name"])
        elif match["action"] == 2: #event
            p1 = choice(users["alive"])

            figthResult = match["description"].format(p1["name"])

        elif match["action"] == 3: #meet
            p1 = choice(users["alive"])
            p2 = choice(users["alive"])

            figthResult = match["description"].format(p1["name"], p2["name"])
        
        time = time - match["time"]
        figthTrailer = figthTrailer + "**" + convertHour(time) + "** " + figthResult + "\n"

    return figthTrailer, users

async def sendDaylyReport(self, ctx, day, result):
#send a embed with the daily report
    if result == "": result = "Today nothing happened"
    embed = discord.Embed(
        title = 'DAY {}'.format(day),
        description=result,
        color=self.bot.embed_color
    )
    await self .bot.send_message(ctx.message.channel, embed=embed)

async def sendInitialReport(self,ctx):
#send first embed of report
    embed = discord.Embed(
        title = 'Battle Royale no DI',
        description='Result of the battle',
        color=self.bot.embed_color
    )
    embed.set_thumbnail(
    url="https://mbtskoudsalg.com/images/pubg-lvl-3-helmet-png-7.png"
    )
    await self.bot.say(embed=embed)

async def thirtysecondtyping(self, ctx):
#wait 30 seconds for people to join while typing
    await self.bot.send_typing(ctx.message.channel)
    await asyncio.sleep(9)
    await self.bot.send_typing(ctx.message.channel)
    await asyncio.sleep(9)
    await self.bot.send_typing(ctx.message.channel)
    await asyncio.sleep(9)

async def getListUsers(self, ctx, reaction):
#create a list with the users that reacted
    users = await self.bot.get_reaction_users(reaction)
    return correctListUsers(ctx, users)

def correctListUsers(ctx, users):
#takes a list of users and gives a list of user name/nick an id
    users = list(filter(lambda x: not x.bot, users))

    def changeNick(user):
        member = ctx.message.server.get_member(user.id)
        name = member.name
        if member.nick != None:
            name = member.nick
        return {
                "name": name,
                "id": user.id,
                "kills": 0
            }

    users = list(map(changeNick , users))
    users = [i for n, i in enumerate(users) if i not in users[n+1:]]
    return {"alive": users, "dead": []}

async def sendChallenge(self, ctx):
#generate embed
    embed = discord.Embed(
        title = 'Battle Royale no DI',
        description='{} started a battle royale'.format(ctx.message.author.mention),
        color=self.bot.embed_color
    )
    embed.set_thumbnail(
        url="https://mbtskoudsalg.com/images/pubg-lvl-3-helmet-png-7.png"
    )
    embed.add_field(
        name='Pick your weapon below if you wish to participate',
        value='(you have approximately 30 seconds)'
    )
    msg = await self.bot.send_message(ctx.message.channel,embed=embed)
    await self.bot.add_reaction(msg, '\U0001F52B')
    #update sent embed so it contains the reaction
    return await self.bot.get_message(msg.channel, msg.id)

def round_down(num, divisor):
#round down a num to the nearest multiple of a divisor
    return num - (num%divisor)

def convertHour(time):
#convert time in hours to midnigth to hour of day
    time = 24 - time
    minutes = time * 60
    hours, minutes = divmod(minutes, 60)
    hours = int(hours)
    minutes = int(minutes)
    if hours < 10:
        hours = "0{}".format(hours)
    if minutes < 10:
        minutes = "0{}".format(minutes)
    return "{0}:{1}h".format(hours, minutes)

def updateListReactions(self):
#update a JSON file
    with open(self.bot.BATTLEROYALE_PATH, 'w') as file:
        json.dump(self.listReactions, file, indent=4)

def updateWinners(self, winner):
#update winners JSON file
    winner = winner["id"]
    if not winner in self.listWinners:
        self.listWinners[winner] = 1
    else:
        self.listWinners[winner] += 1
    
    with open(self.bot.BATTLEROYALEWINS_PATH, 'w') as file:
        json.dump(self.listWinners, file, indent=4)

def updateKDR(self, users):
#update KDR JSON file
    for user in users["dead"]:
        if not user["id"] in self.listKdr:
            self.listKdr[user["id"]] = {"kills": user["kills"], "death": 1}
        else:
            self.listKdr[user["id"]]["kills"] += user["kills"]
            self.listKdr[user["id"]]["death"] += 1

    for user in users["alive"]:
        if not user["id"] in self.listKdr:
            self.listKdr[user["id"]] = {"kills": user["kills"], "death": 0}
        else:
            self.listKdr[user["id"]]["kills"] += user["kills"]

    with open(self.bot.BATTLEROYALEKDR_PATH, 'w') as file:
        json.dump(self.listKdr, file, indent=4)

def victoryEmbed(self, user):
#create final embed
    embed = discord.Embed(
        title = 'Winner',
        description=user["name"],
        color=self.bot.embed_color
    )
    embed.set_footer(text = "Kills: {}".format(user["kills"]))
    return embed

def setup(bot):
    bot.add_cog(BattleRoyale(bot))
