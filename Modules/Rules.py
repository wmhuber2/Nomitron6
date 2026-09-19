"""
Main Run Function On Messages
"""
import sys, urllib, discord, io # type: ignore

def find(bot, text):
    query = text.lower()
    ret_msg = []

    if query[ 0] == '"': query = query[1:  ]
    if query[-1] == '"': query = query[ :-1]

    if len(query) <= 2: return "Must Search Words Longer Then 2 Letters"
    else:
        rulecount = 5
        list_of_rules = bot.where(['Rules', '*', "Text"], lambda x: query in x.lower())
        if len(list_of_rules) <= 0: return "No Rules Found With That Test"

        for rule_key in list_of_rules:
            rule_key = rule_key[1]
            head = bot.get('Rules', rule_key, "Header")
            body = bot.get('Rules', rule_key, "Text")
            low  = body.lower()

            if rulecount <= 0: break
            else:
                rulecount-=1
                count = 2
                initIndex = 0
                msg = '`'+str(head)+':`\n'
                while count > 0:
                    if query not in low[initIndex:]: break
                    index = low[initIndex:].index(query)
                    index += initIndex

                    initIndex = index + len(query)

                    boundLower = index - 40
                    if boundLower < 0:boundLower = 0

                    boundUpper = index + 120
                    if boundUpper >= len(low): boundUpper = len(low)-1

                    msg +=( ('\t...' if boundLower > 0 else '')\
                            +body[boundLower:index]\
                            +'**'+ body[index:index+len(query)]\
                            +'**'+ body[index+len(query):boundUpper]\
                            +'...').replace('\n','  ')+'\n\n'
                
                    count -= 1
                if count <= 0:
                    msg += '...and more in this rule...'
                ret_msg.append(msg)
        
    return ret_msg

def rule(bot, rulenum):
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
    if bot.has('Rules'):
        for rule in bot.keys('Rules'):
            if rule not in rule_found: bot.remove('Rules', rule)

    with urllib.request.urlopen('https://gitlab.com/nomicgame/nomic-viii/-/raw/master/rules-r.md?ref_type=heads') as response:
        rules = response.read().decode("utf-8").replace('&nbsp;~','').replace('\r','').replace('\n ','\n').replace('\n\n ','\n')
        ruletxt = rules.split("\n## ")[1:]
        for rule in ruletxt:
            try:
                header = rule.split('\n',1)[0]
                body   = rule.split('\n',1)[1]
                rulenum = header.split(' ')[0]
                
                rule = str(rule) #markdownify.markdownify( rule, heading_style = "ATX", escape_asterisks=False))
                rule_found.append(int(rulenum))
                bot.set(('Rules', int(rulenum)), kwargs={
                    'Header': header, 
                    'Text': body, 
                    'Is Mutable': 'IMMUTABLE' in header
                })
            except Exception as e:
                bot.log('ERROR Importing Rules.', e, rule)
        
async def on_message(bot, message):
    bot.log(f"Message Received: {message['Content']}")
    if message['Content'].startswith('!find'):
        await bot.Modules['Discord_Module'].send(bot=bot, target=message['Channel'], content=find(bot, message['Content'][6:]), silent=True) 
    elif message['Content'].startswith('!rule'):
        await bot.Modules['Discord_Module'].send(bot=bot, target=message['Channel'], content=rule(bot, message['Content'][6:]), silent=True) 

