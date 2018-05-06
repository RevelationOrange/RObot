import os
import time
import codecs


logfolder = "logs"
exceptionList = ['bunnycuddles.txt', 'testLog.txt']
chk = '10.30.2017.txt'

searchTerm = 'hehe'.lower()
usrs = ['ChevetteGirl']
for fn in os.listdir(logfolder):
    if fn not in exceptionList:
        lfl = []
        print(fn)
        with codecs.open(os.sep.join((logfolder, fn)), 'r', 'utf-8') as logFile:
            for line in logFile:
                if len(line) > 1:
                    l = line[:-1].split(',')
                    # print(l)
                    if l[0] == 'session start':
                        # print('{}, {}'.format(l[0], time.strftime("%X", time.localtime(float(l[2])))))
                        pass
                    else:
                        pmfix = ''
                        if l[0] in ['pm from', 'pm to']:
                            pmfix = l.pop(0)
                        # print(l)
                        try:
                            usr, t, msg = l[0], float(l[1]), ','.join(l[2:])
                        except:
                            lfl[-1][2] += ','.join(l)
                            continue
                        usr, t, msg = l[0], float(l[1]), ','.join(l[2:])
                        if pmfix:
                            usr = pmfix + ' ' + usr
                        # print("{}  {}: {}".format(time.strftime("%X",time.localtime(t)), usr, msg))
                        lfl.append([t, usr, msg])
        for i in range(len(lfl)):
            line = lfl[i]
            # t, usr, msg = line
            if line[1] in usrs and searchTerm in line[2].lower():
                for j in range(i-5, i+6):
                    if j < len(lfl):
                        t, usr, msg = lfl[j]
                        print("{}  {}: {}".format(time.strftime("%X", time.localtime(t)), usr, msg))
                print()
