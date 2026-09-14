import discord, numpy, sys, os, inspect, io, typing, asyncio
import random
file_path  = os.path.realpath(os.path.abspath(inspect.getfile(inspect.currentframe())))
path  = os.path.realpath(os.path.abspath(os.path.join(file_path, os.pardir,)))+'/'

JudgeOptInRole = "Judge Opt In"
checks = {}

async def setup(bot):
    global checks
    bot.init_database('Commands', id_key='Name', columns=[
            'Name', bot.OIK, 'Mod Only', 'Active Only', 'DM Only', 'Channel', 'Limit' 
        ])
        

    async def isMod(interaction: discord.Interaction):
        if type(interaction) is dict:            
            oktouse = bot.Modules['Discord_Module'].isModerator(bot, interaction['Author PID'])
        else:
            oktouse = bot.Modules['Discord_Module'].isModerator(bot, interaction.user.id)
        return oktouse
    async def isPlayer(interaction: discord.Interaction):
        if type(interaction) is dict:            
            oktouse = bot.Modules['Discord_Module'].isPlayer(bot, interaction['Author PID'])
        else:
            oktouse = bot.Modules['Discord_Module'].isPlayer(bot, interaction.user.id)
        return oktouse
    async def isDM(interaction: discord.Interaction):
        if type(interaction) is dict:            
            return interaction['Category'] == 'DM'
        else:
            return interaction.channel.type in [bot.discord.ChannelType.private, bot.discord.ChannelType.group]
    async def isActions(interaction: discord.Interaction):
        if type(interaction) is dict:            
            return interaction['Channel'] == 'actions'
        else:
            return interaction.channel.name == 'actions'
    async def isSpam(interaction: discord.Interaction):
        if type(interaction) is dict:            
            return ( await isDM(interaction) ) or 'spam' in interaction['Channel']
        else:
            return ( await isDM(interaction) ) or 'spam' in interaction.channel.name
    checks['isMod'] = isMod
    checks['isPlayer'] = isPlayer
    checks['isDM'] = isDM
    checks['isActions'] = isActions
    checks['isSpam'] = isSpam

async def on_message(bot, message):
    if message['Content'][0] == '!':
        cmdKey = message['Content'].split(' ')[0][1:]
        if cmdKey in bot.Commands.keys():
            for check in bot.Commands[cmdKey]['checks']:
                checkResult = await checks[check](message)
                if not checkResult: 
                    return await bot.Modules['Discord_Module'].add_reaction(bot, msgid = message['MID'], source_id = message['Channel'], emoji = '❌')
            args = [message,] + message['Content'].split(' ')[1:]

            await bot.Commands[cmdKey]['callback'](*args)

def command_list(bot):
    async def help(interaction: discord.Interaction):
        txt = "Your Available Commands:\n - Use !COMMAND or slash commands to activate them.\n"
        for cmd in command_list(bot):
            if 'isMod' in cmd['checks'] and not await checks['isMod'](interaction): continue
            txt += f"- {cmd['name']} : {cmd['description']}\n"

        await bot.Modules['Discord_Module'].return_resp(bot, interaction, txt, wrap=['```diff\n', '```'])
        # with open(path+'PlayerREADME.md', 'r') as helpFile:
        #     await bot.Modules['Discord_Module'].return_resp(bot, interaction, helpFile.read(), wrap=['```diff\n', '```'])
        
    async def data(interaction: discord.Integration, player:discord.Member):
        pid = player.id
        text  = f"Player : {bot.get('Users',pid, 'Name')}\n"
        text += f"Points : {bot.get('Users',pid, 'Points')}\n"
        text += f"Balls  : {bot.get('Users',pid, 'Balls')}\n"
        text += f"Balls left to Gain by BLAM! : {bot.get('Users',pid,'BLAM Balls Left To Gain')}\n"
        text += f"Souls:\n" + (" - ".join( [ str(bot.get('Users',p, 'Name')) for p in bot.where( 'Souls', lambda df: df['Owner-PID'] == pid) ]))
        await bot.Modules['Discord_Module'].return_resp(bot, interaction, text, ephemeral=True)

    async def whack(interaction: discord.Integration ):
        PID = interaction.user.id


        bot.inc('Users',PID,{'Post Gurlip Whack Counter':1})
        if bot.get('Users', PID, 'Post Gurlip Whack Counter') <= 3:
            gurlips = [b for b in bot.keys('Users') if bot.Modules['Discord_Module'].hasRole(bot, b, 'Gurlip')]
            to_degurlip = random.choice(gurlips)
            await bot.Modules['Discord_Module'].removeRole(bot, to_degurlip, 'Gurlip')
                
        if bot.get('Users', PID, 'Balls') > 1:
            bot.inc('Users', PID, {'Balls':-1, 'Points':1})
            await bot.Modules['Discord_Module'].return_resp(bot, interaction, "You have lost a ball and gained a point")
        else:
            await bot.Modules['Discord_Module'].return_resp(bot, interaction, "You dont have the balls")

    async def blam(interaction: discord.Integration):
        if type(interaction) is not dict: 
            return await bot.Modules['Discord_Module'].return_resp(bot, interaction, "This command cannot be used via slash due to discord limitations. Please use !blam instead", ephemeral=True)

        blopable = bot.where('Users', lambda df: df['IsBLOPed'] != True)
        blopable = [b for b in blopable if bot.Modules['Discord_Module'].isPlayer(bot, b)]
        bot.log('blob '+str([bot.get('Users',b,'Name') for b in blopable]))

        bloper = interaction['Author PID']

        if len(blopable) == 0: return await bot.Modules['Discord_Module'].return_resp(bot, interaction, "All players have been BLOPed")
        if bot.get('Users', bloper, 'Blops This Turn') >= 2: return await bot.Modules['Discord_Module'].return_resp(bot, interaction, "You can only BLOP 2x per turn max.")
        if bot.get('Users', bloper, 'BLAM Balls Left To Gain') == 0: return await bot.Modules['Discord_Module'].return_resp(bot, interaction, "You are at your Ball Blop Reward Limit. No Blamming for you.")
        toBlop = random.choice(blopable)

        isGurlip = bot.Modules['Discord_Module'].hasRole(bot, toBlop, 'Gurlip') or bot.Modules['Discord_Module'].hasRole(bot, bloper, 'Gurlip')

        randNums = [0,0]
        while randNums[0] == randNums[1]: randNums = numpy.random.randint(1, 31+1, 2)
        if randNums[0] > randNums[1]:
            winner = bloper
            loser  = toBlop
        else:
            winner = toBlop
            loser  = bloper
        bot.inc('Users', bloper, {'Blops This Turn':1})
        bot.set('Users',toBlop,{'IsBLOPed':True})
        text = f"BLOP!er: {bot.get('Users',bloper, 'Name')}-{randNums[0]}, BLOP!ee {bot.get('Users',toBlop, 'Name')}-{randNums[1]}"
        
        if isGurlip:
            if bot.get('Users', loser, 'BLAM Balls Left To Gain') >0:
                bot.inc('Users', loser, {'Balls': 1,
                                        'BLAM Balls Left To Gain': -1})
                text += f"\nBalls have been assigned to {bot.get('Users',loser, 'Name')}"

            bot.set('Users',winner,{'Post Gurlip Whack Counter':0})
            await bot.Modules['Discord_Module'].addRole(bot, winner, 'Gurlip')
            
            text += f"\nGurlips Role has been assigned to {bot.get('Users',winner, 'Name')}"

        await bot.Modules['Discord_Module'].return_resp(bot, interaction, text)



    async def roll(interaction: discord.Interaction, dice :str):
        diceInfo = dice.split('d')
        if len(diceInfo) == 2:
            randNum = numpy.random.randint(1, int(diceInfo[1])+1, int(diceInfo[0]))
            text = f"{dice} -> {sum(randNum)} : {str(randNum).replace('  ',' ').replace(' ',', ')}"
        else: text =  "Bad dice format. Please use something like 69d420 to roll 69 dice with 420 sides"
        await bot.Modules['Discord_Module'].return_resp(bot, interaction, text)
    async def ping(interaction: discord.Interaction,): 
        await bot.Modules['Discord_Module'].return_resp(bot, interaction, 'Pong')
    async def dance(interaction: discord.Interaction,): 
        await bot.Modules['Discord_Module'].return_resp(bot, interaction, "https://media.tenor.com/3SSi0qLshgkAAAAC/time-to-party-dance.gif")
    async def echo(interaction: discord.Interaction, text :str): 
        await bot.Modules['Discord_Module'].return_resp(bot, interaction, text) 

    async def clear(interaction: discord.Interaction):
        if type(interaction) is dict:
            if interaction['Category'] == 'DM': return await bot.Modules['Discord_Module'].return_resp(bot, interaction, 'Cannot do in DMs')
            messages = [m async for m in bot.Modules['Discord_Module'].chan_from_Name(bot, interaction['Channel']).history(limit=200)]
        else:
            messages = [m async for m in interaction.channel.history(limit=200)]
        for msg in messages: 
            try:await msg.delete()
            except: pass
        
        await bot.Modules['Discord_Module'].return_resp(bot, interaction, '200 Messages Removed By Mod')
    
    async def find(interaction: discord.Interaction, text: str):
        body = bot.Modules['Rules'].find(bot, text)
        await bot.Modules['Discord_Module'].return_resp(bot, interaction, body, ephemeral=True) 
    async def rule(interaction: discord.Interaction, number: int):
        body = bot.Modules['Rules'].rule_int(bot, number)
        print(body)
        await bot.Modules['Discord_Module'].return_resp(bot, interaction, body) 

    async def getDB(interaction: discord.Interaction, name: str):
        if name not in bot.Databases.keys():
            return await bot.Modules['Discord_Module'].return_resp(bot, interaction, f"Please choose a valid Db from the list" + '\n- '.join(['',]+list(bot.Databases.keys())),) 
        
        f= io.BytesIO( bot.Databases[name].to_csv().encode('utf-8') )
        return await bot.Modules['Discord_Module'].return_resp(bot, interaction, f"DB-{name}", files=[discord.File(f, filename=f"{name}.csv"),]) 
    
    async def popProposal(interaction:  discord.Interaction):
        await bot.Modules['Discord_Module'].return_resp(bot, interaction, f"Popping")
        await bot.Modules['Voting'].popProposalMain(bot)
    async def deckify(interaction:  discord.Interaction):
        await bot.Modules['Discord_Module'].return_resp(bot, interaction, f"Deckify")
        await bot.Modules['Voting'].PutToVote(bot)
    async def tally(interaction:  discord.Interaction):
        await bot.Modules['Discord_Module'].return_resp(bot, interaction, f"TallyVotes")
        await bot.Modules['Voting'].TallyVotes(bot)
    async def reloadRefs(interaction:  discord.Interaction):
        await bot.Modules['Discord_Module'].return_resp(bot, interaction, f"Refreshing All References")
        await bot.Modules['Nomitron'].RELOAD_REFS(bot)

    async def reset_Blop(interaction:  discord.Interaction):
        for pid in bot.keys('Users'):
            bot.set('Users',pid,{'IsBLOPed':False})
        
        await bot.Modules['Discord_Module'].return_resp(bot, interaction, f"Success")

    async def addTime(interaction:  discord.Interaction, db:str, row: str, col:str, hrs: float):
        bot.inc(db, row, {col: hrs * bot.hr})
        await bot.Modules['Discord_Module'].return_resp(bot, interaction, f"Success")

    async def set_db(interaction:  discord.Interaction, db:str, row: str, col:str, value: str):
        try: value = int(value)
        except: pass

        try: row = int(row)
        except: pass

        try: bot.set(db, row, {col: value})
        except Exception as e:
            return await bot.Modules['Discord_Module'].return_resp(bot, interaction, f"Failed to Set: {e}")

        await bot.Modules['Discord_Module'].return_resp(bot, interaction, f"Success")
    
    async def set_user_db(interaction:  discord.Interaction, player: discord.Member, col:str, value: str):
        try: value = int(value)
        except: pass

        try: row = int(row)
        except: pass

        try: bot.set('Users', player.id, {col: value})
        except Exception as e:
            return await bot.Modules['Discord_Module'].return_resp(bot, interaction, f"Failed to Set: {e}")

        await bot.Modules['Discord_Module'].return_resp(bot, interaction, f"Success")
    
    async def setPoints(interaction:  discord.Interaction, player:discord.Member, points: float):
        try: bot.set('Users', player.id, {'Points': points})
        except Exception as e:
            return await bot.Modules['Discord_Module'].return_resp(bot, interaction, f"Failed to Set: {e}")

        await bot.Modules['Discord_Module'].return_resp(bot, interaction, f"Success")

    async def declare_active(interaction:  discord.Interaction):
        if type(interaction) is dict:
            s = await bot.Modules['Activity'].attemptActivate(bot, interaction["Author PID"])
        else:
            s = await bot.Modules['Activity'].attemptActivate(bot, interaction.user.id)
        if s: 
            await bot.Modules['Discord_Module'].return_resp(bot, interaction, 'You are now Active', ephemeral=0)
        else:
            await bot.Modules['Discord_Module'].return_resp(bot, interaction, 'You cannot be made active at this time. You have a forced inactive role', ephemeral=True)
    
    async def sudo(interaction:  discord.Interaction):
        if type(interaction) is dict:
            if interaction["Author PID"] not in [471529178462814209, ]: return await bot.Modules['Discord_Module'].return_resp(bot, interaction, 'Bad!!! You cant use this!!', ephemeral=1)
            if bot.Modules['Discord_Module'].hasRole(bot, interaction["Author PID"], 'Moderator'):
                await bot.Modules['Discord_Module'].removeRole(bot, interaction["Author PID"], 'Moderator')
            else:
                await bot.Modules['Discord_Module'].addRole(bot, interaction["Author PID"], 'Moderator')
        else:
            if interaction.user.id not in [471529178462814209, ]: return await bot.Modules['Discord_Module'].return_resp(bot, interaction, 'Bad!!! You cant use this!!', ephemeral=1)
            if bot.Modules['Discord_Module'].hasRole(bot,  interaction.user.id, 'Moderator'):
                await bot.Modules['Discord_Module'].removeRole(bot, interaction.user.id, 'Moderator')
            else:
                await bot.Modules['Discord_Module'].addRole(bot, interaction.user.id, 'Moderator')
        await bot.Modules['Discord_Module'].return_resp(bot, interaction, 'Done', ephemeral=1)
    
    async def declare_inactive(interaction:  discord.Interaction):
        if type(interaction) is dict:
            s = await bot.Modules['Activity'].makeInactive(bot, interaction["Author PID"])
        else:
            s = await bot.Modules['Activity'].makeInactive(bot, interaction.user.id)
        await bot.Modules['Discord_Module'].return_resp(bot, interaction, 'You are now Inactive', ephemeral=0)
    
    async def optInJudge(interaction:  discord.Interaction):
        if type(interaction) is dict:
            await bot.Modules['Discord_Module'].addRole(bot, interaction["Author PID"], JudgeOptInRole)
        else:
            await bot.Modules['Discord_Module'].addRole(bot, interaction.user.id, JudgeOptInRole)
        await bot.Modules['Discord_Module'].return_resp(bot, interaction, "You have opted in as judge", ephemeral=False)
    
    async def optOutJudge(interaction:  discord.Interaction):
        if type(interaction) is dict:
            await bot.Modules['Discord_Module'].removeRole(bot, interaction["Author PID"], JudgeOptInRole)
        else:
            await bot.Modules['Discord_Module'].removeRole(bot, interaction.user.id, JudgeOptInRole)
        await bot.Modules['Discord_Module'].return_resp(bot, interaction, 'You will no longer be considered for judge', ephemeral=0)
    
    async def playerWithRoles(interaction:  discord.Interaction, role: discord.Role):
        if type(interaction) is dict:
            roleName = role
        else:
            roleName = role.name
        pids = bot.Modules['Discord_Module'].usersWithRole(bot, roleName)
        names = [bot.get('Users', p,'Name') for p in pids]
        
        await bot.Modules['Discord_Module'].return_resp(bot, interaction, 'Players:\n'+('\n'.join(names)), ephemeral=False)
    
    async def create_endorsement(interaction:  discord.Interaction, player: discord.Member, queue_prop_msgid: str ):
        propID = bot.where('Queue-Proposals', lambda df: df['Endorse-MID'] == int(queue_prop_msgid))
        if len(propID) ==1:
            propID = propID[0]
            bot.set('User-Proposal-Endorsement', f"{player.id}-{propID}", values={
                    'PID':player.id,'Proposal-ID':propID
                })
            await bot.Modules['Discord_Module'].return_resp(bot, interaction, 'Done', ephemeral=1)
        else: 
            await bot.Modules['Discord_Module'].return_resp(bot, interaction, f'Failed {propID} {player.id}', ephemeral=1)

    return [
    dict( 
        name= 'help',
        description= 'get Help for Commands',
        callback = help,
        checks = ['isSpam', 'isPlayer']),
    dict( 
        name= 'blam',
        description= 'blam a random player',
        callback = blam,
        checks = ['isActions', 'isPlayer']),
    dict( 
        name= 'whack',
        description= 'whack and loose a ball',
        callback = whack,
        checks = ['isActions', 'isPlayer']),
    dict( 
        name= 'player-data',
        description= "get a player's data",
        callback = data,
        checks = ['isSpam', 'isPlayer']),
    dict( 
        name= 'find',
        description= 'search all the rules for some text.',
        callback = find,
        checks = ['isSpam']), 
    dict( 
        name= 'rule',
        description= 'get rule by number',
        callback = rule,
        checks = ['isSpam']),
    dict( 
        name= 'ping',
        description= 'mod only -  ping Nomitron for a response',
        callback = ping,
        checks = ['isMod']),
    dict( 
        name= 'dance',
        description= 'make nomitron dance.',
        callback = dance,
        checks = ['isPlayer']),
    dict( 
        name= 'roll',
        description= 'roll dice.',
        callback = roll,
        checks = []),
    dict( 
        name= 'echo',
        description= 'mod only -  Nomitron says what you tell it to.',
        callback = echo,
        checks = ['isMod']),
    # dict( 
    #     name= 'clear',
    #     description= 'mod only -  Clear the last 200 msgs',
    #     callback = clear,
    #     checks = ['isMod']),
    dict( 
        name= 'get-table',
        description= 'mod only - get table',
        callback = getDB,
        checks = ['isMod']), 
    dict( 
        name= 'pop-prop',
        description= 'mod only -  pop proposals like start of turn',
        callback = popProposal,
        checks = ['isMod']),
    dict( 
        name= 'reset-blop',
        description= 'mod only -  reset blop like start of turn',
        callback = reset_Blop,
        checks = ['isMod']),
    dict( 
        name= 'open-voting',
        description= 'mod only -  move things from deck to voting',
        callback = deckify,
        checks = ['isMod']),
    dict( 
        name= 'tally',
        description= 'mod only -  tally ALL votes',
        callback = tally,
        checks = ['isMod']),
    dict( 
        name= 'refresh-references',
        description= 'mod only -  refresh the server data rules etc',
        callback = reloadRefs,
        checks = ['isMod']),
    dict( 
        name= 'set',
        description= 'mod only -  set a value in DB',
        callback = set_db,
        checks = ['isMod']), 
    dict( 
        name= 'set-player',
        description= 'mod only -  set a user value in DB',
        callback = set_user_db,
        checks = ['isMod']), 
    dict( 
        name= 'set_points',
        description= 'mod only -  sets a players points ',
        callback = setPoints,
        checks = ['isMod']),  
    dict( 
        name= 'inc-hr-time',
        description= 'mod only -  inc a value in DB',
        callback = addTime,
        checks = ['isMod']), 
    dict( 
        name= 'declare-active',
        description= 'make yourself Active if possible',
        callback = declare_active,
        checks = ['isPlayer', 'isActions']),
    dict( 
        name= 'declare-inactive',
        description= 'make yourself Inctive if possible',
        callback = declare_inactive,
        checks = ['isPlayer', 'isActions']),
    dict( 
        name= 'opt-in-judge',
        description= 'opt into being a judge',
        callback = optInJudge,
        checks = ['isPlayer', 'isActions']),
    dict( 
        name= 'opt-out-judge',
        description= 'opt out of being a judge',
        callback = optOutJudge,
        checks = ['isPlayer','isActions']),
    dict( 
        name= 'player-role-list',
        description= 'mod only -  list all players with a role',
        callback = playerWithRoles,
        checks = ['isMod']),
    dict( 
        name= 'sudo',
        description= 'mod only -  toggle mod role',
        callback = sudo,
        checks = []),
    dict( 
        name= 'create-endorsement',
        description= 'mod only -  add an endorsement for a player',
        callback = create_endorsement,
        checks = ['isMod']),
    ]