#
# Cards Module For Discord Bot (Rules 302 and 309)
################################
import random, math

ranks  = ['Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Page', 'Knight', 'Queen', 'King', 'Ace']
suits  = ['Swords', 'Wands', 'Coins', 'Cups']
majors = ['The Fool', 'The Magician', 'The High Priestess', 'The Empress', 'The Emperor', 'The Hierophant', 'The Lovers',
          'The Chariot', 'Strength', 'The Hermit', 'Wheel of Fortune', 'Justice', 'The Hanged Man', 'Death', 'Temperance',
          'The Devil', 'The Tower', 'The Star', 'The Moon', 'The Sun', 'Judgement', 'The World']

# Count is how many can be out of the MDoMA. Weight is a finite card's weight while copies are left, and an infinite
# card's with none out; it halves with each copy out (rule 302)
cardDefs = {f'{rank} of {suit}': {'Count': math.inf, 'Weight': 1} for suit in suits for rank in ranks} \
         | {name: {'Count': 1, 'Weight': 0} for name in majors}

crystalCost = 2
drawModes   = {
    'crystals': f'once per turn, for {crystalCost} Crystals (rule 302)',
    'spread':   'once, in the turn a mod grants it (rule 302, Opening Spread)',
}


async def setup(bot):
    add_command = bot.Modules['Commands'].add_command

    add_command(bot,
        name= 'draw',
        description= f"draw a card from the MDoMA: !draw <{' | '.join(drawModes)}>. !draw alone lists the modes",
        callback = draw,
        checks = ['isPlayer', 'isActions'])
    add_command(bot,
        name= 'hand',
        description= "DMs you your cards. Mods can see a player's: !hand <@player>",
        callback = hand,
        checks = ['isPlayer'])

    add_command(bot,
        name= 'draw-force',
        description= 'mod only -  draw a card for a player, with no cost or limit: !draw-force <@player>',
        callback = drawForce,
        checks = ['isMod'])
    add_command(bot,
        name= 'draw-set-eligibility',
        description= f"mod only -  allow or stop a player's draw this turn: !draw-set-eligibility <@player> <{' | '.join(drawModes)}> <true | false>",
        callback = setEligibility,
        checks = ['isMod'])
    add_command(bot,
        name= 'set-count',
        description= 'mod only -  set how many of a card are out of the MDoMA: !set-count <amount> <card>',
        callback = setCount,
        checks = ['isMod'])

    bot.update_nested_dict(('Cards',), structure = {})
    bot.update_nested_dict(('Card-Counts',), structure = {name: 0 for name in cardDefs})
    if not bot.has('Vars', 'Next Card ID'): bot.set(('Vars', 'Next Card ID'), 1)

def canDraw(bot, pid, mode):
    """Whether a player can draw with a mode now, and why not."""
    turn = bot.get('Vars', 'Turn')
    player = bot.get('Players', pid)
    draws = player.get('Draws', {})
    if mode == 'crystals':
        crystals = player.get('Intrinsic', {}).get('Crystals', 0)
        if draws.get('Crystals Used Turn') == turn: return False, "You've already drawn with Crystals this turn."
        if crystals < crystalCost:                  return False, f"That costs {crystalCost} Crystals, and you have {crystals}."
        return True, None
    if mode == 'spread':
        if draws.get('Spread Granted Turn') != turn: return False, "You haven't been granted an Opening Spread draw this turn."
        return True, None
    return False, f"There is no {mode} draw."

def drawCard(bot, pid, mode):
    """Draw one card from the MDoMA into a player's private hand. Returns its ID and name."""
    counts, cid = bot.get('Card-Counts'), bot.get('Vars', 'Next Card ID')
    weights = []
    for name, card in cardDefs.items():
        if counts[name] >= card['Count']: weights.append(0)
        elif card['Count'] == math.inf:   weights.append(card['Weight'] * 2 ** -counts[name])
        else:                             weights.append(card['Weight'])
    name = random.choices(list(cardDefs), weights=weights)[0]
    bot.set(('Cards', cid), {
        'Name': name, 'Owner': pid, 'Zone': 'Private', 'Edition': None, 'Stickers': [],
        'Drawn Turn': bot.get('Vars', 'Turn'), 'Drawn Mode': mode,
    })
    bot.stage(('Card-Counts', name), 'increment', 1)
    bot.stage(('Vars', 'Next Card ID'), 'increment', 1)
    return cid, name



# Player Commands
async def draw(bot, payload, *args):
    pid = payload['Author PID']
    words = payload['Content'].split()
    mode = words[1].lower() if len(words) > 1 else ''
    if mode not in drawModes:
        text = "Use !draw <mode>. The modes are:\n"
        for m, how in drawModes.items():
            ok, why = canDraw(bot, pid, m)
            text += f"- {m}: {how}. {'You can use it now.' if ok else why}\n"
        return await bot.Modules['Discord_Module'].return_resp(bot, payload, text)
    ok, why = canDraw(bot, pid, mode)
    if not ok: return await bot.Modules['Discord_Module'].return_resp(bot, payload, why)

    if mode == 'crystals':
        bot.stage(('Players', pid, 'Intrinsic', 'Crystals'), 'decrement', crystalCost)
        bot.set(('Players', pid, 'Draws', 'Crystals Used Turn'), bot.get('Vars', 'Turn'))
    if mode == 'spread': bot.set(('Players', pid, 'Draws', 'Spread Granted Turn'), None)
    cid, name = drawCard(bot, pid, mode)
    await bot.Modules['Discord_Module'].return_resp(bot, payload, f"{bot.get('Players', pid, 'Name')} drew a card ({mode}).")
    await bot.Modules['Discord_Module'].send(bot, pid, f"You drew #{cid}: {name}.")

async def hand(bot, payload, *args):
    author = payload['Author PID']
    words = payload['Content'].split()
    pid = author
    if len(words) > 1:
        if not bot.Modules['Discord_Module'].isModerator(bot, author):
            return await bot.Modules['Discord_Module'].return_resp(bot, payload, "Only mods can see another player's hand.")
        pid = bot.Modules['ItemsAndTeams'].pidFrom(bot, words[1])
        if pid is None: return await bot.Modules['Discord_Module'].return_resp(bot, payload, "Use !hand, or !hand <@player> as a mod.")

    held = {cid: card for cid, card in bot.get('Cards').items() if card['Owner'] == pid}
    text = f"{bot.get('Players', pid, 'Name')}'s hand:\n"
    text += '\n'.join(f"- #{cid}: {card['Name']} ({card['Zone'].lower()})" for cid, card in held.items()) or 'No cards.'
    await bot.Modules['Discord_Module'].send(bot, author, text)



# Mod Commands
async def drawForce(bot, payload, *args):
    words = payload['Content'].split()
    pid = bot.Modules['ItemsAndTeams'].pidFrom(bot, words[1]) if len(words) > 1 else None
    if pid is None:
        return await bot.Modules['Discord_Module'].return_resp(bot, payload, "Use !draw-force <@player>.")
    who = bot.get('Players', pid, 'Name')
    if not bot.Modules['Discord_Module'].isPlayer(bot, pid):
        return await bot.Modules['Discord_Module'].return_resp(bot, payload, f"{who} is not a player.")

    cid, name = drawCard(bot, pid, 'force')
    await bot.Modules['Discord_Module'].send(bot, 'actions', f"{who} drew a card (drawn by a mod).")
    await bot.Modules['Discord_Module'].send(bot, pid, f"You drew #{cid}: {name}.")

async def setEligibility(bot, payload, *args):
    words = payload['Content'].split()
    pid = bot.Modules['ItemsAndTeams'].pidFrom(bot, words[1]) if len(words) > 1 else None
    mode, state = (words[2].lower(), words[3].lower()) if len(words) > 3 else ('', '')
    if pid is None or mode not in drawModes or state not in ['true', 'false']:
        return await bot.Modules['Discord_Module'].return_resp(bot, payload, f"Use !draw-set-eligibility <@player> <{' | '.join(drawModes)}> <true | false>.")
    who = bot.get('Players', pid, 'Name')
    if not bot.Modules['Discord_Module'].isPlayer(bot, pid):
        return await bot.Modules['Discord_Module'].return_resp(bot, payload, f"{who} is not a player.")

    turn = bot.get('Vars', 'Turn')
    if mode == 'crystals': bot.set(('Players', pid, 'Draws', 'Crystals Used Turn'), None if state == 'true' else turn)
    if mode == 'spread':   bot.set(('Players', pid, 'Draws', 'Spread Granted Turn'), turn if state == 'true' else None)
    await bot.Modules['Discord_Module'].return_resp(bot, payload, f"{who} {'can' if state == 'true' else 'can no longer'} draw with {mode} this turn.")

async def setCount(bot, payload, *args):
    words = payload['Content'].split(' ', 2)
    name = {name.lower(): name for name in cardDefs}.get(words[2].strip().lower()) if len(words) > 2 else None
    if name is None or not words[1].isdigit():
        return await bot.Modules['Discord_Module'].return_resp(bot, payload, "Use !set-count <amount> <card>, with a whole number of at least 0 and the card's full name, e.g. !set-count 2 Three of Cups.")
    amount, limit = int(words[1]), cardDefs[name]['Count']
    if amount > limit:
        return await bot.Modules['Discord_Module'].return_resp(bot, payload, f"{name} is finite: at most {limit} can be out of the MDoMA.")

    old = bot.get('Card-Counts', name)
    bot.set(('Card-Counts', name), amount)
    await bot.Modules['Discord_Module'].return_resp(bot, payload, f"{name}: {amount} out of the MDoMA (was {old}).")
