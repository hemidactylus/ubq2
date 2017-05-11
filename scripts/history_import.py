'''
    history_import.py : utility to import the number-counter stat
    from the old 'UBQ' - by parsing the log files and their archives -
    it goes all to table 'stat_counterstatusspans'.
'''

import os
import sys
from datetime import datetime
import time
import subprocess

import env

from app.utils.cmdLineParse import cmdLineParse
from config import dbFullName
from app.database.dbtools import (
    dbOpenDatabase,
)
from app.database.dblogging import (
    logCounterStatusSpan,
    clearCounterStatusSpansTable,
)
from app.database.models import (
    CounterStatusSpan,
    CounterStatus,
)

# settings
importBaseDir=os.path.abspath(os.path.dirname(__file__))
tmpDir=os.path.join(importBaseDir,'history_import_tmp')
srcDir=os.path.join(importBaseDir,'history_import_data')

def collectFiles(startDir):
    '''
        builds recursively a list of all filenames of the tree
    '''
    oList=[os.path.join(startDir,f) for f in os.listdir(startDir)]
    return [
        itm
        for f in oList
        for itm in ([f] if os.path.isfile(f) else collectFiles(f))
    ]

def isLogFile(fName):
    '''
        returns True if the filename (here provided with its whole path)
        is that of a log file
    '''
    fTitle=os.path.split(fName)[1].lower()
    return fTitle[-4:]=='.log' \
        or fTitle.startswith('archived_cntlog') \
        or fTitle[-3:]=='.gz'

def extractEvents(fName,indent=2,tempDir=None):
    '''
        makes a log file into a list of counterid/datetime/number
        ready for merging, sorting and processing

        Most of the lines are discarded. Need only offline-statuses and newnumber-statuses such as:
            [ 05/05/17-09:33:18 | 1493969598 ] <EM1> nc nn 4
            [ 05/05/17-12:14:40 | 1493979280 ] <CC1> nc lo 84

        If the file is a gzipped archive, must extract its contents to the temp dir,
        collect the event list from all such files, clean the temp dir, return the whole list
    '''
    entryList=[]
    indSpacing='    '*indent
    fTitle=os.path.split(fName)[1]
    if fName[-3:]!='.gz':
        opener=lambda fName: open(fName).readlines()
        fileType='L'
        # regular log file
        print('%s[%s : %s ' % (indSpacing,fileType,fTitle), end='')
        for lNum,li in enumerate(opener(fName)):
            entry=parseLogEntry(li,fileName=fTitle,lineNumber=lNum+1)
            if entry:
                entryList.append(entry)
        print(' (%6i) ]' % len(entryList))
        return entryList
    else:
        fileType='G'
        print('%s[%s : %s ' % (indSpacing,fileType,fTitle))
        # extract to temp dir
        extractionOutcome=subprocess.call(['tar','-xf',fName,'-C',tempDir])
        for nFile in os.listdir(tempDir):
            fullNFile=os.path.join(tempDir,nFile)
            entryList+=extractEvents(fullNFile,indent+1,tempDir)
            os.remove(fullNFile)
        print('%s(%6i) ]' % (indSpacing,len(entryList)))
        return entryList

def parseLogEntry(line,fileName='N/A',lineNumber=-1):
    '''
        If the line is eligible for being a log entry,
        returns the parsed entry object, otherwise returns None
    '''
    REQUIRED_KEYS={'value','counterid'}
    DISPENSABLE_KEYS={'timestamp'}

    terms=list(filter(lambda a: a!='',map(lambda l: l.strip(),line.split(' '))))
    tstamp=terms[:5]
    message=terms[5:]
    #
    entry={}
    # timestamp
    if len(tstamp)==5:
        tStampIndex=1+list(filter(lambda p: p[1]=='|', enumerate(tstamp)))[0][0]
        entry['timestamp']=int(tstamp[tStampIndex])
    # message
    if len(message)>=4 and message[1]=='nc':
        if message[0][0]=='<' and message[0][-1]=='>':
            entry['counterid']=message[0][1:-1]
        if message[2]=='nn':
            # new regular number
            entry['value']=int(message[3])
        elif message[2]=='lo':
            # new 'offliene' status
            entry['value']=-1
    if not ((REQUIRED_KEYS|DISPENSABLE_KEYS)-entry.keys()):
        return entry
    elif (entry.keys()-DISPENSABLE_KEYS):
        print(
            'WARNING: strange entry found [%s:%i]: %s' % (
                fileName,
                lineNumber,
                str(entry),
            )
        )
    else:
        return None

if __name__=='__main__':
    usage='** Usage: <command>  [-wipetables] [-sourcedir DIR] [-tmpdir DIR] [-nodump]'
    optionSet={'sourcedir','tmpdir','dump', 'wipetables'}
    cmdArgs,cmdOpts=cmdLineParse(sys.argv[1:])
    if 'sourcedir' in cmdOpts:
        if len(cmdOpts['sourcedir'])==1:
            print('* Setting source dir to "%s"' % cmdOpts['sourcedir'][0])
            srcDir=cmdOpts['sourcedir'][0]
    if 'tmpdir' in cmdOpts:
        if len(cmdOpts['tmpdir'])==1:
            print('* Setting temp dir to "%s"' % cmdOpts['tmpdir'][0])
            tmpDir=cmdOpts['tmpdir'][0]
    if 'wipetables' in cmdOpts:
        print('* Wiping the histories on DB before inserting')
    if len(cmdOpts.keys()-optionSet)>0:
        print('Unrecognized option(s): "%s"' % (','.join(cmdOpts.keys()-optionSet)))
    if len(cmdArgs)>0:
        print('Unrecognized command-line arguments: "%s"' % (','.join(cmdArgs)))

    # initialisation
    print('* Src dir: %s' % srcDir)
    print('* Tmp dir: %s' % tmpDir)

    # is the temp dir empty?
    if len(os.listdir(tmpDir))>0:
        print('** ERROR: nonempty temp dir. Aborting')
    else:
        # recursively collect all filenames relevant for importing
        print('* Collecting file names ... ',end='')
        allFiles=list(filter(isLogFile,collectFiles(srcDir)))
        print('done: %i logfiles found.' % len(allFiles))
        # one by one, parse them and collect all entries
        # TEMP:
        # allFiles=allFiles[:5]
        # END TEMP
        allEvents=[]
        print('* Processing files ...')
        for logFile in allFiles:
            fTitle=os.path.relpath(logFile,srcDir)
            theseEvents=extractEvents(logFile,tempDir=tmpDir)
            allEvents+=theseEvents
        print('Done processing files [total events: %i]' % len(allEvents))
        # arrange events in sorted lists, one per counter
        print('Rearranging and shuffling events ... ', end='')
        counterIDs=set(ev['counterid'] for ev in allEvents)
        counterHistories={counterid: [] for counterid in counterIDs}
        for ev in allEvents:
            # here abnormal numbers are discarded
            if ev['value']>=-1 and ev['value']<100:
                counterHistories[ev['counterid']].append(ev)
        sortedHistories={cid: sorted(clst,key=lambda ev: ev['timestamp']) for cid,clst in counterHistories.items()}
        print('done (%s).' % ', '.join('%s: %i' % (cid,len(clst)) for cid,clst in sortedHistories.items()))
        if 'dump' in cmdOpts:
            # ugly output for debug in tmpDir
            print('Dumping for debug... ',end='')
            for cK,cLst in sortedHistories.items():
                print('[%s] ' % cK, end='')
                open(os.path.join(tmpDir,'dump_%s.dat' % cK),'w').write(
                    '\n'.join('%3i\t%s' % (ev['value'],time.mktime(ev['timestamp'].timetuple())) for ev in cLst)
                )
            print('done.')
        # Construction of the events in the final form:
        #   counterid, value, starttime, endtime
        # A dict-pass is done to remove zero-seconds events,
        # keeping the highest value.
        print('Filtering event lists... ',end='')
        uniquedHistories={}
        for cK,cLst in sortedHistories.items():
            evDict={}
            for ev in cLst:
                # for duplicate timestamp, overwrite only if highest value
                if ev['timestamp'] not in evDict or evDict[ev['timestamp']]['value']<ev['value']:
                    evDict[ev['timestamp']]=ev
            uniquedHistories[cK]=sorted(evDict.values(),key=lambda ev: ev['timestamp'])
        print('done (%s).' % ', '.join('%s: %i' % (cid,len(clst)) for cid,clst in uniquedHistories.items()))
        # for all counters, a list of N elements results in N-1 full-fledged events,
        # plus a last one covering up to the present time.
        # If the import is done consistently (i.e. in a moment of inactivity and after having
        # wiped the history), then no single state change is lost (except the very first).
        db=dbOpenDatabase(dbFullName)
        # optionally clear the table before injecting new items
        if 'wipetables' in cmdOpts:
            print('Clearing the previously-present history from DB... ', end='')
            clearCounterStatusSpansTable(db)
            print('done.')
        #
        print('Registering events on the history... ',end='')
        for cK,cLst in sortedHistories.items():
            print('[%s] ' % cK,end='')
            for ev1,ev2 in zip(cLst[:-1],cLst[1:]):
                csDict={
                    'counterid': cK,
                    'value': ev1['value'],
                    'starttime': ev1['timestamp'],
                    'endtime': ev2['timestamp'],
                }
                newEvent=CounterStatusSpan(
                    **csDict
                )
                logCounterStatusSpan(db,newEvent)
            # and a last event spanning up to now
            csDict={
                'counterid': cK,
                'value': cLst[-1]['value'],
                'starttime': cLst[-1]['timestamp'],
                'endtime': time.mktime(datetime.now().timetuple()),
            }
            newEvent=CounterStatusSpan(
                **csDict
            )
            logCounterStatusSpan(db,newEvent)
        db.commit()
        print(' done.')
