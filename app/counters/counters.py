'''
    counters.py : handling of counters, their
    update, the logic of handling their status
'''

from datetime import datetime, timedelta
from time import time
import pytz

from app.database.dbtools import (
    dbOpenDatabase,
    dbGetCounterByKey,
    dbUpdateCounterStatus,
    dbGetCounterStatus,
    dbAddCounterStatus,
    dbGetSetting,
)
from config import (
    dbFullName,
)
from app.utils.dateformats import (
    localDateFromTimestamp,
)

def constrain(num,min,max,outervalue):
    if num<=max and num>=min:
        return num
    else:
        return outervalue

def signalNumberToCounter(cKey, nNumber):
    '''
        Handles completely the signal nNumber received with the key cKey.
        Must conform to the specifics of the update-endpoint:
            2   key is unregistered:
                this includes counter with MODE='o'
            1   not enough arguments (not raised anymore)
            0   all well (including when N is out of bounds, in which case -> -1)
    '''
    db=dbOpenDatabase(dbFullName)
    tCounter=dbGetCounterByKey(db, cKey)
    if tCounter is None or tCounter.mode=='o':
        return '2'
    else:
        # counter exists and is in states 'a', 'p', 'm': handle updates
        #
        # retrieve the old values
        oldStatus=dbGetCounterStatus(db,tCounter.id)
        # prepare the fields that are to be changed
        newStatus={
            'id': tCounter.id,
            'lastupdate': int(time()),
        }
        newValue=constrain(nNumber,0,99,-2)
        if oldStatus is None or not oldStatus.online or oldStatus.value != newValue:
            # really new number
            newStatus['value']=newValue
            newStatus['lastchange']=newStatus['lastupdate']
        if oldStatus is None:
            # right now, at the update, we assume counter online and no notify needed
            newStatus['online']=1
            newStatus['tonotify']=0
        # write changes to record
        if oldStatus is not None:
            dbUpdateCounterStatus(db,newStatus['id'],newStatus)
        else:
            dbAddCounterStatus(db,newStatus)
        # invoke the offlinechecker
        checkCounterActivity(db, tCounter.id)
        #
        db.commit()
        return '0'

def checkCounterActivity(db, counterid):
    '''
        depending on the last activity time and the current time,
        possible changes online <--> offline are handled here,
        with notifications to admin whenever deemed necessary
    '''
    # if we update counter status - we assume it exists at this point,
    # otherwise we silently do nothing
    cntStatus=dbGetCounterStatus(db,counterid)
    if cntStatus is not None:
        elapsed=int(time()-cntStatus.lastupdate)
        newOnline=(elapsed<int(dbGetSetting(db,'COUNTER_OFFLINE_TIMEOUT')))
        newStatus={}
        if cntStatus.online != newOnline:
            # act upon such a change
            newStatus['online']=int(newOnline)
            newStatus['tonotify']=int(not(newOnline))
        if not newOnline and elapsed>int(dbGetSetting(db,'COUNTER_ALERT_TIMEOUT')) and cntStatus.tonotify:
            # it has been offline for more than the alert-time:
            #   if in the time window, send notification out
            #   mark tonotify=False in any case
            if isWithinAlertTime(db, time()):
                print('HERE SHOULD ALERT OF OFFLINE "%s"!' % counterid)
            newStatus['tonotify']=0
        if newStatus:
            newStatus['id']=counterid
            dbUpdateCounterStatus(db,counterid,newStatus)

def isWithinAlertTime(db, timestamp):
    '''
        returns True if the provided utc timestamp falls within the alert-sending time window
    '''
    tzDate=localDateFromTimestamp(timestamp,dbGetSetting(db,'WORKING_TIMEZONE'))
    aStart=datetime.strptime(dbGetSetting(db,'ALERT_WINDOW_START'),'%H:%M').time()
    aEnd=datetime.strptime(dbGetSetting(db,'ALERT_WINDOW_END'),'%H:%M').time()
    return tzDate.time() >= aStart and tzDate.time() <= aEnd
