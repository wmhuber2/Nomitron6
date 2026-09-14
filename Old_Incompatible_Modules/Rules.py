"""
Main Run Function On Messages
"""
import pickle, sys, urllib, discord, io, markdownify # type: ignore

def find(bot, text):
    query = text.lower()
    ret_msg = ""

    if query[ 0] == '"': query = query[1:  ]
    if query[-1] == '"': query = query[ :-1]
    print ('Searching for', query)
    if len(query) <= 2: return "Must Search Words Longer Then 2 Letters"
    else:
        found = False
        rulecount = 5
        roundmsg = ""
        for rule in bot.keys('Rules'):
            body = bot.get('Rules',rule, 'Text')
            low  = body.lower()

            if query in low and (rulecount <= 0 or len(ret_msg) > 1900):
                roundmsg += str(rule) + ', '
            elif query in low and rulecount >= 0:
                rulecount-=1
                isIn = 1
                count = 2
                initIndex = 0
                msg = '`'+str(rule)+':`\n'
                while isIn and count > 0:
                    found = True
                    try:
                        index = low[initIndex:].index(query)
                        index += initIndex

                        initIndex = index + len(query)

                        boundLower = index - 40
                        if boundLower < 0:boundLower = 0

                        boundUpper = index + 120
                        if boundUpper >= len(low): boundUpper = len(low)-1

                        msg +=('\t...'\
                              +body[boundLower:index]\
                              +'**'+ body[index:index+len(query)]\
                              +'**'+ body[index+len(query):boundUpper]\
                              +'...').replace('\n','  ')+'\n\n'
                    except ValueError:
                        isIn = 0
                    count -= 1
                if count <= 0:
                    msg += '...and more...'
                ret_msg += msg
        if len(roundmsg) != 0:
            ret_msg += f'\nand in rules: {roundmsg}'
        if not found:
            return "Couldn't Find A Match For "+query
        return ret_msg

def rule_int(bot, rulenum):
    if not bot.has('Rules', int(rulenum)):
        return "I couldn't find that rule."
    body = bot.get('Rules', int(rulenum), 'Text')
    bot.log(f"Found Rule {rulenum}")
    body = body.replace('\\xe2\\x95\\x9e', ' ')
    body = body.replace('\\xe2\\x95\\x90', ' ')
    body = body.replace('\\xe2\\x95\\xa1', ' ')
    body = body.replace('\\xe2\\x94\\x80', ' ')
    return body

"""
Setup Log Parameters and Channel List And Whatever You Need to Check on a Bot Reset.
Handles Change In Server Structure and the like. Probably Can Leave Alone.
"""
async def reload_references(bot):
    # Do Stuff Here
    
    rule_found = []
    with urllib.request.urlopen('https://gitlab.com/nomicgame/nomic-viii/-/raw/master/rules-r.md?ref_type=heads') as response:
        rules = response.read().decode("utf-8").replace('&nbsp;~','').replace('\r','').replace('\n ','\n').replace('\n\n ','\n')
        ruletxt = rules.split("\n## ")[1:]
        print(f'   |   Found {len(ruletxt)} Rules')
        for rule in ruletxt:
            try:
                header = rule.split('\n')[0]
                rulenum = header.split(' ')[0]
                
                rule = str(markdownify.markdownify( rule, heading_style = "ATX", escape_asterisks=False))
                rule_found.append(int(rulenum))
                bot.set('Rules',int(rulenum), values={
                    'Text': rule, 
                    'Is Mutable': 'IMMUTABLE' in header
                })
            except Exception as e:
                print('ERROR Importing Rules.', e)
                print(rule)
        

    for rule in bot.keys('Rules'):
        if rule not in rule_found: bot.remove('Rules', rule)
