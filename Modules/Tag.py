#
# Tag Module For Discord Bot (Rule 314)
################################
import random

itRole   = 'It'     # decorative: Vars.It is what decides who is It
tagChans = ['game', 'off-topic']
lookBack = 200      # how many messages a TAG searches for its target


async def setup(bot):
    bot.Modules['Commands'].add_command(bot,
        name= 'tag-reassign',
        description= 'mod only -  make a different random player It',
        callback = passIt,
        checks = ['isMod'])

    if not bot.has('Vars', 'It'): bot.set(('Vars', 'It'), None)

async def reload_references(bot):
    # Queued, so it runs once Discord_Module's reload of the roles is committed
    bot.add_Task(syncRole)

async def syncRole(bot):
    if itRole not in bot.get_Ref('Roles'): await bot.Modules['Discord_Module'].create_role(bot, itRole)
    it = bot.get('Vars', 'It')
    for pid in bot.get_Ref('Players'):
        holds = bot.Modules['Discord_Module'].hasRole(bot, pid, itRole)
        if pid == it and not holds: await bot.Modules['Discord_Module'].addRole(bot, pid, itRole)
        if pid != it and holds:     await bot.Modules['Discord_Module'].removeRole(bot, pid, itRole)

def setIt(bot, pid):
    now, old = bot.get('Vars', 'Time'), bot.get('Vars', 'It')
    if old is not None: bot.set(('Players', old, 'Last It Time'), now)
    bot.set(('Vars', 'It'), pid)
    bot.schedule(
        name = 'Tag Timeout',
        method_name = 'passIt',
        module_name = 'Tag',
        Key = ('Vars','Time'), Mode='>=', Trigger_Value= now + 48*bot.hr, sequential_only=False
    )
    bot.add_Task(syncRole)

# Runs from !tag-reassign and when someone has been It for 48 hours
async def passIt(bot, *args):
    it = bot.get('Vars', 'It')
    players = [pid for pid in bot.get_Ref('Players') if pid != it and bot.Modules['Discord_Module'].isPlayer(bot, pid)]
    if len(players) == 0: return
    pid = random.choice(players)
    setIt(bot, pid)
    await bot.Modules['Discord_Module'].send(bot, 'actions', f"{bot.get('Players', pid, 'Name')} is now It.")

async def on_message(bot, message):
    pid = message['Author PID']
    if message['Content'].strip() != 'TAG' or message['Channel'] not in tagChans or pid != bot.get('Vars', 'It'): return
    if not bot.Modules['Discord_Module'].isPlayer(bot, pid): return

    day, now = bot.get('Vars', 'Day'), bot.get('Vars', 'Time')
    chan = bot.Modules['Discord_Module'].chan_from_Name(bot, message['Channel'])
    target = None
    if bot.get('Players', pid).get('Last Tag Day') != day:
        async for msg in chan.history(limit = lookBack, before = bot.discord.Object(id = message['MID'])):
            author = msg.author.id
            if author == pid or author not in bot.get_Ref('Players'): continue
            if not bot.Modules['Discord_Module'].isPlayer(bot, author): continue
            lastIt = bot.get('Players', author).get('Last It Time')
            if lastIt is None or now - lastIt >= 24*bot.hr:
                target = author
                break
    if target is None:
        return await bot.Modules['Discord_Module'].add_reaction(bot, message['Channel'], message['MID'], '❌')

    bot.set(('Players', pid, 'Last Tag Day'), day)
    setIt(bot, target)
    await bot.Modules['Discord_Module'].return_resp(bot, message, f"{bot.get('Players', pid, 'Name')} tagged {bot.get('Players', target, 'Name')}, who is now It.")
