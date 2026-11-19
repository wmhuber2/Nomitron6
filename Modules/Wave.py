#
# Wave Module For Discord Bot (Rule 322)
################################
import random

smileyCoin = 'Smiley-Coins'
kissChance = 0.01
waveImage  = 'https://i.imgur.com/gbr13dg.png'
kissImage  = 'https://i.imgur.com/x3jJRwW.png'


async def setup(bot):
    bot.Modules['Commands'].add_command(bot,
        name= 'wave',
        description= f'spend 1 {smileyCoin} to wave at Nomitron, once per day',
        callback = wave,
        checks = ['isPlayer', 'isActions'])

async def wave(bot, payload, *args):
    pid = payload['Author PID']
    player, day = bot.get('Players', pid), bot.get('Vars', 'Day')
    coins = player.get('Currency', {}).get(smileyCoin, 0)
    if player.get('Last Wave Day') == day:
        return await bot.Modules['Discord_Module'].return_resp(bot, payload, "You've already waved today.")
    if coins < 1:
        return await bot.Modules['Discord_Module'].return_resp(bot, payload, f"Waving costs 1 {smileyCoin}, and you have {coins}.")

    bot.stage(('Players', pid, 'Currency', smileyCoin), 'decrement', 1)
    bot.set(('Players', pid, 'Last Wave Day'), day)
    if random.random() < kissChance: text = f"{kissImage}"
    else:                            text = f"{waveImage}"
    await bot.Modules['Discord_Module'].return_resp(bot, payload, text)
