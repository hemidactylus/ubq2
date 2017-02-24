'''
    dblogging.py : all statistics/log writes to DB happen from here
'''

from app.database.dbtools import (
    dbAddRecordToTable,
    dbRetrieveRecordsByKey,
    dbRetrieveAllRecords,
)
from app.database.models import CounterStatusSpan

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
