
inactiveRule = [ ]

InactiveRole  = "Inactive"
OverdueRole = "Overdue"
ModBlockRole = 'Mod-Blocked'
inactive_forcing_roles = [OverdueRole, ModBlockRole]

async def setup(bot): pass

async def makeActive(bot, pid):
    if bot.Modules['Discord_Module'].isActive(bot, pid): return
    else: await bot.Modules['Discord_Module'].removeRole(bot, pid, InactiveRole)

async def makeInactive(bot,pid):
    if not bot.Modules['Discord_Module'].isActive(bot, pid): return
    else: await bot.Modules['Discord_Module'].addRole(bot, pid, InactiveRole)


async def update(bot,):
    roles = bot.keys('Roles')
    for role in [InactiveRole, OverdueRole, ModBlockRole]:
        if role not in roles: 
            bot.add_Task(bot.Modules['Discord_Module'].create_role, {'roleName': role})

    for pid in bot.keys('Players'):
        if not bot.Modules['Discord_Module'].isPlayer(bot, pid): continue

        # Active Checks
        if bot.Modules['Discord_Module'].isActive(bot, pid):
            if bot.get('Players',pid).get('Last Active Time') is not  None:
                bot.set(('Players', pid, 'Last Active Time'), kwargs=None)
        # Inactive Checks
        else:
            if bot.get('Players',pid).get('Last Active Time') is  None:
                bot.set(('Players', pid, 'Last Active Time'), kwargs=bot.get('Vars','Time'))
        
            for role in inactive_forcing_roles:
                if bot.Modules['Discord_Module'].hasRole(bot, pid, role): await makeInactive(bot, pid)


async def attemptActivate(bot,pid):
    if not bot.Modules['Discord_Module'].isActive(bot, pid):
        for role in inactive_forcing_roles:
            if bot.Modules['Discord_Module'].hasRole(bot, pid, role): return False
        await makeActive(bot, pid)
    return True
