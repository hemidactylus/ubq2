'''
    counters.py : handling of counters, their
    update, the logic of handling their status
'''

from datetime import datetime, timedelta
from time import time
import pytz

from app.database.dbtools import (
    dbOpenDatabase,
    dbGetCounters,
    dbGetCounterByKey,
    dbUpdateCounterStatus,
    dbGetCounterStatus,
    dbAddCounterStatus,
    dbGetSetting,
    dbGetCounter,
    dbGetUsers,
)
from app.database.models import (
    CounterStatusSpan,
)
from app.database.dblogging import (
    logCounterStatusSpan,
)
from config import (
    dbFullName,
    UBQ_SERVICE_FULLNAME,
    EMAIL_OFFLINE_ALERT_SUBJECT,
    EMAIL_OFFLINE_ALERT_BODY,
    EMAIL_ONLINE_ALERT_SUBJECT,
    EMAIL_ONLINE_ALERT_BODY,
)
from app.utils.dateformats import (
    localDateFromTimestamp,
)
from app.sendMail.sendMail import sendMail

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
        # logging
        if oldStatus is not None:
            prevValue=oldStatus.value if oldStatus.online else -1
            if prevValue!=newValue:
                logCounterStatusSpan(
                    db,
                    CounterStatusSpan(
                        counterid=tCounter.id,
                        value=prevValue,
                        starttime=oldStatus.lastchange,
                        endtime=newStatus['lastchange'],
                    )
                )
        #
        if oldStatus is None:
            # right now, at the update, we assume counter online and no notify needed
            newStatus['online']=1
            newStatus['tonotify']=0
            newStatus['lastnotify']=0
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

        DOES NOT COMMIT BY ITSELF

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
            # additionally mark the time of going-offline
            newStatus['lastchange']=int(time())
            if not newOnline:
                # log the last number up to this time: only when going-offline must the log be triggered from here
                logCounterStatusSpan(
                    db,
                    CounterStatusSpan(
                        counterid=cntStatus.id,
                        value=cntStatus.value,
                        starttime=cntStatus.lastchange,
                        endtime=newStatus['lastchange'],
                    )
                )
        if not newOnline and elapsed>int(dbGetSetting(db,'COUNTER_ALERT_TIMEOUT')) and cntStatus.tonotify:
            # it has been offline for more than the alert-time:
            #   if in the time window, send notification out
            #   mark tonotify=False in any case
            if isWithinAlertTime(db, time()):
                dispatchOfflineAlert(db,counterid)
                newStatus['lastnotify']=int(time())
            newStatus['tonotify']=0
        if newOnline and not cntStatus.online and not cntStatus.tonotify:
            # it is coming back online, it wasnt' at the previous check,
            # and the notification has been sent out already:
            #    check if a back-online notification is to be sent:
            #    i.e. (1) we must be in the time window, (2) not too much time must have passed
            if isWithinAlertTime(db, time()) and \
                (time()-cntStatus.lastnotify)<=int(dbGetSetting(db,'COUNTER_BACK_ONLINE_TIMESPAN')):
                #
                dispatchOnlineAlert(db, counterid)
        if newStatus:
            newStatus['id']=counterid
            dbUpdateCounterStatus(db,counterid,newStatus)

def dispatchOnlineAlert(db,counterid):
    '''
        Scans the user accounts and, for those with an active alert-email setting,
        prepares and sends the back-online email
    '''
    addressees=[u.email for u in dbGetUsers(db) if u.subscribed]
    if addressees:
        cnt=dbGetCounter(db,counterid)
        if cnt:
            subject=EMAIL_ONLINE_ALERT_SUBJECT.format(
                countername=cnt.fullname,
                counterid=cnt.id,
            )
            body=EMAIL_ONLINE_ALERT_BODY.format(
                countername=cnt.fullname,
                counterid=cnt.id,
                alerttimeout=dbGetSetting(db,'COUNTER_ALERT_TIMEOUT'),
                servicename=UBQ_SERVICE_FULLNAME,
                counternotes=cnt.notes,
            )
            sendMail(
                mailSubject=subject,
                mailBody=body,
                recipientList=addressees,
            )

def dispatchOfflineAlert(db,counterid):
    '''
        Scans the user accounts and, for those with an active alert-email setting,
        prepares and sends the alert-warning email
    '''
    addressees=[u.email for u in dbGetUsers(db) if u.subscribed]
    if addressees:
        cnt=dbGetCounter(db,counterid)
        if cnt:
            subject=EMAIL_OFFLINE_ALERT_SUBJECT.format(
                countername=cnt.fullname,
                counterid=cnt.id,
            )
            body=EMAIL_OFFLINE_ALERT_BODY.format(
                countername=cnt.fullname,
                counterid=cnt.id,
                alerttimeout=dbGetSetting(db,'COUNTER_ALERT_TIMEOUT'),
                servicename=UBQ_SERVICE_FULLNAME,
                counternotes=cnt.notes,
            )
            sendMail(
                mailSubject=subject,
                mailBody=body,
                recipientList=addressees,
            )

def isWithinAlertTime(db, timestamp):
    '''
        returns True if the provided utc timestamp falls within the alert-sending time window
    '''
    tzDate=localDateFromTimestamp(timestamp,dbGetSetting(db,'WORKING_TIMEZONE'))
    aStart=datetime.strptime(dbGetSetting(db,'ALERT_WINDOW_START'),'%H:%M').time()
    aEnd=datetime.strptime(dbGetSetting(db,'ALERT_WINDOW_END'),'%H:%M').time()
    return tzDate.time() >= aStart and tzDate.time() <= aEnd

def checkBeat(db=None):
    '''
        this is called from a heartbeat job and triggers offline-counter-checks
        If no db is passed, self-commits; else, DOES NOT COMMIT
    '''
    if db is None:
        _db=dbOpenDatabase(dbFullName)
    else:
        _db=db
    allCounters=dbGetCounters(_db)
    for cnt in allCounters:
        checkCounterActivity(_db, cnt.id)
    if db is None:
        _db.commit()
