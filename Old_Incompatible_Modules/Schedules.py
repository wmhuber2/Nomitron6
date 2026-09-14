#
#  Nomitron 4 Safe
#

import datetime
async def setup(bot):
    if 'End Of Day' not in bot.keys('Schedules'): 
        bot.schedule(
            name = 'End Of Day',
            method_name = 'onDayEnd',
            module_name = 'Schedules',
            DB = 'Vars', DB_ID='Time',DB_Col='Value',Mode='greater', Trigger_Value= bot.Modules['Nomitron'].startDate, sequential_only=False
        )
    if 'End Of Week' not in bot.keys('Schedules'): 
        bot.schedule(
            name = 'End Of Week',
            method_name = 'onWeekEnd',
            module_name = 'Schedules',
            DB = 'Vars', DB_ID='Time',DB_Col='Value',Mode='greater', Trigger_Value= bot.Modules['Nomitron'].startDate, sequential_only=False
        )  
    if 'End Of Week' not in bot.keys('Schedules'): 
        bot.schedule(
            name = f'End of Turn 0',
            method_name = 'onTurnEnd',
            module_name = 'Schedules',
            DB = 'Vars', DB_ID='Time',DB_Col='Value',Mode='greater', Trigger_Value= bot.Modules['Nomitron'].startDate, sequential_only=False
        ) 
    if 'Start Of Day' not in bot.keys('Schedules'): 
        bot.schedule(
            name = 'Start Of Day',
            method_name = 'onDayStart',
            module_name = 'Schedules',
            DB = 'Vars', DB_ID='Day',DB_Col='Value',Mode='equal', Trigger_Value= bot.get('Vars','Day') + 1, sequential_only=False
        ) 
    if 'Start Of Turn' not in bot.keys('Schedules'): 
        bot.schedule(
            name = 'Start Of Turn',
            method_name = 'onTurnStart',
            module_name = 'Schedules',
            DB = 'Vars', DB_ID='Turn',DB_Col='Value',Mode='equal', Trigger_Value= bot.get('Vars','Turn') + 1, sequential_only=False
        )
    if 'Start Of Week' not in bot.keys('Schedules'): 
        bot.schedule(
            name = 'Start Of Week',
            method_name = 'onWeekStart',
            module_name = 'Schedules',
            DB = 'Vars', DB_ID='Week',DB_Col='Value',Mode='equal', Trigger_Value= bot.get('Vars','Week') + 1, sequential_only=False
        ) 

    print('   Schedules Created:')

async def onDayEnd(bot):
    bot.log(f"End Of Day {bot.get('Vars', 'Day')}") 
    await bot.Modules['Discord_Module'].send(bot, "actions", f"-----------END OF DAY---------")
    

    day = bot.get('Vars', 'Day') + 1
    isEndOfTurn = ((day-1)*bot.day + bot.Modules['Nomitron'].startDate).weekday() in [0,3,5]
    bot.set('Vars', 'Day', day )
    bot.set('Vars', 'Weekday', ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][((day-1)*bot.day + bot.Modules['Nomitron'].startDate).weekday()])
    bot.schedule(
        name = 'End Of Day',
        method_name = 'onDayEnd',
        module_name = 'Schedules',
        DB = 'Vars', DB_ID='Time',DB_Col='Value',Mode='greater', Trigger_Value= bot.Modules['Nomitron'].startDate + (day * bot.day), sequential_only=False
    )
    if isEndOfTurn:
        await bot.wrap( onTurnEnd, {'bot':bot} )

async def onTurnEnd(bot):
    bot.log(f"End Of Turn {bot.get('Vars', 'Turn')}")

    await bot.Modules['Voting'].TallyVotes(bot)
    for pid in bot.keys('Users'): bot.set('Users', pid, {'Blops This Turn':0})

    gurlips = [bot.Modules['Discord_Module'].hasRole(bot, b, 'Gurlip') for b in bot.keys('Users') ]
    if False not in gurlips:
        for pid in bot.keys('Users'): 
            await bot.Modules['Discord_Module'].removeRole(bot, pid, 'Gurlip')

    bot.set('Vars', 'Turn', values={
        'Value': bot.get('Vars', 'Turn') + 1
        })
  
async def onWeekEnd(bot):
    bot.log(f"End Of Week {bot.get('Vars', 'Week')}")
    week = bot.get('Vars', 'Week') + 1
    bot.set('Vars', 'Week', week )
    weekstart = bot.Modules['Nomitron'].startDate - bot.Modules['Nomitron'].startDate.weekday() * bot.day
    
    bot.schedule(
        name = 'End Of Week',
        method_name = 'onWeekEnd',
        module_name = 'Schedules',
        DB = 'Vars', DB_ID='Time',DB_Col='Value',Mode='greater', Trigger_Value= weekstart + (week * 7 * bot.day), sequential_only=False
    )  


async def onDayStart(bot):
    bot.log(f"START OF DAY {bot.get('Vars', 'Day')} ")

    await bot.Modules['Discord_Module'].send(bot, "actions", f"Start Of Day {bot.get('Vars', 'Day')} {bot.get('Vars', 'Weekday')} : <t:{int(bot.get('Vars', 'Time').timestamp())}:f>")
    
    bot.schedule(
        name = 'Start Of Day',
        method_name = 'onDayStart',
        module_name = 'Schedules',
        DB = 'Vars', DB_ID='Day',DB_Col='Value',Mode='equal', Trigger_Value= bot.get('Vars','Day') + 1, sequential_only=False
    )

async def onTurnStart(bot):
    bot.log(f"START OF Turn {bot.get('Vars', 'Turn')} {bot.get('Vars', 'Weekday')}")

    await bot.Modules['Discord_Module'].send(bot, "actions", f"Start Of Turn {bot.get('Vars', 'Turn')}")
    bot.schedule(
        name = 'Start Of Turn',
        method_name = 'onTurnStart',
        module_name = 'Schedules',
        DB = 'Vars', DB_ID='Turn',DB_Col='Value',Mode='equal', Trigger_Value= bot.get('Vars','Turn') + 1, sequential_only=False
    )
    
    turnDurration =3 if ((bot.get('Vars', 'Day')-1)*bot.day + bot.Modules['Nomitron'].startDate).weekday() == 0 else 2
    turnEndTime = (bot.get('Vars', 'Day') + turnDurration - 1) * bot.day + bot.Modules['Nomitron'].startDate

    for pid in bot.keys('Users'):
        bot.set('Users',pid,{'IsBLOPed':False})

    bot.schedule(
        name = f'On Deck',
        method_name = 'popProposalMain',
        module_name = 'Voting',
        DB = 'Vars', DB_ID='Time',DB_Col='Value',Mode='greater', Trigger_Value= turnEndTime - 2*bot.day, sequential_only=False
    ) 

    bot.schedule(
        name = f'Vote Starts',
        method_name = 'PutToVote',
        module_name = 'Voting',
        DB = 'Vars', DB_ID='Time',DB_Col='Value',Mode='greater', Trigger_Value= turnEndTime - 1*bot.day, sequential_only=False
    ) 
    await bot.wrap( bot.Modules['Voting'].popProposalJudge, {'bot':bot} )

async def onWeekStart(bot):
    bot.log(f"START Of Week {bot.get('Vars', 'Week')}")
    await bot.Modules['Discord_Module'].send(bot, "actions", f"Start Of Week {bot.get('Vars', 'Week')}")
    week = bot.get('Vars', 'Week')
    
    bot.schedule(
        name = 'Start Of Week',
        method_name = 'onWeekStart',
        module_name = 'Schedules',
        DB = 'Vars', DB_ID='Week',DB_Col='Value',Mode='equal', Trigger_Value= bot.get('Vars','Week') + 1, sequential_only=False
    ) 

