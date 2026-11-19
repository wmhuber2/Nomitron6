#
# Guild Module For Discord Bot (Rule 317)
################################

guildChan    = 'actions'
slogan       = 'pass me da moolah'
disbursement = 23
guildCoin    = 'Guild-Coins'


async def on_message(bot, message):
    pid = message['Author PID']
    if message['Channel'] != guildChan or slogan not in message['Content'].lower(): return
    if not bot.Modules['Discord_Module'].isPlayer(bot, pid): return

    week = bot.get('Vars', 'Week')
    if bot.get('Players', pid).get('Guild Week') != week: bot.set(('Players', pid, 'Guild Week'), week)
    await bot.Modules['Discord_Module'].add_reaction(bot, guildChan, message['MID'], '✅')


# Called from Schedules.onWeekStart: pays whoever said the slogan last week
async def onWeekStart(bot):
    week = bot.get('Vars', 'Week')
    paid = []
    for pid in bot.get_Ref('Players'):
        player = bot.get('Players', pid)
        if player.get('Guild Week') != week - 1 or not bot.Modules['Discord_Module'].isPlayer(bot, pid): continue
        bot.stage(('Players', pid, 'Currency', guildCoin), 'increment', disbursement)
        paid.append(player['Name'])
    if len(paid) > 0:
        await bot.Modules['Discord_Module'].send(bot, guildChan, f"The guild paid {disbursement} {guildCoin} to: {', '.join(paid)}")
