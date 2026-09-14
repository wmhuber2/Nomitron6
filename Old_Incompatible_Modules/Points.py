

def setup(bot):
    bot.init_database('Souls', id_key='Soul-ID', columns=[
        'Soul-ID', 'Owner-PID', 
    ])

    for pid in bot.keys('Users'):
        souldid = pid
        if 'Souls' in bot.Databases and not bot.has('Souls',souldid):
            bot.set('Souls',souldid, values={'Owner-PID':pid})
            

        if type(bot.get('Users',pid,'Proposals Vote Blam Counter')) not in [float, int]:
            bot.set('Users',pid,values={'Proposals Vote Blam Counter':0})
        if type(bot.get('Users',pid,'Points')) not in [float, int]:
            bot.set('Users',pid,values={'Points':0})