#!/usr/bin/env python
# -*- coding: utf-8 -*-

''''''

"""
    TestBot: a QuickBlox compatible chat bot.
    This is a basic chat bot code that works in both 1:1 and MUC chat environments.
    Can be used for adding automated agents into QuickBlox powered apps. Typical use cases include testing, moderation, customer support, trivia/quiz games etc.
    All custom and QuickBlox related code copyright (C) 2014 Taras Filatov, Igor Khomenko and QuickBlox.
    Based on the code from SleekXMPP project by Nathanael C. Fritz. (C) 2010.
    Distributed under Apache 2.0 open source license. See the file LICENSE for copying permission including bundled 3rd party codes.
"""

'''
base code:
credit to qndel for getting this started, pointing me to the right examples, and showing me how to deal with xmpp messages
(the base structure is from the sleekxmpp echobot example, the muc code is from another sleekxmpp example)


'''

import sys
import logging
import getpass
import os
import time
import RObotLib
from optparse import OptionParser
import sleekxmpp
from sleekxmpp.xmlstream import ET,handler,matcher
import subprocess
import codecs
from termcolor import colored as color
from numpy import random as rng

"""
   IMPORTANT: for MUC auto-join to work, change these to your own script path and QuickBlox credentials.
   Also make sure you made this script executable (chmod -x testbot.py).
"""


selfPath = os.path.realpath(__file__)

user_jid = 'snp2_robot@of1.kongregate.com'
user_password = '{"k":"33117572_018e30119cce763e32b81ffa247d094e01f8aec0"}'
room_jid = "174726-swords-and-potions-2-1@conference.of1.kongregate.com"
room_nick = "snp2_RObot"

chatlogFilename = 'logs' + os.sep + time.strftime('%m.%d.%Y.txt')
bunnylogFilename = 'logs' + os.sep + 'bunnycuddles.txt'
mindyAltsFilename = 'logs' + os.sep + 'mindyAlts.txt'

pmColor = 'red'
counter = 0

# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    raw_input = input

def canIntConvert(x):
    # just a convenience, so a string can be checked if it's an int without crashing
    try:
        int(x)
        return True
    except:
        return False

class MUCBot(sleekxmpp.ClientXMPP):
    """
    A simple SleekXMPP bot that will greet those
    who enter the room, and acknowledge any messages
    that mention the bot's nickname.
    """

    def __init__(self, jid, password, room, nick, logfilename='', repliesEnabled=False, bunnyLog=''):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.room = room
        self.nick = nick
        self.logFilename = logfilename
        self.canReply = repliesEnabled
        self.grpMsgTimer = 0
        self.pbTimer = 0
        self.pmCmdTimers = {}
        self.hinderances = {}
        self.bunnylogFilename = bunnyLog
        self.yays = []
        self.yayCooldown = 0
        self.startTime = time.time()
        self.sheetsCooldown = 0

        # The session_start event will be triggered when
        # the bot establishes its connection with the server
        # and the XML streams are ready for use. We want to
        # listen for this event so that we we can initialize
        # our roster.
        self.add_event_handler("session_start", self.start)

        # The groupchat_message event is triggered whenever a message
        # stanza is received from any chat room. If you also also
        # register a handler for the 'message' event, MUC messages
        # will be processed by both handlers.
        self.add_event_handler("groupchat_message", self.muc_message)

        # The message event is triggered whenever a message
        # stanza is received. Be aware that that includes
        # MUC messages and error messages.
        self.add_event_handler("message", self.message)

        # The groupchat_presence event is triggered whenever a
        # presence stanza is received from any chat room, including
        # any presences you send yourself. To limit event handling
        # to a single room, use the events muc::room@server::presence,
        # muc::room@server::got_online, or muc::room@server::got_offline.
        self.add_event_handler("muc::%s::presence" % self.room, self.muc_online)

        # event handler for private messages
        # credit to qndel for this line
        self.register_handler(sleekxmpp.xmlstream.handler.callback.Callback('PrivateHandler', sleekxmpp.xmlstream.matcher.xpath.MatchXPath('{%s}iq/{%s}query' % ( self.default_ns, "kongregate:iq:msg")), self.privateMessage))

    def handlePM(self, msgBody, usr):
        if self.canReply:
            if usr not in self.pmCmdTimers or time.time() - self.pmCmdTimers[usr] > 3.:
                inputs = msgBody.split(' ')
                if usr in self.hinderances and self.hinderances[usr]:
                    if inputs[0][1:] not in ['stopHinder', 'stophinder']:
                        self.hinderances[usr] -= 1
                        inputs[0] = '!' + rng.choice(RObotLib.hinderRNG)
                else:
                    if inputs[0][1:] in ['stopHinder', 'stophinder']:
                        inputs = ['!stophinder', 'err']
                handled = RObotLib.handler(inputs[0][1:], usr, inputs[1:])
                if handled is not None:
                    if inputs[0][1:] == 'hinder':
                        if len(inputs) > 1 and canIntConvert(inputs[1]):
                            nRands = inputs[1]
                        else:
                            nRands = rng.randint(1,5+1)
                        self.hinderances[usr] = nRands
                    elif inputs[0][1:] in ['stopHinder', 'stophinder']:
                        self.hinderances[usr] = 0
                    responses, replyMsgs = handled
                    for i in range(len(responses)):
                        time.sleep(1.2)
                        print(color('PM TO {}: {}'.format(usr, replyMsgs[i]), pmColor))
                        if self.logFilename:
                            with codecs.open(self.logFilename, 'a', 'utf-8') as lf:
                                lf.write('pm to,{},{},{}\n'.format(usr, time.time(), replyMsgs[i]))
                        self.send_raw(responses[i])
                    self.pmCmdTimers[usr] = time.time()
                else:
                    print(color('got past checkForCommands, but handler returned None', 'yellow'))
                    print(color(msgBody, 'yellow'), usr)

    def privateMessage(self, msg):
        m = str(msg)
        tmp = RObotLib.decryptPM(m)
        if tmp is not None:
            msgText, sendTo = tmp
            if self.logFilename:
                with codecs.open(self.logFilename, 'a', 'utf-8') as lf:
                    lf.write('pm from,{},{},{}\n'.format(sendTo,time.time(),msgText))
            print(color('PM FROM {}: {}'.format(sendTo, msgText), pmColor))
            msgBody = checkForCommands(msgText)
            if msgBody and sendTo != 'RevelationOrange':
                self.handlePM(msgBody, sendTo)
            elif msgText == 'help':
                self.handlePM('!'+msgText, sendTo)
            elif sendTo == 'RevelationOrange':
                inputs = msgBody.split(' ')
                if inputs[0] == '!say':
                    chatTxt = ' '.join(inputs[1:])
                    resprepl = "<message to='174726-swords-and-potions-2-1@conference.of1.kongregate.com' from='snp2_RObot@of1.kongregate.com/xiff' type='groupchat' id='dc96ae0e-27ec-40e5-83f2-b4a013d5ec0a' xmlns='jabber:client'><body>{}</body><x xmlns='jabber:x:event'><composing/></x></message>"
                    resp = resprepl.format(chatTxt)
                    print(chatTxt)
                    print(resp)
                    xmpp.send_raw(resp)
                elif inputs[0] == '!msgs':
                    print(self.pmCmdTimers)
                elif inputs[0] == '!yay':
                    for y in self.yays:
                        print(time.ctime(y))
                    resp = RObotLib.formulateResponse('yay!™', sendTo)
                    if self.logFilename:
                        with codecs.open(self.logFilename, 'a', 'utf-8') as lf:
                            lf.write('pm to,{},{},{}\n'.format(sendTo, time.time(), 'yay!™'))
                    print(color('PM TO {}: {}'.format(sendTo, 'yay!™'), pmColor))
                    xmpp.send_raw(resp)
                elif inputs[0] == '!hinders':
                    for x in self.hinderances:
                        print(color('{}: {}'.format(x, self.hinderances[x]), 'blue'))
                elif inputs[0] == '!ads':
                    for ad in RObotLib.townAdsList:
                        print(color(ad, 'green'))
                else:
                    rMsg = '[construction zone]'
                    resp = RObotLib.formulateResponse(rMsg, sendTo)
                    if self.logFilename:
                        with codecs.open(self.logFilename, 'a', 'utf-8') as lf:
                            lf.write('pm to,{},{},{}\n'.format(sendTo, time.time(), rMsg))
                    xmpp.send_raw(resp)

    def start(self, event):
        """
        Process the session_start event.
        Typical actions for the session_start event are
        requesting the roster and broadcasting an initial
        presence stanza.
        Arguments:
            event -- An empty dictionary. The session_start
                     event does not provide any additional
                     data.
        """
        if self.logFilename:
            with codecs.open(self.logFilename, 'a', 'utf-8') as lf:
                lf.write('\nsession start,{},{}\n'.format(self.nick,time.time()))
        self.get_roster()
        self.send_presence()
        self.plugin['xep_0045'].joinMUC(self.room,
                                        self.nick,
                                        maxhistory="1",
                                        # If a room password is needed, use:
                                        # password=the_room_password,
                                        wait=True)
        xmpp.send_raw("<iq type='set' id='_bind_auth_2' xmlns='jabber:client'><bind xmlns='urn:ietf:params:xml:ns:xmpp-bind'><resource>xiff</resource></bind></iq>")
        xmpp.send_raw("<iq type='set' id='_session_auth_2' xmlns='jabber:client'><session xmlns='urn:ietf:params:xml:ns:xmpp-session'/></iq>")
        xmpp.send_raw("<presence xmlns='jabber:client'><show>chat</show></presence>")
        xmpp.send_raw("<presence from='snp2_robot@of1.kongregate.com/xiff' to='174726-swords-and-potions-2-1@conference.of1.kongregate.com/snp2_RObot' xmlns='jabber:client'><x xmlns='http://jabber.org/protocol/muc'><history seconds='60'/></x><status>[&quot;s7q60PSIczJlH0n8jGQXdw==&quot;,&quot;[\&quot;snp2_RObot\&quot;,\&quot;\&quot;,1,\&quot;cdn4:/assets/avatars/defaults/wrestleboy.png?i10c=img.resize(width:16)\&quot;,\&quot;Swords \\\\u0026 Potions 2\&quot;,\&quot;/games/EdgebeeStudios/swords-and-potions-2\&quot;,[],[]]&quot;,{&quot;special_chat_vars&quot;:&quot;{}&quot;}]</status></presence>")

    def message(self, msg):
        """
        [ 1:1 CHATS. In this section we handle private (1:1) chat messages received by our bot. These may include system messages such as MUC invitations. ]
        """

        """
        1:1 message test auto-reply
        Uncomment the code lines below to make chat bot reply to any incoming 1:1 chat messages by quoting them
        """

        """
        if msg['type'] in ('chat', 'normal'):
            msg.reply("Thanks for sending\n%(body)s" % msg).send()
        #"""

        """
        MUC auto-join:
        Let's listen for any MUC invites and join the corresponding MUC rooms once invited.
        """

        """if msg['mucnick'] != self.nick and "created a group" in msg['body']:"""
        '''
        if msg['mucnick'] != self.nick and "Create new chat" in msg['body']:
            from bs4 import BeautifulSoup
            y = BeautifulSoup(str(msg))
            roomToJoin = y.xmpp_room_jid.string
            print("Got an invite to join room")
            """os.system(selfPath + " -d -j " + qbChatLogin + " -r " + str(roomToJoin) + " -n " + qbChatNick + " -p " + qbUserPass)"""
            """subprocess.call(selfPath + " -d -j " + qbChatLogin + " -r " + str(roomToJoin) + " -n " + qbChatNick + " -p " + qbUserPass, shell=True)"""
            botId = subprocess.Popen([selfPath + " -d -j " + qbChatLogin + " -r " + str(
                roomToJoin) + " -n " + qbChatNick + " -p " + qbUserPass], shell=True)
            print("spawned new bot ID=")
            print(botId)

            self.send_message(mto=msg['from'].bare,
                              mbody="Thank you for your kind invitation, joining your new room now!",
                              mtype='groupchat')
        '''

    def muc_message(self, msg):
        if time.time()-self.startTime > 3.2:
            delayTime = 1.0
            grpAndPBcooldown = 15. # minutes
            print(msg['mucnick']+':', msg['body'])
            if self.logFilename:
                with codecs.open(self.logFilename, 'a', 'utf-8') as lf:
                    lf.write('{},{},{}\n'.format(msg['mucnick'],time.time(),msg['body']))
            if msg['mucnick'] == 'ChevetteGirl':
                if '<' in msg['body'] or '>' in msg['body']:
                    if 'bunnycuddle' in msg['body'] or 'bunny cuddle' in msg['body']:
                        if self.bunnylogFilename:
                            with codecs.open(self.bunnylogFilename, 'a', 'utf-8') as lf:
                                lf.write('bunnycuddle,{},{}\n'.format(time.time(), msg['body']))
            pbMatch = 'item: poop bucket'
            yayTxt0 = 'yay!™'
            yayTxt1 = 'yay!'
            sheetsTxt = ['!sheets', '!spreadsheets']
            sheetsMsg = "Here's the list of spreadsheets: bit.ly/snp2_sheets"
            if msg['body'][:len(pbMatch)] == pbMatch:
                if time.time() - self.pbTimer >= grpAndPBcooldown * 60.:
                    pbResponse = RObotLib.getKnarfResp()
                    resp = RObotLib.grpMsgRepl.format(pbResponse)
                    time.sleep(delayTime)
                    xmpp.send_raw(resp)
                    self.pbTimer = time.time()
            elif msg['body'][:len(yayTxt1)] == yayTxt1 and msg['mucnick'] not in [x[0] for x in RObotLib.mindyAltsList if x[1] == 'known']:
                if time.time() - self.yayCooldown >= grpAndPBcooldown * 60.:
                    self.yays.append(time.time())
                    if len(self.yays) > 1 and time.time() - self.yays[-2] <= 20.:
                        self.yays = []
                        resp = RObotLib.grpMsgRepl.format(yayTxt0)
                        time.sleep(delayTime)
                        xmpp.send_raw(resp)
                        self.yayCooldown = time.time()
            elif msg['body'] in sheetsTxt:
                if time.time() - self.sheetsCooldown >= grpAndPBcooldown * 60.:
                    resp = RObotLib.grpMsgRepl.format(sheetsMsg)
                    time.sleep(delayTime)
                    xmpp.send_raw(resp)
                    self.sheetsCooldown = time.time()
                else:
                    msgBody = checkForCommands(msg['body'], 'public')
                    if msgBody:
                        self.handlePM(msgBody, msg['mucnick'])
            else:
                msgBody = checkForCommands(msg['body'], 'public')
                if msgBody:
                    self.handlePM(msgBody, msg['mucnick'])

    def muc_online(self, presence):
        """
        Process a presence stanza from a chat room. In this case,
        presences from users that have just come online are
        handled by sending a welcome message that includes
        the user's nickname and role in the room.
        Arguments:
            presence -- The received presence stanza. See the
                        documentation for the Presence stanza
                        to see how else it may be used.
        """

        '''
        if presence['muc']['nick'] != self.nick:
            self.send_message(mto=presence['from'].bare,
                              mbody="Hello, %s %s" % (presence['muc']['role'],
                                                      presence['muc']['nick']),
                              mtype='groupchat')
        '''

    def copy_dialog_id(self, origin_message, new_message):
        """
        Copy a dialog_id from a received message to a replay message
        """
        dialog_id_in = origin_message.xml.find('{jabber:client}extraParams/{jabber:client}dialog_id')

        if dialog_id_in is not None:
            extra_params_out = ET.Element('{jabber:client}extraParams')
            dialog_id_out = ET.Element('{}dialog_id')
            dialog_id_out.text = dialog_id_in.text
            extra_params_out.append(dialog_id_out)
            new_message.append(extra_params_out)

def checkForCommands(m, source='pm'):
    msgSplit = m.split(' ')
    while len(msgSplit) and not msgSplit[0]:
        msgSplit.pop(0)
    if msgSplit:
        if len(msgSplit[0]) > 1:
            if msgSplit[0][0] == '!' and msgSplit[0][1] not in ['!', ':']:
                if msgSplit[0][-1] == ':':
                    msgSplit[0] = msgSplit[0][:-1]
                if source == 'pm' or msgSplit[0][1:].lower() not in RObotLib.pmOnly:
                    return ' '.join(msgSplit)
            if msgSplit[0][-1] == ':':
                if msgSplit[0][:-1].lower() in RObotLib.optionDict:
                    return ' '.join(['!'+msgSplit[0][:-1]]+msgSplit[1:])

if __name__ == '__main__':

    try:
        from local_settings import *
    except ImportError:
        print("No custom config found, use default settings")
    else:
        print("Use custom settings")

    # Setup the command line arguments.
    optp = OptionParser()

    # Output verbosity options.
    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=logging.INFO)

    # JID and password options.
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")
    optp.add_option("-r", "--room", dest="room",
                    help="MUC room to join")
    optp.add_option("-n", "--nick", dest="nick",
                    help="MUC nickname")

    opts, args = optp.parse_args()

    # Setup logging.
    # opts.loglevel = logging.DEBUG
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    if opts.jid is not None:
        user_jid = opts.jid
    if user_jid is None:
        user_jid = raw_input("Username: ")

    if opts.password is not None:
        user_password = opts.password
    if user_password is None:
        user_password = getpass.getpass("Password: ")

    if opts.room is not None:
        room_jid = opts.room
    if room_jid is None:
        room_jid = raw_input("MUC room: ")

    if opts.nick is not None:
        room_nick = opts.nick
    if room_nick is None:
        room_nick = raw_input("MUC nickname: ")

    print("initial jid: " + user_jid)
    print("initial password: " + user_password)
    print("initial room: " + room_jid)
    print("initial nick: " + room_nick)

    # Setup the MUCBot and register plugins. Note that while plugins may
    # have interdependencies, the order in which you register them does
    # not matter.
    xmpp = MUCBot(user_jid, user_password, room_jid, room_nick, chatlogFilename, True, bunnylogFilename)
    xmpp.register_plugin('xep_0030')  # Service Discovery
    xmpp.register_plugin('xep_0045')  # Multi-User Chat
    xmpp.register_plugin('xep_0199')  # XMPP Ping

    # Connect to the XMPP server and start processing XMPP stanzas.
    xmpp['feature_mechanisms'].unencrypted_plain = True
    if xmpp.connect(use_tls=False):
        # If you do not have the dnspython library installed, you will need
        # to manually specify the name of the server if it does not match
        # the one in the JID. For example, to use Google Talk you would
        # need to use:
        #
        # if xmpp.connect(('talk.google.com', 5222)):
        #     ...
        xmpp.process(block=True)
        print("Done")
    else:
        print("Unable to connect.")
