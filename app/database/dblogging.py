'''
    dblogging.py : all statistics/log writes to DB happen from here
'''

from time import time

from config import (
    dbFullName,
)
from app.database.dbtools import (
    dbAddRecordToTable,
    dbUpdateRecordOnTable,
    dbRetrieveRecordsByKey,
    dbRetrieveRecordByKey,
    dbRetrieveAllRecords,
    dbGetSetting,
    dbClearTable,
    dbGetCounter,
    dbOpenDatabase,
    dbGetSetting,
)
from app.database.models import(
    CounterStatusSpan,
    UserUsageDay,
)
from app.utils.dateformats import (
    localDayTimestamp,
    pastTimestamp,
)
from app.utils.parsing import (
    integerOrDefault,
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
    # retrieve, for all days, the number of usages
    # whose nrequests is >= the required cut
    accessesPerDay={}
    for accessEntry in dbGetUserUsageDays(db,counterid,startTime=reqDay):
        eventDate=localDayTimestamp(accessEntry.date,dbTZ)
        accessesPerDay[eventDate]=accessesPerDay.get(eventDate,0)
        if (accessEntry.lastrequest-accessEntry.firstrequest)>=rCut:
            accessesPerDay[eventDate]=accessesPerDay[eventDate]+1
    return accessesPerDay

def logNumbersUsageFetch(counterid,durationthreshold='0',accessthreshold='0',daysBack=None):
    '''
        packs some of the param-parsing and querying logic
        for the two number/accesses base queries into a single
        call used by several 'usage stats' endpoints
    '''
    _daysBack=integerOrDefault(daysBack,-1)
    if daysBack is not None and _daysBack>0:
        reqDay=pastTimestamp(_daysBack)
    else:
        reqDay=None
    dCut=integerOrDefault(durationthreshold,0)
    rCut=integerOrDefault(accessthreshold,0)
    db=dbOpenDatabase(dbFullName)
    dbTZ=dbGetSetting(db,'WORKING_TIMEZONE')
    #
    accesses=logRetrieveNumberOfAccessesPerDay(db,dbTZ,counterid,rCut,reqDay)
    numbers=logRetrieveNumberOfNumbersPerDay(db,dbTZ,counterid,dCut,reqDay)
    #
    return {
        'accesses': accesses,
        'numbers': numbers,
    }

def logRetrieveAccessesPerUser(db,dbTZ,counterid,accessthreshold=None,daysBack=None,minDaysCut=None):
    '''
        a pre-built data retrieval function for
        the days-per-user statistics ('recurring users')

        A timezone is required for the date conversions

        Cutoff arguments are either None or valid date/numbers
    '''
    _daysBack=integerOrDefault(daysBack,-1)
    if daysBack is not None and _daysBack>0:
        reqDay=pastTimestamp(_daysBack)
    else:
        reqDay=None
    rCut=integerOrDefault(accessthreshold,0)
    mdCut=integerOrDefault(minDaysCut,0)
    # collect all usages passing the filter
    # as time-ordered lists per each occurring user
    accessesPerUser={}
    for accessEntry in dbGetUserUsageDays(db,counterid,startTime=reqDay):
        eventDate=localDayTimestamp(accessEntry.date,dbTZ)
        if (accessEntry.lastrequest-accessEntry.firstrequest)>=rCut:
            userId=accessEntry.userid
            accessObject={
                'date': accessEntry.date,
                'nrequests': accessEntry.nrequests,
                'firstrequest': accessEntry.firstrequest,
                'lastrequest': accessEntry.lastrequest,
            }
            accessesPerUser[userId]=accessesPerUser.get(userId,[])+[accessObject]
    # anonymize and sort the per-user list
    userToIndex={uid: uind for uind,uid in enumerate(accessesPerUser.keys())}
    return {
        userToIndex[uid]: sorted(ulist, key=lambda aObj: aObj['date'])
        for uid,ulist in accessesPerUser.items()
        if len(ulist)>=mdCut
    }
