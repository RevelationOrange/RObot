from base64 import b64encode,b64decode
import wikiSearch
from numpy.random import choice as rngChoice
from os import sep
from string import capwords


def MIME(s, encrypt=True):
    # print(s)
    if encrypt:
        txt = b64encode(bytes(s, 'utf8'))
    else:
        txt = b64decode(bytes(s, 'utf8'))
    return str(txt)[2:-1]

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

lenLim = 248
def msgChopper(m):
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
        'help': "Ha ha, very funny. This command just displays info about me and my commands, and it's no more complicated than !help [command]. Without the [] of course.",
        'info': "This is just some info about me, author stuff, that kind of thing.",
        'search': "This is a flexible search function you can use to get lists of items, customers, buildings, shop stuff, quests, workers, achievements, and classes based on the criteria you enter. The format is: [section], [attribute]: [critera]. You can use as many attribute: criteria parts as you like, just separate them with commas. Example: items, level: range 5 10, price: over 2000",
        'item': "Display info about an item. If you use a partial item name, and there is more than one match but it is isn't an exact match (ex: knife will return info on knife, not survival knife), it will give you a list of items found. (the info displayed isn't exhaustive, I'll be working on a way to do that in a pm)",
    }
    if not args:
        return 'Hello! I don\'t have much functionality yet, my only commands are !help, !info, !item, and !search, but that should be changing soon! For more info on each command, use !help [command]. There is a 3 second timer on commands.'
    else:
        if args[0] in helpTexts or args[0][1:] in helpTexts:
            return helpTexts[args[0]]
        else:
            return "I don't recognize the command you entered. When using !help [command], don't include the []"

def info():
    return 'The skeleton for this chatbot was done by qndel (getting it actually connected to kong), everything else was written by RevelationOrange, in python 3.5.2'

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
            return 'More than one item found matching that name, and no exact match: ' + ', '.join([x['name'] for x in res])
        else:
            found = res[0]
            print('single result partial match')
        if found['type'] == 'rare resources':
            infoRepl = '{name}, lvl {level} ({type}). {value:,} gold.'
            if found['nfRecs'] != '--':
                infoRepl += ' Precraft for: {}.'.format(', '.join([x for x in found['nfRecs']]))
            message = infoRepl.format(**found)
            return message
        else:
            infoRepl = '{name}, lvl {level} ({type}). {value:,} gold, {ctText} craft time. Uses: {ingrs}, made by {madeBy} on {station}. Unlocked by {unlckBy}, Unlocks {unlcks}.'
            tmp = {}
            tmp['name'] = capwords(found['name'])
            tmp['ctText'] = found['craftTime'].lower()
            tmp['ingrs'] = ', '.join([' '.join([str(y) for y in x]) for x in found['ingredients']])
            tmp['station'] = ' '.join([capwords(str(x)) for x in found['madeOn']])
            tmp['unlckBy'] = '(starter recipe)' if not found['prevItem'] else found['prevItem'][0] if len(found['prevItem']) == 1 else '{} ({})'.format(*found['prevItem'])
            if found['nextItem'] == [['--']]:
                tmp['unlcks'] = '--'
            else:
                tmp['unlcks'] = ', '.join([capwords('{} ({})'.format(*x)) for x in found['nextItem']])
            if found['nfRecs'] != '--':
                infoRepl += ' Precraft for: {}.'.format(', '.join([x for x in found['nfRecs']]))
            if found['nfQuests'] != ['--']:
                infoRepl += ' Used in quests: {}.'.format(', '.join(found['nfQuests']))
            if found['nfBuilds'] != ['--']:
                infoRepl += ' Needed for buildings: {}'.format(', '.join(['{} {} ({})'.format(*x) for x in found['nfBuilds']]))
            found.update(tmp)
            message = infoRepl.format(**found)
            return message
    else:
        return 'No items found matching that name.'

def search(args):
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
    if len(res) > lenLim*3:
        res = 'too many search results (more than 3 messages worth), please narrow your search'
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

optionDict = {'info':info, 'help':help, 'search':search, 'item':item, 'mindyalts':mindyAlts,
              'submittownad':submitTownAd, 'removetownad':removeTownAd}
optionDictAdmin = ['say', 'msgs', 'yay']
knarfResponses = [
    'In loving memory of knarfbot, may its bucket be ever full',
    'rip knarfbot o7',
    'in knarfbot we trust',
    "knarf's bucket has been pooped, but it shall live on in our hearts",
]
def getKnarfResp():
    return rngChoice(knarfResponses)
plzPMmsg0 = "Please keep requests to whispers! Use !help if you don't know the commands. (item: is not a command, !item is)"
plzPMmsg1 = "Please keep requests to whispers! Use !help if you don't know the commands."
grpMsgRepl = "<message to='174726-swords-and-potions-2-1@conference.of1.kongregate.com' from='snp2_RObot@of1.kongregate.com/xiff' type='groupchat' id='dc96ae0e-27ec-40e5-83f2-b4a013d5ec0a' xmlns='jabber:client'><body>{}</body><x xmlns='jabber:x:event'><composing/></x></message>"

def handler(fxnRaw, usr, args):
    fxn = fxnRaw.lower()
    if fxn in optionDict:
        if fxn in ['info', 'mindyalts']:
            message = optionDict[fxn]()
            # return optionDict[fxn](usr)
        elif fxn in ['submittownad', 'removetownad']:
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
