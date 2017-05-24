'''
    dblogging.py : all statistics/log writes to DB happen from here
'''

from time import time

from app.database.dbtools import (
    dbAddRecordToTable,
    dbUpdateRecordOnTable,
    dbRetrieveRecordsByKey,
    dbRetrieveRecordByKey,
    dbRetrieveAllRecords,
    dbGetSetting,
    dbClearTable,
    dbGetCounter,
)
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

def clearCounterStatusSpansTable(db):
    '''
        *completely* erases the contents of the status-spans table
    '''
    dbClearTable(db, 'stat_counterstatusspans')

def getCounterStatusSpans(db, counterid=None, startTime=None, endTime=None):
    '''
        retrieves counter-status events for a given counterID or all of them
    '''
    whereClauses=[]
    if startTime is not None:
        whereClauses+=['endtime >= %i' % startTime]
    if endTime is not None:
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
        'stat_userusagedays',
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

def dbGetUserUsageDays(db,counterid,usageDate=None, startTime=None, endTime=None):
    '''
        given a counter id and optionally a date the usage stat is
        extracted
    '''
    whereClauses=[]
    if usageDate is not None:
        whereClauses+=['date = %i' % usageDate]
    if startTime is not None:
        whereClauses+=['date >= %i' % startTime]
    if endTime is not None:
        whereClauses+=['date >= %i' % startTime]
    #
    return (UserUsageDay(**uud) 
        for uud in dbRetrieveRecordsByKey(
            db,
            'stat_userusagedays',
            {'counterid': counterid},
            whereClauses=whereClauses,
        )
    )

def dbAddUserUsageDay(db,nUserUsageDay):
    dbAddRecordToTable(db, 'stat_userusagedays', nUserUsageDay)

def dbUpdateUserUsageDay(db,nUserUsageDay):
    '''
        it is assumed the record exists already at this point
    '''
    dbUpdateRecordOnTable(db, 'stat_userusagedays', nUserUsageDay)

def logUserCounterRequest(db, userid, counterid):
    '''
        handles all logic associated to a user requesting a counter
        in terms of the per-user, per-counter and per-date log:
        creation/update of the log record, and so on.
    '''
    # calculate now and now's date, locally
    evTime=int(time())
    evDate=localDayTimestamp(evTime,dbGetSetting(db,'WORKING_TIMEZONE'))
    # try and see if record is new:
    userUDay=dbGetUserUsageDay(db,userid,counterid,evDate)
    if userUDay:
        # if record exists already, edit and re-update it back
        userUDay.nrequests+=1
        userUDay.lastrequest=evTime
        dbUpdateUserUsageDay(db,userUDay.asDict())
    else:
        # if record is new, create it and insert
        nCntStat=UserUsageDay(
            userid=userid,
            counterid=counterid,
            date=evDate,
            firstrequest=evTime,
            lastrequest=evTime,
            nrequests=1,
        )
        dbAddUserUsageDay(db,nCntStat.asDict())
    db.commit()

def logRetrieveNumberOfNumbersPerDay(db,dbTZ,counterid,durationthreshold=None,reqDay=None):
    '''
        a pre-built data retrieval function for
        the historical number-of-numbers per day

        A timezone is required for the date conversions

        Cutoff arguments here are either None or valid date/numbers

    '''
    dCut=durationthreshold if durationthreshold is not None else 0
    counterName=dbGetCounter(db,counterid).fullname
    # retrieve, for all days, the number of numbers
    # whose duration is >= the required cut
    numbersPerDay={}
    for numberEvent in getCounterStatusSpans(db,counterid,startTime=reqDay):
        # this seems to be OK in the query, i.e. the following IF is not needed
        eventDate=localDayTimestamp(numberEvent.starttime,dbTZ)
        numbersPerDay[eventDate]=numbersPerDay.get(eventDate,0)
        if numberEvent.value>=0 and (numberEvent.endtime-numberEvent.starttime)>=dCut:
            numbersPerDay[eventDate]=numbersPerDay[eventDate]+1
    return numbersPerDay

def logRetrieveNumberOfAccessesPerDay(db,dbTZ,counterid,accessthreshold=None,reqDay=None):
    '''
        a pre-built data retrieval function for
        the history of accesses per day

        A timezone is required for the date conversions

        Cutoff arguments are either None or valid date/numbers
    '''
    rCut=accessthreshold if accessthreshold is not None else 0
    counterName=dbGetCounter(db,counterid).fullname
    # retrieve, for all days, the number of usages
    # whose nrequests is >= the required cut
    accessesPerDay={}
    for accessEntry in dbGetUserUsageDays(db,counterid,startTime=reqDay):
        eventDate=localDayTimestamp(accessEntry.date,dbTZ)
        accessesPerDay[eventDate]=accessesPerDay.get(eventDate,0)
        if (accessEntry.lastrequest-accessEntry.firstrequest)>=rCut:
            accessesPerDay[eventDate]=accessesPerDay[eventDate]+1
    return accessesPerDay
