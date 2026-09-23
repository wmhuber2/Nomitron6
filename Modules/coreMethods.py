#
# Admin Module For Discord Bot
################################


async def update_display(bot):
    chanName = 'game-data'
    if not bot.has('Text Channels', chanName):
        return await bot.Modules['Discord_Module'].create_channel(bot, chanName, 'BUSINESS', 'Locked')
    
    displayMsgs = [ ]
    displayMsgs.append({
            'Content': f"Nomic Time: Week {bot.get('Vars', 'Week')} - Day {bot.get('Vars', 'Day')} ({bot.get('Vars', 'Weekday')})- Turn {bot.get('Vars', 'Turn')} \n at {bot.get('Vars', 'Time').strftime('%Y-%m-%d %H:%M:%S')}",
    })
    displayMsgs.append({
            'Content': f"Next Proposal Number {bot.get('Vars', 'Next Proposal Number')} ",
    })
    await bot.Modules['Discord_Module'].display(bot, chanName, displayMsgs)
 
    