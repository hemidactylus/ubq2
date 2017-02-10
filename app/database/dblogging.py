'''
    dblogging.py : all statistics/log writes to DB happen from here
'''

from app.database.dbtools import (
    dbAddRecordToTable,
)

def logCounterStatusSpan(db, csSpan):
    '''
        inserts a new counter-status timespan into the table
    '''
    dbAddRecordToTable(db,'stat_counterstatusspans', csSpan.asDict())
