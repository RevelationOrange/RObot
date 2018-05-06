from base64 import b64encode,b64decode
import wikiSearch
from numpy.random import choice as rngChoice
from os import sep
from string import capwords
import time
from calendar import timegm
from math import floor


def MIME(s, encrypt=True):
    # print(s)
    if encrypt:
        txt = b64encode(bytes(s, 'utf8'))
    else:
        txt = b64decode(bytes(s, 'utf8'))
    return str(txt)[2:-1]

def canIntConvert(x):
    # just a convenience, so a string can be checked if it's an int without crashing
    try:
        int(x)
        return True
    except:
        return False

def decryptPM(msg):
    st = '<msg opcode="chat.pm">'
    end = '</msg>'
    if st in msg:
        c = MIME(msg[msg.find(st) + len(st):msg.find(end, msg.find(st) + len(st))], False)
        bodySt = '"data":"'
        fromSt = '"from":"'
        genEnd = '","'
        text = c[c.find(bodySt) + len(bodySt):c.find(genEnd, c.find(bodySt) + len(bodySt))]
        fromUser = c[c.find(fromSt) + len(fromSt):c.find(genEnd, c.find(fromSt) + len(fromSt))]
        return (text,fromUser)
    else:
        return

def formulateResponse(txt, to):
    replOutBody = '{"from":"snp2_robot","to":"%s","data":"%s"}' % (to, txt)
    replFullReq = "<iq type='get' id='9d41c8c7-98fc-4bb5-ba97-d381c9a710c4' xmlns='jabber:client'><query xmlns='kongregate:iq:msg'><msg opcode='chat.pm'>{}</msg></query></iq>"
    encrOut = MIME(replOutBody)
    fullOutReq = replFullReq.format(encrOut)
    return fullOutReq

def getNextFWTD():
    sundayNum = 6
    currentGMT = time.gmtime(time.time())
    tomorrowMidnight = [x for x in time.gmtime(time.time() + 86400.)]
    tomorrowMidnight[3:6] = 0,0,0
    if currentGMT[2] == 1:
        fwtdTier = 2
    elif currentGMT[2] == 15:
        fwtdTier = 3
    elif currentGMT[6] == sundayNum:
        fwtdTier = 4
    else:
        fwtdTier = 0
    ttm = timegm(tomorrowMidnight) - timegm(currentGMT)
    if fwtdTier:
        timeLeft = ttm
    else:
        timeLeft = 0
    nextMonth = [x for x in currentGMT]
    if nextMonth[1] == 12:
        nextMonth[0] += 1
        nextMonth[1] = 1
    else:
        nextMonth[1] += 1
    nextMonth[2:6] = 1,0,0,0
    nxtTier3 = (sundayNum - tomorrowMidnight[6]) * 86400. + ttm
    nxtTier1 = timegm(nextMonth) - timegm(currentGMT)
    if currentGMT[2] < 15:
        nxtTier2  = (15 - currentGMT[2]) * 86400. + ttm
    else:
        nextMonth[2] = 15
        nxtTier2 = timegm(nextMonth) - timegm(currentGMT)
    nxtTier2 = min(nxtTier1,nxtTier2)
    nxtTier3 = min(nxtTier1, nxtTier2, nxtTier3)
    return (fwtdTier, timeLeft, nxtTier1, nxtTier2, nxtTier3)

lenLim = 250
maxPMs = 3
def msgChopper(m):
    if len(m) > maxPMs*lenLim:
        ms = ['Too many results, please narrow down your search or use a more unique name.']
    else:
        ms = []
        msplit = m.split(' ')
        msg = ''
        while len(msplit) > 0:
            if not msg:
                msg = msplit.pop(0)
            elif len(msg + ' ' + msplit[0]) > lenLim:
                ms.append(msg)
                msg = ''
            else:
                msg += ' ' + msplit.pop(0)
        ms.append(msg)
    return ms

mindyAltsFilename = 'trackers' + sep + 'mindyAlts.txt'
mindyAltsList = []
with open(mindyAltsFilename) as maf:
    spec = False
    for line in maf:
        if line[:-1] == 'SPECULATIVE':
            spec = True
        elif spec:
            mindyAltsList.append((line[:-1], 'suspected'))
        else:
            mindyAltsList.append((line[:-1], 'known'))

townAdsFilename = 'trackers' + sep + 'townAds.csv'
townAdsList = []
with open(townAdsFilename) as adsFile:
    for line in adsFile:
        l = line[:-1].split(',')
        if l[-1] == '2':
            for ad in townAdsList:
                if ad[0] == l[0] and ad[1] == l[1]:
                    townAdsList.remove(ad)
        else:
            townAdsList.append([l[0], l[1], ' '.join(l[2:-1]), l[-1]])

def help(args=0):
    helpTexts = {
        'thread': "Here's the help thread: http://www.kongregate.com/forums/304-swords-potions-2/topics/721821. Though, to be honest, I don't think even RO fully understands how I work- at least when it comes to !search.",
        'forum': "Here's the help thread: http://www.kongregate.com/forums/304-swords-potions-2/topics/721821. Though, to be honest, I don't think even RO fully understands how I work- at least when it comes to !search.",
        'info': "This is just some info about me, author stuff, that kind of thing.",
        'search': "This is a flexible search function you can use to get lists of items, customers, buildings, shop stuff, quests, workers, achievements, and classes based on the criteria you enter. The format is: [section], [attribute]: [critera]. You can use as many attribute: criteria parts as you like, just separate them with commas. Example: items, level: range 5 10, price: over 2000",
        'item': "Display info about an item. If you use a partial item name, and there is more than one match but it is isn't an exact match (ex: knife will return info on knife, not survival knife), it will give you a list of items found.",
        'building': "Display info about a building. You can use a partial name here, but you do need to provide a building level.",
        'customer': "Display info about a customer. You can use a partial customer name here, and if there's only a single result, it'll return that, otherwise it'll return a list of all matches.",
        'cust': "Display info about a customer. You can use a partial customer name here, and if there's only a single result, it'll return that, otherwise it'll return a list of all matches.",
        'quest': "Display info about a dungeon or event quest. If more than one matching name is found, it will mark the type of quest on each result.",
        'pvp': "Get an explanation of how PVP (klash) and works. You can use !pvp or !klash, and you can specify attack, krowns, or VP to hear more about those. (ex: !pvp krowns)",
        'klash': "Get an explanation of how PVP (klash) and works. You can use !pvp or !klash, and you can specify attack, krowns, or VP to hear more about those. (ex: !pvp krowns)",
        'sheets': 'This gives a link to a bunch of useful spreadsheets that have made by players over the years, for tracking stuff, getting info, etc.',
        'gettingstarted': 'This gives a link to nick\'s new players guide.',
        'gs': 'This gives a link to nick\'s new players guide.',
        'cmd': 'This gives a list of all working commands.',
        'wiki': 'This gives a link to the edgebee snp2 wiki.',
        'fwt': 'Tells you when the next free world trade days are happening. Some cities have a building, the trader\'s guild, that grants everyone in the city access to world trade (as if they had used a coupon) for a day, on each 1st, 15th, and sunday (depending on the level of the building).',
        'fwtd': 'Tells you when the next free world trade days are happening. Some cities have a building, the trader\'s guild, that grants everyone in the city access to world trade (as if they had used a coupon) for a day, on each 1st, 15th, and sunday (depending on the level of the building).',
        'help': "Ha ha, very funny. This command just displays info about me and my commands, and it's no more complicated than !help [command]. Without the [] of course.",
    }
    if not args:
        return 'You can use commands in 2 ways. ex: !item or item: (I tend to prefer !item). For a list of all working commands, use !cmd (or: !cmds, !commands, !commandList). For more info on each command, use !help [command]. There is a 3 second timer on commands. For a (mostly) thorough explanation of me: http://www.kongregate.com/forums/304-swords-potions-2/topics/721821'
    else:
        if args[0] in helpTexts or args[0][1:] in helpTexts:
            return helpTexts[args[0]]
        else:
            return "I don't recognize the command you entered. Here are the commands you can ask about: " + ', '.join([x for x in helpTexts])

def cmd():
    return "Current working commands: !help, !info, !item, !building, !customer (or !cust), !quest, !search, !klash (or !pvp), !sheets, !gettingStarterd (or !gs), !fwt, !wiki. And !cmd."

def info():
    return 'The skeleton for this chatbot was done by qndel (getting it actually connected to kong), everything else was written by RevelationOrange, in python 3.5.2'

def timeTextConverter(t, inHrs=True):
    if inHrs:
        if t < 24.:
            s = '' if t == 1 else 's'
            timeText = '{} hour{}'.format(int(t), s)
        elif t % 24:
            days = int(floor(t / 24.))
            sd = '' if days == 1 else 's'
            hrs = int(t - days * 24)
            sh = '' if hrs == 1 else 's'
            timeText = '{} day{}, {} hour{}'.format(days, sd, hrs, sh)
        else:
            days = int(t / 24.)
            s = '' if days == 1 else 's'
            timeText = '{} day{}'.format(days, s)
    else:
        texts = []
        days = int(floor(t / 86400.))
        dpl = '' if days == 1 else 's'
        dtxt = '{} day{}'.format(days, dpl) if days else ''
        hours = int(floor((t - days*86400.) / 3600.))
        hpl = '' if hours == 1 else 's'
        htxt = '{} hour{}'.format(hours, hpl) if hours else ''
        minutes = int(floor((t - days*86400. - hours*3600.) / 60.))
        mpl = '' if minutes == 1 else 's'
        mtxt = '{} minute{}'.format(minutes, mpl) if minutes else ''
        if days: texts.append(dtxt)
        if hours: texts.append(htxt)
        if minutes: texts.append(mtxt)
        # if len(texts) > 2: texts.pop()
        timeText = ', '.join(texts)
    return timeText

def printHandler(infoObj, section):
    if section == 'items':
        if infoObj['type'] == 'rare resources':
            infoRepl = '{name}, lvl {level} ({type}). {value:,} gold.'
            if infoObj['nfRecs'] != '--':
                infoRepl += ' Precraft for: {}.'.format(', '.join([x for x in infoObj['nfRecs']]))
            prString = infoRepl.format(**infoObj)
            return prString
        else:
            infoRepl = '{name}, lvl {level} ({type}). {value:,} gold, {ctText} craft time. Uses: {ingrs}, made by {madeBy} on {station}. Unlocked by {unlckBy}, Unlocks {unlcks}.'
            tmp = {}
            tmp['name'] = capwords(infoObj['name'])
            tmp['ctText'] = infoObj['craftTime'].lower()
            tmp['ingrs'] = ', '.join([' '.join([str(y) for y in x]) for x in infoObj['ingredients']])
            tmp['station'] = ' '.join([capwords(str(x)) for x in infoObj['madeOn']])
            tmp['unlckBy'] = '(starter recipe)' if not infoObj['prevItem'] else infoObj['prevItem'][0] if len(infoObj['prevItem']) == 1 else '{} ({})'.format(*infoObj['prevItem'])
            if infoObj['nextItem'] == [['--']]:
                tmp['unlcks'] = '--'
            else:
                tmp['unlcks'] = ', '.join([capwords('{} ({})'.format(*x)) for x in infoObj['nextItem']])
            if infoObj['nfRecs'] != '--':
                infoRepl += ' Precraft for: {}.'.format(', '.join([x for x in infoObj['nfRecs']]))
            if infoObj['nfQuests'] != ['--']:
                infoRepl += ' Used in quests: {}.'.format(', '.join(infoObj['nfQuests']))
            if infoObj['nfBuilds'] != ['--']:
                infoRepl += ' Needed for buildings: {}'.format(', '.join(['{} {} ({})'.format(*x) for x in infoObj['nfBuilds']]))
            infoObj.update(tmp)
            prString = infoRepl.format(**infoObj)
            return prString
    elif section == 'buildings':
        infoRepl = "{name} {level}. "
        timeText = timeTextConverter(infoObj['time'])
        '''
        check buildings:
        for time text: archery range 1, 2, refinery 10, mysterious pillars 10, pier 4
        '''
        if type(infoObj['unlockedBy']) is list:
            prevBuild = '{} {}'.format(*infoObj['unlockedBy'])
        else:
            prevBuild = infoObj['unlockedBy']
        infoRepl += "Cost: {}, {}, unlocked by {}.".format('{:,} {}'.format(*infoObj['upgradeCost']), timeText, prevBuild)
        if infoObj['buildUnlocks']:
            if infoObj['buildUnlocks'] != 'none':
                infoRepl += " Buildings unlocked: {}.".format(', '.join(['{} {}'.format(*x) for x in infoObj['buildUnlocks']]))
        if infoObj['custUnlocks'] != 'none':
            infoRepl += " Customers: {}.".format(', '.join(['{} ({})'.format(*x) for x in infoObj['custUnlocks']]))
        if infoObj['bonus'] != 'none':
            infoRepl += " Bonus: {} {}".format(*infoObj['bonus'])
        prString = infoRepl.format(**infoObj)
        return prString
    elif section == 'customers':
        infoRepl = "{name} ({class}), lvl range {startLvl}-{maxLvl}. Buys {}. Level required: {lvlReq}, appeal required: {appealReq}. Unlocked by {}."
        buyList = ', '.join(infoObj['iTypes'])
        unlck = '{} {}'.format(*infoObj['unlockedBy'])
        prString = infoRepl.format(buyList, unlck, **infoObj)
        return prString
    elif section == 'dungeon':
        infoRepl = "{name} (dungeon quest), lvl {shopLvlReq}, xp per loot: {xpPerLoot:,}, duration {} ({} with max lighthouse bonuses). Rewards: {}. Value req'd for 100% common: {comValue:,}. Max level (still gets xp): {maxLvl}"
        timeText = timeTextConverter(infoObj['time'])
        timeTextLH = timeTextConverter(infoObj['time']*0.8)
        rews = ', '.join(['{} {}'.format(*x) for x in infoObj['loots']])
        prString = infoRepl.format(timeText, timeTextLH, rews, **infoObj)
        return prString
    elif section == 'event':
        infoRepl = "{name} (event quest), lvl {shopLevelReq}, xp per customer: {xp:,}, duration: {}. Items required: {}. Customers required: {}. Reward: {}. Unlocked by {unlockedBy}."
        timeText = timeTextConverter(infoObj['time'])
        iReqs = ', '.join(infoObj['itemsNeeded'])
        cReqs = ', '.join(infoObj['custsNeeded'])
        rew = ' '.join([str(x).replace('_', ' ') for x in infoObj['reward']])
        prString = infoRepl.format(timeText, iReqs, cReqs, rew, **infoObj)
        return prString

def item(args):
    itemName = ' '.join(args)
    if itemName == 'poop bucket' or itemName == 'poop_bucket':
        return getKnarfResp()
    elif itemName == 'acid bin':
        return "Acid is a rare resource, there's no bin for it. You get it from quests, the daily spin, or krown chests (but don't spend krowns on it lol)."
    elif itemName.lower() == 'walking fortress':
        itemName = 'walking forteress'
    elif 'codex' in itemName.lower():
        itemName = 'codex de genèse'
    elif itemName.lower() == 'lag':
        time.sleep(5)
    searchText = 'items, name: {}'.format(itemName)
    try:
        res = wikiSearch.quickSearch(searchText, False)
    except:
        return 'Error: be sure to include an item name with !item (and no extra spaces). If you need help, /w me !help, or !help item'
    if res:
        exactMatch = 0
        for i in res:
            if i['name'] == itemName:
                exactMatch = i
        if exactMatch:
            found = exactMatch
            print('exact match')
        elif len(res) > 1:
            return '{} items found matching that name, and no exact match: '.format(len(res)) + ', '.join([x['name'] for x in res])
        else:
            found = res[0]
            print('single result partial match')
        return printHandler(found, 'items')
    else:
        return 'No items found matching that name.'

def building(args):
    i = 0
    while i < len(args) and not canIntConvert(args[i]):
        i += 1
    if i and i < len(args):
        bName = ' '.join(args[:i])
        bLvl = args[i]
        searchText = "buildings, name: {}, level: {}".format(bName, bLvl)
        try:
            res = wikiSearch.quickSearch(searchText, False)
        except:
            return "Error: be sure to include a building name and level with !building, such as: !building city hall 3"
        if res:
            exactMatch = 0
            for b in res:
                if b['name'] == bName:
                    exactMatch = b
            if exactMatch:
                found = exactMatch
            elif len(res) == 1:
                found = res[0]
            else:
                return "{} buildings found matching that name, and no exact match: ".format(len(res)) + ', '.join([x['name'] for x in res])
            return printHandler(found, 'buildings')
        else:
            return "No buildings found with that name and level."
    else:
        return "To get building info, you need to provide the name and level of the building. ex: !building city hall 3"

def customer(args):
    custName = ' '.join(args)
    if custName.lower() == 'rupert':
        return "Maybe you meant rubert? " + customer(['rubert'])
    searchText = 'customers, name: {}'.format(custName)
    try:
        res = wikiSearch.quickSearch(searchText, False)
    except:
        return "Error: be sure to include at least a partial customer name, and no extra spaces."
    if res:
        # search for exact match, then check exact match, single partial match, or multiple results
        exactMatch = 0
        for c in res:
            if c['name'] == custName:
                exactMatch = c
        if exactMatch:
            found = exactMatch
        elif len(res) == 1:
            found = res[0]
        else:
            return "{} customers found matching that name, and no exact match: ".format(len(res)) + ', '.join([x['name'] for x in res])
        return printHandler(found, 'customers')
    else:
        return "No customers found matching that name."

def quest(args):
    qname = ' '.join(args)
    qSearchText = 'quests, name: {}'.format(qname)
    hSearchText = 'hunts, name: {}'.format(qname)
    results = []
    try:
        qRes = wikiSearch.quickSearch(qSearchText, False)
    except:
        return "Error: be sure to include at least a partial quest name, and no extra spaces"
    for r in qRes:
        results.append([r, 'event'])
    try:
        hRes = wikiSearch.quickSearch(hSearchText, False)
    except:
        return "Error: be sure to include at least a partial quest name, and no extra spaces"
    for r in hRes:
        results.append([r, 'dungeon'])
    if results:
        exactMatch = 0
        for qh in results:
            if qh[0]['name'] == qname:
                exactMatch = qh
        if exactMatch:
            found = exactMatch
        elif len(results) == 1:
            found = results[0]
        else:
            return "{} dungeon and/or event quests found matching that name, and no exact match: ".format(len(results)) + \
                   ', '.join(['{} ({})'.format(x[0]['name'], x[1]) for x in results])
        return printHandler(found[0], found[1])
    else:
        return "No dungeon or event quests found matching that name."

def search(args):
    if args == ['nick']:
        return "We Are All nick"
    res = 'search results: '
    try:
        names = wikiSearch.quickSearch(' '.join(args))
    except IndexError:
        return 'Error: bad search statement. Be sure not to have any spare spaces or commas, and include criteria if you use \'attribute:\' (bad ex: \'items:, \' or \'items: name:\')'
    except ValueError:
        return 'Error: bad search statement. Be sure to include numbers in the critera if you include numeric attributes (ex: \'items, value: \')'
    except TypeError:
        if args:
            return 'Error: invalid section used ({}).'.format(args[0])
        else:
            return 'Error: must specify a section (and be sure not to have any extra spaces). Use !help search for more info.'
    except BaseException as ex:
        return 'Error: invalid attribute or criteria used. Be sure the attribute you\'re using is appropriate (so don\'t use ingredients when searching in buildings), and don\'t use extra terms in the critera (ex: \'range 5 10\' is correct, \'5 to 10\' is not)'
    except:
        return 'Error: uh... something. An error I haven\'t thought of came up, let me know this happened and I\'ll account for it.'
    res += names
    return res

def mindyAlts():
    msg = 'known alts: ' + ', '.join([x[0] for x in mindyAltsList if x[1] == 'known'])
    if len([x for x in mindyAltsList if x[1] == 'suspected']):
        msg += ', suspected alts: ' + ', '.join([x[0] for x in mindyAltsList if x[1] == 'suspected'])
    return msg

def submitTownAd(usr,args=0):
    if args:
        if len(args) == 1:
            for ad in townAdsList:
                if ad[0] == args[0] and ad[-1] == '1':
                    return 'ad found for {}: {} (submitted by {})'.format(args[0], ad[2], ad[1])
            return "No enabled ad found for {}. To submit one, use !submitTownAd {} [message], and bug RO to enable it (and any already submitted ads).".format(args[0], args[0])
        else:
            with open(townAdsFilename, 'a') as adsFile:
                adsFile.write(','.join([args[0], usr, ' '.join(args[1:]), '0']) + '\n')
            return 'Message added for {}! RO will need to manually enable it before it\'s added to the queue.'.format(args[0])
    else:
        return "Please provide a town name and advertisement message."

def removeTownAd(usr,args=0):
    if args:
        for ad in townAdsList:
            if ad[0] == args[0] and ad[-1] == '1':
                if ad[1] == usr:
                    with open(townAdsFilename, 'a') as adsFile:
                        adsFile.write(','.join([args[0], usr, ad[2], '2']) + '\n')
                    townAdsList.remove(ad)
                    return 'Ad for {} disabled.'.format(args[0])
                else:
                    return 'That ad was created by another user, ask them to disable it, or ask RO if he\'s around.'
        return 'No enabled ad for {} found.'.format(args[0])
    else:
        return "Please specify a town name in order to disable the ad for that town. Note that you must be person who submitted an ad in order to disable it."

def pvp(args):
    argDict = {'attack': "Customer attack works similar to quests, only you take the square root of the item's value, rounded down (their level has an associated value too). This contributes to a category, fighters, rogues, or spellcasters, based on the customer's class.",
               'krown': "Krowns are a currency you get from klash, For reaching certain attack totals, you get 5 krowns. 100 krowns is the max reward per klash, which takes 24k attack. Krowns can be spent opening chests, with either rare resources or special items.",
               'krowns': "Krowns are a currency you get from klash, For reaching certain attack totals, you get 5 krowns. 100 krowns is the max reward per klash, which takes 24k attack. Krowns can be spent opening chests, with either rare resources or special items.",
               'vp': "Victory points are the reward for winning categories in klash. If you get more VP than the other town, you 'win' the klash (which has no specific reward itself). You can unlock some things by getting enough VPs, for example, the epic defender recipe.",
               'vps': "Victory points are the reward for winning categories in klash. If you get more VP than the other town, you 'win' the klash (which has no specific reward itself). You can unlock some things by getting enough VPs, for example, the epic defender recipe."}
    if args:
        if args[0].lower() in argDict:
            return argDict[args[0].lower()]
        else:
            return "Sorry, {} isn't an option for more info in !pvp. It's only attack, krowns, or VP.".format(args[0])
    else:
        return "Klash basics: every player in a city can send 10 customers per klash (25hrs). Their attack value goes towards both your krown rewards and one category based on their class. Each town wins 1 VP per category they win, whichever town gets more VP wins. " + \
               "For more info about it, use !pvp attack, !pvp krowns, or !pvp VP"

def fwt():
    tier,timeLeft,nxt1,nxt15,nxtSun = getNextFWTD()
    ttxt0 = timeTextConverter(timeLeft, False)
    ttxt1 = timeTextConverter(nxt1, False)
    ttxt2 = timeTextConverter(nxt15, False)
    ttxt3 = timeTextConverter(nxtSun, False)
    if tier:
        return "Free world trade is active! Trader's guilds level {} and up can use it, {} left. Upcoming FWTs for levels-  2 (1st of the month): {}; 3 (+15th): {}; 4 (+sunday): {}.".format(tier, ttxt0, ttxt1, ttxt2, ttxt3)
    else:
        return "Next free world trade days for trader's guild level- 2 (1st of the month): {}; 3 (+15th): {}; 4 (+sunday): {}.".format(ttxt1, ttxt2, ttxt3)

def hinder():
    return "If you insist."

def stopHinder(args):
    if args:
        return "No hinderance to stop."
    else:
        return "Ok, enough of that."

def sheets():
    return "Here's the list of spreadsheets: bit.ly/snp2_sheets"

def gettingStarted():
    return "Here's a useful guide for new players: bit.ly/SP2guide"

def wiki():
    return "Here's the edgebee wiki for snp2: http://www.edgebee.com/wiki/index.php?title=Swords_%26_Potions_2"

optionDict = {'info':info, 'help':help, 'search':search, 'item':item, 'mindyalts':mindyAlts, 'pvp':pvp, 'klash':pvp,
              'submittownad':submitTownAd, 'removetownad':removeTownAd, 'hinder':hinder, 'stophinder':stopHinder,
              'sheets':sheets, 'spreadsheets':sheets, 'building':building, 'customer':customer, 'cust':customer,
              'gettingstarted':gettingStarted, 'gs':gettingStarted, 'quest':quest, 'fwt':fwt, 'fwtd':fwt,
              'freeworldtrade':fwt, 'freeworldtradeday':fwt, 'wiki':wiki, 'cmd':cmd, 'cmds':cmd, 'commands':cmd,
              'commandlist':cmd}
noArgFxns = ['info', 'mindyalts', 'hinder', 'sheets', 'gettingstarted', 'gs', 'fwt', 'fwtd', 'freeworldtrade',
             'freeworldtradeday', 'wiki', 'cmd', 'cmds', 'commands', 'commandlist']
usrFxns = ['submittownad', 'removetownad']
pmOnly = ['mindyalts']
hinderRNG = ['info', 'help', 'search', 'item', 'pvp', 'hinder', 'sheets', 'building', 'cust', 'gs', 'quest', '']
optionDictAdmin = ['say', 'msgs', 'yay']
knarfResponses = [
    'In loving memory of knarfbot, may its bucket be ever full',
    'rip knarfbot o7',
    'in knarfbot we trust',
    "knarf's bucket has been pooped, but it shall live on in our hearts",
]
def getKnarfResp():
    return rngChoice(knarfResponses)

grpMsgRepl = "<message to='174726-swords-and-potions-2-1@conference.of1.kongregate.com' from='snp2_RObot@of1.kongregate.com/xiff' type='groupchat' id='dc96ae0e-27ec-40e5-83f2-b4a013d5ec0a' xmlns='jabber:client'><body>{}</body><x xmlns='jabber:x:event'><composing/></x></message>"

def handler(fxnRaw, usr, args):
    fxn = fxnRaw.lower()
    if fxn in optionDict and not (usr in [x[0] for x in mindyAltsList] and fxn == 'mindyalts'):
        if fxn in noArgFxns:
            message = optionDict[fxn]()
            # return optionDict[fxn](usr)
        elif fxn in usrFxns:
            message = optionDict[fxn](usr, args)
        else:
            message = optionDict[fxn](args)
            # return optionDict[fxn](usr, args)
        msgs = msgChopper(message)
        outs = []
        for m in msgs:
            outReq = formulateResponse(m, usr)
            outs.append(outReq)
        return (outs, msgs)
    else:
        message = "That's not a recognized/implemented command (yet?). Use !help for more info."
        msgs = msgChopper(message)
        outs = []
        for m in msgs:
            outReq = formulateResponse(m, usr)
            outs.append(outReq)
        return (outs, msgs)
