'''
    counters.py : handling of counters, their
    update, the logic of handling their status
'''

from datetime import datetime, timedelta
import sys
from time import time
import pytz

from app.database.dbtools import (
    dbOpenDatabase,
    dbGetCounters,
    dbGetCounterByKey,
    dbUpdateCounterStatus,
    dbGetCounterStatus,
    dbAddCounterStatus,
    dbAddSystemAlert,
    dbGetSetting,
    dbGetCounter,
    dbGetUsers,
)
from app.database.models import (
    CounterStatusSpan,
    SystemAlert,
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
    EMAIL_ILLEGAL_ACCESS_SUBJECT,
    EMAIL_ILLEGAL_ACCESS_BODY,
    REDIRECT_EMAIL_TO_STDOUT,
    ALERT_DATE_FORMAT,

)
from app.utils.dateformats import (
    localDateFromTimestamp,
    pastTimestamp,
    localisedDatetime,
)
from app.sendMail.sendMail import sendMail

def constrain(num,min,max,outervalue):
    if num<=max and num>=min:
        return num
    else:
        return outervalue

def sendAlert(db,mailSubject,mailBody,recipientList,alertType='general',counterid='',**kwargs):
    '''
        a wrapper to sendMail that however, for debugging purposes,
        can be redirected to a console output by suppressing the email.
        This is done by setting REDIRECT_EMAIL_TO_STDOUT=True
        in the config

        Additionally, all events are also logged to a dedicated 'system_alerts' table
    '''
    # log the email that is about to be send
    dbAddSystemAlert(db,{
        'date': pastTimestamp(0), # now
        'type': alertType,
        'message': mailBody,
        'counterid': counterid,
        'subject': mailSubject,
    })
    db.commit()
    # send email alert
    try:
        mailDateSignature=localisedDatetime(
            dbGetSetting(db,'WORKING_TIMEZONE')
        ).strftime(ALERT_DATE_FORMAT)
        if not REDIRECT_EMAIL_TO_STDOUT:
            # log just one line anyway to stdout
            print('[sendAlert] Issuing email with subject=<%s>' % mailSubject,end='')
            sys.stdout.flush()
            sendMail(
                mailSubject=mailSubject,
                mailBody=mailBody,
                recipientList=recipientList,
                dateSignature=mailDateSignature,
                **kwargs
            )
            print('[sendAlert] done')
        else:
            print('== [DEBUG SENDMAIL REDIRECTED TO STDOUT] ==')
            print('MAIL_RECIPIENTS : %s' % ', '.join(recipientList))
            print('MAIL_SUBJECT    : %s' % mailSubject)
            print('MAIL_BODY       :\n%s' % mailBody)
            print('MAIL_DATE_SIG   : %s' % mailDateSignature)
            print('===========================================')
            sys.stdout.flush()
    except:
        # log the failed email sending
        dbAddSystemAlert(db,{
            'date': pastTimestamp(0), # now
            'type': 'cannot_send_email_alert',
            'message': mailBody,
            'counterid': counterid,
            'subject': mailSubject,
        })
        db.commit()

def signalNumberToCounter(cKey, nNumber, request):
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
    if tCounter is None:
        # counter does not exist, i.e. unregistered key.
        # Issue an alert with some context information
        reqHeaders=request.headers
        reqCookies=request.cookies
        reqUrl=request.url
        reqRemoteAddr=request.remote_addr
        warnIllegalAccessAlert(db,reqHeaders,reqCookies,reqUrl,reqRemoteAddr)
        # and return a 'unreg key' value back
        return '2'
    elif tCounter.mode=='o':
        # no alert is raised, nevertheless a 'unreg key' is returned to the caller
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

def collectAddressees(db):
    return [u.email for u in dbGetUsers(db) if u.subscribed]

def dispatchOnlineAlert(db,counterid):
    '''
        Scans the user accounts and, for those with an active alert-email setting,
        prepares and sends the back-online email
    '''
    addressees=collectAddressees(db)
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
            sendAlert(
                db,
                mailSubject=subject,
                mailBody=body,
                recipientList=addressees,
                counterid=counterid,
                alertType='online_alert',
            )

def warnIllegalAccessAlert(db,reqHeaders,reqCookies,reqUrl,reqRemoteAddr):
    '''
        Prepares and sends a "warning: illegal access" warning by email
        with the relevant request data attached
    '''
    addressees=collectAddressees(db)
    if addressees:
        subject=EMAIL_ILLEGAL_ACCESS_SUBJECT
        body=EMAIL_ILLEGAL_ACCESS_BODY.format(
            reqHeaders=reqHeaders,
            reqCookies=reqCookies,
            reqUrl=reqUrl,
            reqRemoteAddr=reqRemoteAddr,
            servicename=UBQ_SERVICE_FULLNAME,
        )
        sendAlert(
            db,
            mailSubject=subject,
            mailBody=body,
            recipientList=addressees,
            counterid='',
            alertType='illegal_access_alert',
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
            sendAlert(
                db,
                mailSubject=subject,
                mailBody=body,
                recipientList=addressees,
                counterid=counterid,
                alertType='offline_alert',
            )

def isWithinAlertTime(db, timestamp):
    '''
        returns True if the provided utc timestamp falls within the alert-sending time window
    '''
    tzDate=localDateFromTimestamp(timestamp,dbGetSetting(db,'WORKING_TIMEZONE'))
    aStart=datetime.strptime(dbGetSetting(db,'ALERT_WINDOW_START'),'%H:%M').time()
    aEnd=datetime.strptime(dbGetSetting(db,'ALERT_WINDOW_END'),'%H:%M').time()
    print('isWithinAlertTime: tzDate, aStart, aEnd: %s %s %s' % (tzDate,aStart,aEnd))
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
