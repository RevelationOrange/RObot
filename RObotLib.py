from base64 import b64encode,b64decode
import wikiSearch
#from numpy.random import choice as rngChoice
import random
from os import sep
from string import capwords
import time
from calendar import timegm
from math import floor


typeStringConverter = {"WK": "thrown", "WB": "bows", "US": "scrolls", "GL": "bracers", "BL": "shoes", "UP": "potions",
                       "WG": "guns", "WL": "music", "WP": "spears", "BM": "boots", "AL": "clothes", "UH": "herbs",
                       "XP": "amulets", "WS": "swords", "WT": "staves", "BH": "heavy boots", "HH": "heavy helmets",
                       "WD": "daggers", "AM": "armor", "AH": "heavy armor", "WA": "axes", "S": "shields",
                       "GM": "gloves", "HM": "helmets", "XR": "rings", "WM": "maces", "GH": "gauntlets",
                       "SI": "rare resources", "HL": "hats"}

closeDate = timegm(time.strptime("20 Apr 2018", "%d %b %Y"))

def MIME(s, encrypt=True):
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
    # print(tomorrowMidnight)
    # print(currentGMT)
    if currentGMT[2] == 1:
        fwtdTier = 2
    elif currentGMT[2] == 15:
        fwtdTier = 3
    elif currentGMT[6] == sundayNum:
        fwtdTier = 4
    else:
        fwtdTier = 0
    ttm = timegm(tomorrowMidnight) - timegm(currentGMT)
    # print(timeTextConverter(ttm, False))
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
    if currentGMT[2]+1 <= 15:
        nxtTier2  = (15 - (currentGMT[2]+1)) * 86400. + ttm
    else:
        nextMonth[2] = 15
        nxtTier2 = timegm(nextMonth) - timegm(currentGMT)
    nxtTier2 = min(nxtTier1,nxtTier2)
    nxtTier3 = min(nxtTier1, nxtTier2, nxtTier3)
    return (fwtdTier, timeLeft, nxtTier1, nxtTier2, nxtTier3)

def getTimeToMidnight():
    currentGMT = time.gmtime(time.time())
    tomorrowMidnight = [x for x in time.gmtime(time.time() + 86400.)]
    tomorrowMidnight[3:6] = 0, 0, 0
    ttm = timegm(tomorrowMidnight) - timegm(currentGMT)
    return ttm

def getTimeToClosing():
    return closeDate - time.time()

def msgChopper(m):
    lenLim = 250
    maxPMs = 3
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

def help(args=0):
    helpTexts = {
        'thread': "Here's the help thread: http://www.kongregate.com/forums/304-swords-potions-2/topics/721821. Though, to be honest, I don't think even RO fully understands how I work- at least when it comes to !search.",
        'forum': "Here's the help thread: http://www.kongregate.com/forums/304-swords-potions-2/topics/721821. Though, to be honest, I don't think even RO fully understands how I work- at least when it comes to !search.",
        'info': "This is just some info about me, author stuff, that kind of thing.",
        'search': "This is a flexible search function you can use to get lists of items, customers, buildings, shop stuff, quests, workers, achievements, and classes based on the criteria you enter. The format is: [section], [attribute]: [critera]. You can use as many attribute: criteria parts as you like, just separate them with commas. Example: items, level: range 5 10, price: over 2000. For more info: www.kongregate.com/forums/304-swords-potions-2/topics/721821",
        'item': "Display info about an item. If you use a partial item name, and there is more than one match but it is isn't an exact match (ex: knife will return info on knife, not survival knife), it will give you a list of items found.",
        'building': "Display info about a building. You can use a partial name here, but you do need to provide a building level.",
        'customer': "Display info about a customer. You can use a partial customer name here, and if there's only a single result, it'll return that, otherwise it'll return a list of all matches.",
        'cust': "Display info about a customer. You can use a partial customer name here, and if there's only a single result, it'll return that, otherwise it'll return a list of all matches.",
        'quest': "Display info about a dungeon or event quest. If more than one matching name is found, it will mark the type of quest on each result.",
        'worker': 'Display info about a worker, just basic stuff like hire cost and when they unlock. If you want a list of items a worker makes, use !search items, made by: whoever',
        'module': "Display info about a shop item (like bins or racks). None of the tier 1 names include the 1, everything else includes its tier number. Ex: leather bin (works for tier 1) leather bin 1 (doesn't), leather bin 3 (works for tier 3). Note that this gives info about every level in a tier, so some of the modules will send multiple messages. And heavy armor rack 3 has too much info, it goes over the 3 message limit.",
        'pvp': "Get an explanation of how PVP (klash) and works. You can use !pvp or !klash, and you can specify attack, krowns, or VP to hear more about those. (ex: !pvp krowns)",
        'klash': "Get an explanation of how PVP (klash) and works. You can use !pvp or !klash, and you can specify attack, krowns, or VP to hear more about those. (ex: !pvp krowns)",
        'sheets': 'This gives a link to a bunch of useful spreadsheets that have made by players over the years, for tracking stuff, getting info, etc.',
        'gettingstarted': 'This gives a link to nick\'s new players guide.',
        'gs': 'This gives a link to nick\'s new players guide.',
        'cmd': 'This gives a list of all working commands.',
        'wiki': 'This gives a link to the edgebee snp2 wiki.',
        'fwt': 'Tells you when the next free world trade days are happening. Some cities have a building, the trader\'s guild, that grants everyone in the city access to world trade (as if they had used a coupon) for a day, on each 1st, 15th, and sunday (depending on the level of the building).',
        'fwtd': 'Tells you when the next free world trade days are happening. Some cities have a building, the trader\'s guild, that grants everyone in the city access to world trade (as if they had used a coupon) for a day, on each 1st, 15th, and sunday (depending on the level of the building).',
        'deadline': 'Tells you the time until midnight GMT, when the shrine krown bonus deadline is.',
        'logindeadline': 'Tells you the time until midnight GMT, when the shrine krown bonus deadline is.',
        'ld': 'Tells you the time until midnight GMT, when the shrine krown bonus deadline is.',
        'wtfodder': 'Gives a list of items that can almost always be sold for max or near max (+900%) on world trade.',
        'wtitems': 'Gives a list of items that can almost always be sold for max or near max (+900%) on world trade.',
        '900': 'Gives a list of items that can almost always be sold for max or near max (+900%) on world trade.',
        '8ball': 'Gives a random positive/negative/unknown response, like a magic 8ball.',
        'bunnycuddle': 'Gives you a bunnycuddle, in place of chev\'s rabbit, bun helsing',
        'donate': 'Gives info about how to donate to RO, if you want to support him for this bot (never feel obligated!)',
        'support': 'Gives info about how to donate to RO, if you want to support him for this bot (never feel obligated!)',
        'help': "Ha ha, very funny. This command just displays info about me and my commands, and it's no more complicated than !help [command]. Without the [] of course.",
    }
    if not args:
        return 'You can use commands in 2 ways. ex: !item or item: (I tend to prefer !item). For a list of all working commands, use !cmd (or: !cmds, !commands, !commandList). For more info on each command, use !help [command]. There is a 3 second timer on commands. For a (mostly) thorough explanation of me: http://www.kongregate.com/forums/304-swords-potions-2/topics/721821'
    else:
        if args[0] in helpTexts:
            return helpTexts[args[0]]
        else:
            return "I don't recognize the command you entered. Here are the commands you can ask about: " + ', '.join([x for x in helpTexts])

def cmd():
    return "Current working commands: !help, !info, !item, !building, !customer (or !cust), !quest, !worker, !module, !search, !klash (or !pvp), !sheets, !gettingStarted (or !gs), !fwt, !wiki, !logindeadline (or !deadline, or !ld), !wtfodder (or !wtitems or !900), !acidbin, !8ball, !bunnycuddle, !donate (or !support). And !cmd. (and possibly more RO has just forgotten to add to this text, who knows)"

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
        pref = ''
        if t < 0:
            pref = '-'
            t *= -1
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
        if len(texts) > 2: texts.pop()
        timeText = pref + ', '.join(texts)
    return timeText

def getDescriptionText(bonusStr):
    if bonusStr == 'customers.extra_per_day':
        descriptionText = 'extra customers per day'
    else:
        descrSections = bonusStr.split('.')
        if descrSections[0] == 'resource':
            if descrSections[1] == 'count_per_hour':
                if descrSections[-1] == 'all':
                    descriptionText = descrSections[-1] + '/hr'
                else:
                    descriptionText = descrSections[-1][4:] + '/hr'
            else:
                descriptionText = descrSections[-1][4:]
        elif descrSections[0] == 'critical':
            descriptionText = 'dupe chance for {}'.format(descrSections[-1])
        elif descrSections[0] == 'sell_price':
            if descrSections[-1] == 'all':
                descriptionText = 'any sale price'
            else:
                descriptionText = '{} sale price'.format(typeStringConverter[descrSections[-1]])
        elif descrSections[0] == 'sell_price_mod':
            if descrSections[-1] == 'all':
                descriptionText = 'sale % bonus'
            else:
                descriptionText = '{} sale % bonus'.format(typeStringConverter[descrSections[-1]])
        elif descrSections[0] == 'sell_xp':
            if descrSections[-1] == 'all':
                descriptionText = 'sale xp'
            else:
                descriptionText = '{} sale xp'.format(typeStringConverter[descrSections[-1]])
        elif descrSections[0] == 'craft_xp':
            descriptionText = 'craft xp'
        elif descrSections[0] == 'quest_xp':
            if descrSections[-1] == 'all':
                descriptionText = 'quest xp'
            else:
                descriptionText = '{} quest xp'.format(descrSections[-1])
        elif descrSections[0] == 'loot_bonus':
            if descrSections[-1] == 'all':
                descriptionText = 'loot chance'
            else:
                descriptionText = '{} loot bonus'.format(descrSections[-1])
        elif descrSections[0] == 'seller_probability':
            descriptionText = 'chance for customer sale'
        elif descrSections[0] == 'breaking_chance':
            if descrSections[-1] == 'war':
                descriptionText = 'klash break chance reduction'
            if descrSections[-1] == 'hunt':
                descriptionText = 'quest break chance reduction'
        elif descrSections[0] == 'klash_bonus':
            descriptionText = 'klash attack for {}'.format(descrSections[-1])
        elif descrSections[0] == 'daily_group_login':
            descriptionText = 'daily krowns'
        elif descrSections[0] == 'klash_merc_max':
            descriptionText = 'max mercs for {}'.format(descrSections[-1])
    return descriptionText

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
            infoRepl += ' Precraft for: {}.'.format(', '.join([x for x in infoObj['nfRecs']]))
            if infoObj['nfQuests'] != ['--']:
                infoRepl += ' Used in quests: {}.'.format(', '.join(infoObj['nfQuests']))
            if infoObj['nfBuilds'] != [['--']]:
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
        if len(infoObj['unlockedBy']) > 1:
            prevBuild = '{} {}'.format(*infoObj['unlockedBy'])
        else:
            prevBuild = infoObj['unlockedBy'][0]
        infoRepl += "Cost: {}, {}, unlocked by: {}.".format('{:,} {}'.format(*infoObj['upgradeCost']) if infoObj['upgradeCost'] else 'none', timeText, prevBuild)
        if infoObj['buildUnlocks']:
            # if infoObj['buildUnlocks'] != 'none':
            infoRepl += " Buildings unlocked: {}.".format(', '.join(['{} {}'.format(*x) for x in infoObj['buildUnlocks']]))
        if infoObj['custUnlocks']:
            infoRepl += " Customers: {}.".format(', '.join(['{} ({})'.format(*x) for x in infoObj['custUnlocks']]))
        if infoObj['bonus']:
            infoRepl += " Bonus: {} {}".format(getDescriptionText(infoObj['bonus'][0]), infoObj['bonus'][1])
        prString = infoRepl.format(**infoObj)
        return prString
    elif section == 'customers':
        infoRepl = "{name} ({chClass}), lvl range {startLvl}-{maxLvl}. Buys {}. Level required: {lvlReq}, appeal required: {appealReq}. Unlocked by {}."
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
    elif section == 'workers':
        infoRepl = "The {name} is unlocked at level {shopLevelReq} for {goldCost:,} gold (or {couponCost} coupon(s), but never do that)"
        prString = infoRepl.format(**infoObj)
        return prString
    elif section == 'modules':
        infoRepl = '{name} (tier {tier})'
        if infoObj['bonuses']:
            infoRepl += ' bonuses: '
            for b in infoObj['bonuses']:
                # here is where b[0] should be converted into something more readable
                descriptionText = getDescriptionText(b[0])
                ##
                infoRepl += '{}: {}, '.format(descriptionText, ', '.join([str(round(x, 4)) for x in b[1]]))
            infoRepl = infoRepl[:-2] + '.'
        if infoObj['goldCosts'] and -1 not in infoObj['goldCosts']:
            infoRepl += ' gold costs: {},'.format(', '.join(['{:,}'.format(x) for x in infoObj['goldCosts']]))
        ttimes = ', '.join([timeTextConverter(x, False) for x in infoObj['times']])
        infoRepl += ' hammer cost: {hammerCost}. upgrade times: ' + '{},'.format(ttimes)
        if infoObj['appeals']:
            infoRepl += ' appeal bonuses: {},'.format(', '.join([str(x) for x in infoObj['appeals']]))
        infoRepl += ' unlocked at level {levelReq}, by {unlockedBy} (max {maxBuyable} with gold)'
        prString = infoRepl.format(**infoObj)
        return prString

def item(args):
    itemName = ''.join([x for x in ' '.join(args) if x != '\\'])
    if itemName == 'poop bucket' or itemName == 'poop_bucket':
        return getKnarfResp()
    elif itemName == 'acid bin':
        return acidBin()
    elif itemName.lower() == 'walking fortress':
        itemName = 'walking forteress'
    elif itemName.lower() == 'drums of meh':
        itemName = 'crystal drum'
    elif 'codex' in itemName.lower():
        itemName = 'codex de genèse'
    elif itemName.lower() == 'lag':
        time.sleep(5)
    searchText = 'items, name: {}'.format(itemName)
    try:
        res = wikiSearch.quickSearch(searchText, False)
    except:
        return 'Error: be sure to include an item name with !item (and no extra spaces). If you need help, /w me !help, or !help item'
    if not res:
        if searchText[-1] == 's':
            res = wikiSearch.quickSearch(searchText[:-1], False)
    if res:
        exactMatch = 0
        for i in res:
            if i['name'].lower() == itemName.lower():
                exactMatch = i
        if exactMatch:
            found = exactMatch
            print('\texact match')
        elif len(res) > 1:
            return '{} items found matching that name, and no exact match: '.format(len(res)) + ', '.join([x['name'] for x in res])
        else:
            found = res[0]
            print('\tsingle result partial match')
        return printHandler(found, 'items')
    else:
        return 'No items found matching that name.'

def building(args):
    i = 0
    while i < len(args) and not canIntConvert(args[i]):
        i += 1
    if i and i < len(args):
        bName = ''.join([x for x in ' '.join(args[:i]) if x != '\\'])
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
    elif custName.lower() == 'jerk':
        return "All of them. Every single one."
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
    qname = ''.join([x for x in ' '.join(args) if x != '\\'])
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

def worker(args):
    wname = ' '.join(args)
    correctionDict = {'shopkeeper': 'Worker', 'shopkeep': 'Worker', 'shop keeper': 'Worker', 'shop keep': 'Worker',
                      'leather worker': 'Leather-worker', 'lw': 'Leather-worker', 'leatherworker': 'Leather-worker'}
    if wname in correctionDict:
        wname = correctionDict[wname]
    searchText = 'workers, name: {}'.format(wname)
    try:
        res = wikiSearch.quickSearch(searchText, False)
    except:
        return 'Error: be sure to include a worker name with !worker (and no extra spaces). If you need help, /w me !help, or !help worker'
    if res:
        exactMatch = 0
        for w in res:
            if w['name'] == wname:
                exactMatch = w
        if exactMatch:
            found = exactMatch
        elif len(res) == 1:
            found = res[0]
        else:
            return "{} workers found matching that name, and no exact match: ".format(len(res)) + ', '.join([x['name'] for x in res])
        return printHandler(found, 'workers')
    else:
        return "No workers found matching that name."

def module(args):
    mname = ' '.join(args)
    if mname.lower() == 'acid bin':
        return acidBin()
    searchText = 'modules, name: {}'.format(mname)
    try:
        res = wikiSearch.quickSearch(searchText, False)
    except:
        return 'Error: be sure to include a module name with !module (and no extra spaces). If you need help, /w me !help, or !help module'
    if res:
        exactMatch = 0
        for m in res:
            if m['name'] == mname:
                exactMatch = m
        if exactMatch:
            found = exactMatch
        elif len(res) == 1:
            found = res[0]
        else:
            return "{} modules found matching that name, and no exact match: ".format(len(res)) + ', '.join([x['name'] for x in res])
        return printHandler(found, 'modules')
    else:
        return "No modules found matching that name."

def search(args):
    if args == ['nick']:
        return "We Are All nick"
    res = 'search results: '
    try:
        names = wikiSearch.quickSearch(''.join([x for x in ' '.join(args) if x != '\\']))
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
        return 'Error: uh... something. An error RO hasn\'t thought of came up, let him know this happened and He\'ll account for it.'
    res += names
    return res

def pvp(args):
    argDict = {'attack': "Customer attack works similar to quests, only you take the square root of the item's value, rounded down (their level has an associated value too). This contributes to a category, fighters, rogues, or spellcasters, based on the customer's class, and can be boosted by your town's walls.",
               'krown': "Krowns are a currency you get from klash, For reaching certain attack totals, you get 5 krowns each. 100 krowns is the max reward per klash, which takes 24k attack. Krowns can be spent opening chests, which contain either rare resources or special items.",
               'krowns': "Krowns are a currency you get from klash, For reaching certain attack totals, you get 5 krowns each. 100 krowns is the max reward per klash, which takes 24k attack. Krowns can be spent opening chests, which contain either rare resources or special items.",
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
        return "Free world trade is active! Trader's guilds level {} and up can use it, {} left. Upcoming FWTs for levels-  2 (1st of the month): {}; 3 (+15th): {}; 4 (+sunday): {}.".format(tier, ttxt0, ttxt1, ttxt2, ttxt3).replace("u", "ü").replace("U", "Ü")
    else:
        return "Next free world trade days for trader's guild level- 2 (1st of the month): {}; 3 (+15th): {}; 4 (+sunday): {}.".format(ttxt1, ttxt2, ttxt3).replace("u", "ü").replace("U", "Ü")

def loginDeadline():
    timeLeft = getTimeToMidnight()
    return "{} left for everyone to log in.".format(timeTextConverter(timeLeft, False))

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
    return "Here's the edgebee wiki for snp2: http://tinyurl.com/altWiki"
# http://www.edgebee.com/wiki/index.php?title=Swords_%26_Potions_2

def bwiki():
    return "Here's the backup wiki: http://tinyurl.com/altWiki"

def refresh():
    return "Refreshing fixes 99% of bugs/glitches in this game. When in doubt, refresh!"

def acidBin():
    return "Acid is a rare resource, there's no bin for it. You get it from quests, the daily spin, or krown chests (but don't spend krowns on it lol)."

def wtFodder():
    theItems = [
        "dryad staff", # staff
        "magic scroll", # scroll
        "dagger", # dagger
        "crushing bludgeon", # mace
        "scale mail", # heavy armor
        "ranseur", # spear
        "iron bracers", # bracers
        "gambeson", # light armor
        "kite shield", # shields
        "long sword", # swords
        "fine gauntlets", # gauntlets
        "dragon", # gun
        "priest's mark", # amulet
        "reactive ring", # ring
        "pole-axe", # axe
                ]
    return "Items that can generally be sold at or near max on wt: " + ", ".join(theItems)

def eightBall(q):
    resps = [
        "I dunno, ask nick",
        "signs point to yes",
        "my sources say no",
        "try again later",
        "lol",
        "probly",
        "probly not",
        "definitely",
        "absolutely not",
        "maybe?",
    ]
    i = random.randint(0, len(resps)-1)
    return resps[i]

def bunnyCuddle():
    return "very well then, you have been cuddled by a bunny"

def donate():
    return "I am a project that RO maintains in his free time, and he will certainly keep me running for as long as snp2 is running, regardless of monetary support. However, if you would like to help him out, feel free to donate at paypal.me/revelationorange or, if you prefer it for some reason, donate to his paypal at revelationorange@gmail.com"

def getRandomBuilding(t):
    # for t in seconds, get a random building that can be completed in that time (limit pool to n=10 longest times)
    hrs = int(t/60./60.)
    if hrs < 8:
        return 0
    else:
        n = 10
        searchText = "buildings, time: at most {} over 0".format(hrs)
        res = wikiSearch.quickSearch(searchText, False)
        rngList = []
        for r in res:
            if 'time' in r:
                rngList.append(r)
        srngList = sorted(rngList, key=lambda x: x['time'], reverse=True)
        i = random.randint(0, n-1)%len(srngList)
        return srngList[i]

def timeToClosing():
    ttc = getTimeToClosing()
    text = timeTextConverter(ttc, False)
    b = getRandomBuilding(ttc)
    baseText = "Time left until snp2 is gone: {}.".format(text)
    if b:
        baseText += " Still enough time to finish {} level {}!".format(b['name'], b['level'])
    return baseText

optAssocs = {info: ['info'], help: ['help'], search: ['search'], item: ['item', 'items'], pvp: ['pvp', 'klash'],
             wiki: ['wiki'], hinder: ['hinder'], stopHinder: ['stophinder'], building: ['building', 'buildings'],
             sheets: ['sheet', 'sheets', 'spreadsheets'], customer: ['cust', 'custs', 'customer', 'customers'],
             gettingStarted: ['gs', 'gettingstarted'], quest: ['quest', 'quests'],
             fwt: ['fwt', 'fwtd', 'freeworldtrade', 'freeworldtradeday'], cmd: ['cmds', 'cmd', 'commands', 'command'],
             bwiki: ['bwiki', 'backupwiki', 'archivewiki', 'altwiki'], eightBall: ['8ball'],
             loginDeadline: ['ld', 'dl', 'deadline', 'logindeadline'], refresh: ['refresh', 'reload'],
             worker: ['worker', 'workers'], wtFodder: ['wtfodder', 'wtitems', '900'], acidBin: ['acidbin'],
             module: ['module', 'shopitem', 'shop', 'mod'], bunnyCuddle: ['bunnycuddle', 'bunnycuddles'],
             donate: ['donate', 'support'], timeToClosing: ['closingtime', 'shutdown', 'snp2death']}

optionDict = {}
for fxn in optAssocs:
    for key in optAssocs[fxn]:
        optionDict[key] = fxn

# optionDict = {'info':info, 'help':help, 'search':search, 'item':item, 'pvp':pvp, 'klash':pvp,
#               'submittownad':submitTownAd, 'removetownad':removeTownAd, 'hinder':hinder, 'stophinder':stopHinder,
#               'sheets':sheets, 'spreadsheets':sheets, 'building':building, 'customer':customer, 'cust':customer,
#               'gettingstarted':gettingStarted, 'gs':gettingStarted, 'quest':quest, 'fwt':fwt, 'fwtd':fwt,
#               'freeworldtrade':fwt, 'freeworldtradeday':fwt, 'wiki':wiki, 'cmd':cmd, 'cmds':cmd, 'commands':cmd,
#               'commandlist':cmd, 'deadline': loginDeadline, 'logindeadline': loginDeadline, 'ld': loginDeadline,
#               'sheet': sheets}
noArgFxns = [info, hinder, sheets, gettingStarted, fwt, wiki, cmd, loginDeadline, refresh, bwiki, wtFodder, acidBin, bunnyCuddle, donate, timeToClosing]
pubFxns = {wiki: 'wiki', bwiki:'bwiki', sheets:'sheets', gettingStarted:'gs', refresh:'refresh', wtFodder: 'wtfodder', timeToClosing: 'snp2death'}
usrFxns = ['submittownad', 'removetownad']
pmOnly = []
hinderRNG = ['info', 'help', 'search', 'item', 'pvp', 'hinder', 'sheets', 'building', 'cust', 'gs', 'quest', 'acidbin',
             '8ball', 'bwiki', 'ld', 'worker', 'gtw', 'bunnycuddle', '']
optionDictAdmin = ['say', 'msgs', 'yay']
knarfResponses = [
    'In loving memory of knarfbot, may its bucket be ever full',
    'rip knarfbot o7',
    'in knarfbot we trust',
    "knarf's bucket has been pooped, but it shall live on in our hearts",
]
def getKnarfResp():
    i = random.randint(0, len(knarfResponses)-1)
    return knarfResponses[i]

def isPub(fxnName):
    chk = fxnName[1:] if fxnName[0] == '!' else fxnName
    if chk in optionDict and optionDict[chk] in pubFxns:
        return pubFxns[optionDict[chk]]
    else:
        return False

grpMsgRepl = "<message to='174726-swords-and-potions-2-1@conference.of1.kongregate.com' from='snp2_RObot@of1.kongregate.com/xiff' type='groupchat' id='dc96ae0e-27ec-40e5-83f2-b4a013d5ec0a' xmlns='jabber:client'><body>{}</body><x xmlns='jabber:x:event'><composing/></x></message>"

def handler(fxnRaw, usr, args):
    fxnName = fxnRaw.lower()
    if fxnName in optionDict:
        fxn = optionDict[fxnName]
        if fxn in noArgFxns:
            message = fxn()
            # return optionDict[fxn](usr)
        elif fxn in usrFxns:
            message = fxn(usr, args)
        else:
            message = fxn(args)
            # return optionDict[fxn](usr, args)
        msgs = msgChopper(message)
        outs = []
        for m in msgs:
            outReq = formulateResponse(m, usr)
            outs.append(outReq)
        return (outs, msgs)
    else:
        tmpmsg = optionDict['item']([fxnRaw] + args)
        if 'Error:' in tmpmsg or 'No items found matching that name.' == tmpmsg:
            message = "That's not a recognized/implemented command (may be Coming Soon™). Use !help for more info."
            msgs = msgChopper(message)
        else:
            msgs = msgChopper(tmpmsg)
        outs = []
        for m in msgs:
            outReq = formulateResponse(m, usr)
            outs.append(outReq)
        return (outs, msgs)
