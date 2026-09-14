#
# Admin Module For Discord Bot
################################
import sys, os,datetime, random, inspect, numpy, re
from shutil import copyfile
from typing import List
import discord

player = None


file_path  = os.path.realpath(os.path.abspath(inspect.getfile(inspect.currentframe())))
path  = os.path.realpath(os.path.abspath(os.path.join(file_path, os.pardir,)))+'/'

async def setup(bot): pass
async def update(bot): pass

async def on_typing(bot, event): pass

async def on_message(bot, message):

    if message['Content'] in [':heart:', '❤️']:
        await bot.Modules['Discord_Module'].return_resp(bot, message, '❤️', ephemeral = True)
    
    if '?' in message['Content'] and '!' == message['Content'][0]:
        options = [[
         "It is certain.",
         "It is decidedly so.",
         "Without a doubt.",
         "Yes definitely.",
         "You may rely on it.",
         "As I see it, yes.",
         "Most likely.",
         "Outlook good.",
         "Yes.",
         "Signs point to yes.",
        ],[
         "Reply hazy, try again.",
         "Ask again later.",
         "Better not tell you now.",
         "Cannot predict now.",
         "Concentrate and ask again.",
        ],[
         "Don't count on it.",
         "My reply is no.",
         "My sources say no.",
         "Outlook not so good.",
         "Very doubtful."]]
        await bot.Modules['Discord_Module'].return_resp(bot, message, random.choice(random.choice(options)))

async def update_display(bot):
    chanName = 'game-data'
    if not bot.has('Text Channels', chanName):
        return await bot.Modules['Discord_Module'].create_channel(bot, chanName, 'BUSINESS', 'Locked')
    else: await bot.Modules['Discord_Module'].confirmChanPerms(bot, chanName, 'Locked')

    displayMsgs = [ ]
    displayMsgs.append({
            'Content': f"Nomic Time: Week {bot.get('Vars', 'Week')} - Day {bot.get('Vars', 'Day')} ({bot.get('Vars', 'Weekday')})- Turn {bot.get('Vars', 'Turn')} \n at {bot.get('Vars', 'Time').strftime('%Y-%m-%d %H:%M:%S')}",
    })
    displayMsgs.append({
            'Content': f"Next Proposal Number {bot.get('Vars', 'Next Proposal Number')} ",
    })
    await bot.Modules['Discord_Module'].display(bot, chanName, displayMsgs)
 
    