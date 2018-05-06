from termcolor import colored
import time
from calendar import timegm
import datetime
import codecs
from numpy import random as rng
from string import capwords


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    COLDICT = {'HEADER' : '\033[95m', 'OKBLUE': '\033[94m', 'OKGREEN' : '\033[92m', 'WARNING' : '\033[93m',
               'FAIL' : '\033[91m', 'ENDC' : '\033[0m', 'BOLD' : '\033[1m', 'UNDERLINE' : '\033[4m'}

def msgChopper(m):
    lenLim = 248
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

def getNextFWTD(offset=0):
    sundayNum = 6
    currentGMT = time.gmtime(time.time() + offset)
    tomorrowMidnight = [x for x in time.gmtime(time.time() + offset + 86400.)]
    tomorrowMidnight[3:6] = 0,0,0
    if currentGMT[2] == 1:
        fwtdTier = 1
    elif currentGMT[2] == 15:
        fwtdTier = 2
    elif currentGMT[6] == sundayNum:
        fwtdTier = 3
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
    return (fwtdTier, timeLeft, nxtTier1, nxtTier2, nxtTier3)

from RObotLib import timeTextConverter,getNextFWTD
def fwtAnnounce(sim=0):
    if sim:
        tier, timeLeft, nxt1, nxt15, nxtSun = sim
    else:
        tier, timeLeft, nxt1, nxt15, nxtSun = getNextFWTD()
    if tier:
        # announce time remaining every 3 hours (use cooldown + range), and a warning half-hour before it ends
        if timeLeft > ((24 * 60) - 5) * 60. and timeLeft <= 24 * 60 * 60.:
            txt = ("Happy free world trade day! (trader's guild level {})".format(tier))
        elif timeLeft > (31 - 5) * 60. and timeLeft <= (31) * 60.:
            txt = ("FWT is almost over! {} left.".format(timeTextConverter(timeLeft, False)))
        else:
            hrs = timeLeft / 3600.
            hrsApprox = round(hrs)
            if not hrsApprox % 3 and abs(hrs - hrsApprox) * 60 < 2:
                txt = ("FWT active, ~{} hours left.".format(hrsApprox))
            else:
                txt = 0
        if txt:
            print(txt)
    else:
        # print(tier, timeLeft, nxtSun)
        nearest = min(nxt1, nxt15, nxtSun)
        if nearest > (31 - 5) * 60. and nearest <= (31) * 60.:
            # announce ~30 minutes until it starts
            txt = ("A free world trade day will be starting in {}!".format(timeTextConverter(nearest, False)))
            print(txt)

from RObotLib import getTimeToMidnight,getNextFWTD, timeTextConverter
(fwtdTier, timeLeft, nxtTier1, nxtTier2, nxtTier3) = getNextFWTD()
print(timeTextConverter(nxtTier1, False), timeTextConverter(nxtTier2, False), timeTextConverter(nxtTier3, False))
from RObotLib import MIME
s = "c25wMl9yb2JvdEBvZjEua29uZ3JlZ2F0ZS5jb20Ac25wMl9yb2JvdAB7ImsiOiIzMzExNzU3Ml83NGNiNmM5NjNhZTBlYjUxMmIzZjJjODVlMmIxOTgzMzgwYTU4Y2JhIn0="
print(MIME(s,False))
s0 = "74cb6c963ae0eb512b3f2c85e2b1983380a58cba"
print(MIME(s0,False))
def isKap(x):
    xsqStr = str(x**2)
    lx = len(str(x))
    r = xsqStr[-lx:]
    rem = len(xsqStr)-len(r)
    if rem:
        l = int(xsqStr[:rem])
        return int(r)+l == x
    else:
        return int(r) == x

kaps = []
for i in range(1,30+1):
    x = 10**i - 1
    if isKap(x):
        kaps.append(i)
s = [3,4,5]
inv = 0
for i in range(len(s)):
    for j in range(i+1, len(s)):
        print(s[i], s[j])