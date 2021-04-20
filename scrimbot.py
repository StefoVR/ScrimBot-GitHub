import discord
from discord.ext import commands, tasks
import datetime as dt
import pytz

with open("key.txt", "r") as keyF:
    key = keyF.read()

f = open("times.txt", "r")
timeList = f.read().splitlines()

scrimTimes = []
scrimChannels = []
scrimMessages = []
pastScrimMessages = []

client = commands.Bot(command_prefix="scrimbot ")


@client.event
async def on_ready():
    print("Bot up.")
    scrimOrganiser.start()


@client.command()
async def add(ctx, scrimTime):
    if "scrim" not in ctx.message.channel.name:
        return

    if scrimTime in timeList:
        # Send the message and reactions.
        message = await ctx.send("New scrim at " + scrimTime + ".")
        await message.add_reaction("👍")
        await message.add_reaction("🇷")
        await message.add_reaction("⏭️")

        # Pin the message.
        await message.pin()

        scrimTimes.append(scrimTime)
        scrimChannels.append(ctx.channel)
        scrimMessages.append(message)

        # Delete original message invoking the command (na_da request)
        await ctx.message.delete()


@client.event
async def on_reaction_add(reaction, user):
    message = reaction.message

    if user == client.user:
        return

    # For some reason discord doesn't detect the initial message reactions, so it has to be reset here
    if message in scrimMessages:
        index = scrimMessages.index(message)
        scrimMessages[index] = message
        print("Reacted")

    # If reacting to a scrim message
    if message in scrimMessages or message in pastScrimMessages:
        # If the message has 9 "👍" reactions, remove this one. This is so scrims cannot have 9 active
        for existingReaction in message.reactions:
            users = await existingReaction.users().flatten()
            if reaction.emoji == "👍" and existingReaction.emoji == "👍" and len(users) >= 10:
                await reaction.remove(user)

            if reaction.emoji == "⏭️" and existingReaction.emoji == "🇷":
                await reaction.remove(user)
                if users[1]:
                    await message.channel.send(users[1].mention + " you're needed for a scrim.")
                    await existingReaction.remove(users[1])
                else:
                    await message.channel.send("No reserves!")

            if reaction.emoji == "🏳️" and existingReaction.emoji == "🏳️" and len(users) >= 2:
                await message.unpin()
                await message.channel.send("Scrim finished.")
                if message in pastScrimMessages:
                    pastScrimMessages.remove(message)


@tasks.loop(seconds=3)
async def scrimOrganiser():
    for x in scrimTimes:
        index = scrimTimes.index(x)

        scrimTime = x.split(":")
        hour = scrimTime[0]
        minute = scrimTime[1]

        # Get real time and format it correctly.
        local_tz = pytz.timezone("Europe/London")

        realHour = str(dt.datetime.now(local_tz).hour)
        realMinute = str(dt.datetime.now(local_tz).minute)
        if len(realMinute) == 1:
            realMinute = "0" + realMinute

        print(realHour, realMinute)

        # Check the time, if it is scrim time send a message and ping the users.
        if realHour == hour and realMinute == minute:
            channel = scrimChannels[index]

            reactions = scrimMessages[index].reactions

            users = ""
            for reaction in reactions:
                if reaction.emoji != "👍":
                    pass
                else:
                    users = await reaction.users().flatten()

            userMentions = " "
            for user in users:
                if user == client.user:
                    pass
                else:
                    userMentions += user.mention + " "

            await scrimMessages[index].reply("Scrim now!" + str(userMentions))

            # Add the flag.
            await scrimMessages[index].add_reaction("🏳️")

            # Remove this scrim.
            scrimChannels.pop(index)

            pastScrimMessages.append(scrimMessages[index])
            scrimMessages.pop(index)

            scrimTimes.pop(index)


client.run(key)
