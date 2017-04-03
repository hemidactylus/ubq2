'''
    dblogging.py : all statistics/log writes to DB happen from here
'''

from app.database.dbtools import (
    dbAddRecordToTable,
    dbRetrieveRecordsByKey,
    dbRetrieveAllRecords,
)
from app.database.models import 
from app.database.models import(
    CounterStatusSpan,
    UserUsageDay,
)
from app.utils.dateformats import (
    localDayTimestamp,
)

def logCounterStatusSpan(db, csSpan):
    '''
        inserts a new counter-status timespan into the table
    '''
    dbAddRecordToTable(db,'stat_counterstatusspans', csSpan.asDict())

def getCounterStatusSpans(db, counterid=None, startTime=None, endTime=None):
    '''
        retrieves counter-status events for a given counterID or all of them
    '''
    whereClauses=[]
    if startTime:
        whereClauses+=['endtime > %i' % startTime]
    if endTime:
        whereClauses+=['starttime < %i' % endTime]
    #
    if counterid:
        return (CounterStatusSpan(**css) 
            for css in dbRetrieveRecordsByKey(
                db,
                'stat_counterstatusspans',
                {'counterid': counterid},
                whereClauses=whereClauses,
            )
        )
    else:
        return (CounterStatusSpan(**css)
            for css in dbRetrieveAllRecords(
                db,
                'stat_counterstatusspans',
                whereClauses=whereClauses,
            )
        )

def dbGetUserUsageDay(db,userid,counterid,usagedate,keepAsDict=False):
    usageDayDict = dbRetrieveRecordByKey(
        db,
        'userusagedays',
        {
            'userid': userid,
            'date': usagedate, 
            'counterid': counterid,
        },
    )
    if keepAsDict:
        return usageDayDict
    else:
        return UserUsageDay(**usageDayDict) if usageDayDict else None

def dbAddUserUsageDay(db,nUserUsageDay):
    dbAddRecordToTable(db, 'userusagedays', nUserUsageDay)

def dbUpdateUserUsageDay(db,nUserUsageDay):
    '''
        it is assumed the record exists already at this point
    '''
    dbUpdateRecordOnTable(db, 'userusagedays', nUserUsageDay)

def logUserCounterRequest(db, userid, counterid):
    '''
        handles all logic associated to a user requesting a counter
        in terms of the per-user, per-counter and per-date log:
        creation/update of the log record, and so on.
    '''
    # calculate now and now's date, locally
    evTime=int(time())
    evDate=localDayTimestamp(evTime)
    # try and see if record is new:
    userUDay=dbGetUserStatusSpans(db,userid,counterid,evDate)
    if userUDay:
        # if not, edit and re-update it back
        nCntStat=UserUsageDay(
            userid=userid,
            counterid=counterid,
            date=evDate,
            firstrequest=evTime,
            lastrequest=evTime,
            nrequests=1,
        )
        dbAddUserUsageDay(db,nCntStat)
        # if record is new, create it and insert
    else:
        userUDay.nrequests+=1
        userUDay.lastrequest=evTime
        dbUpdateUserUsageDay(db,userUDay)
    db.commit()
