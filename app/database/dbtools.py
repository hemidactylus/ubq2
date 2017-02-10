# dbtools.py : library to interface with the database

import sqlite3 as lite
from operator import itemgetter

from app.database.models import(
    User,
    Counter,
    CounterStatus,
)
from app.database.dbschema import dbTablesDesc
from config import DB_DEBUG

# GENERIC FUNCTIONS

def listColumns(tableName):
    '''
        reads the table structure and returns an *ordered*
        list of its fields
    '''
    colList=[]
    if 'primary_key' in dbTablesDesc[tableName]:
        colList+=[dbTablesDesc[tableName]['primary_key'][0]]
    colList+=map(itemgetter(0),dbTablesDesc[tableName]['columns'])
    return colList

def dbAddRecordToTable(db,tableName,recordDict):
    colList=listColumns(tableName)
    #
    insertStatement='INSERT INTO %s VALUES (%s)' % (tableName, ', '.join(['?']*len(colList)))
    insertValues=tuple(recordDict[k] for k in colList)
    #
    if DB_DEBUG:
        print('[dbAddRecordToTable] %s' % insertStatement)
        print('[dbAddRecordToTable] %s' % ','.join('%s' % iv for iv in insertValues))
    db.execute(insertStatement, insertValues)
    #
    return

def dbUpdateRecordOnTable(db,tableName,newDict, allowPartial=False):
    dbKey=dbTablesDesc[tableName]['primary_key'][0]
    otherFields=list(map(itemgetter(0),dbTablesDesc[tableName]['columns']))
    updatePart=', '.join('%s=?' % of for of in otherFields if not allowPartial or of in newDict)
    updatePartValues=[newDict[of] for of in otherFields if not allowPartial or of in newDict]
    whereClause='%s=?' % dbKey
    whereValue=newDict[dbKey]
    updateStatement='UPDATE %s SET %s WHERE %s' % (tableName,updatePart,whereClause)
    updateValues=updatePartValues+[whereValue]
    if DB_DEBUG:
        print('[dbUpdateRecordOnTable] %s' % updateStatement)
        print('[dbUpdateRecordOnTable] %s' % ','.join('%s' % iv for iv in updateValues))
    db.execute(updateStatement, updateValues)
    #
    return

def dbOpenDatabase(dbFileName):
    con = lite.connect(dbFileName)
    return con

def dbCreateTable(db,tableName,tableDesc):
    '''
        tableName is a string
        tableDesc is a nonempty array of pairs (name,type)
    '''
    fieldLines=[]
    if 'primary_key' in tableDesc:
        fieldLines+=['%s %s PRIMARY KEY' % (tableDesc['primary_key'])]
    fieldLines+=['%s %s' % fld for fld in tableDesc['columns']]
    createCommand='CREATE TABLE %s (\n\t%s\n);' % (
        tableName,
        ',\n\t'.join(fieldLines),
    )
    if DB_DEBUG:
        print('[dbCreateTable] %s' % createCommand)
    cur=db.cursor()
    cur.execute(createCommand)

def dbRetrieveAllRecords(db, tableName):
    '''
        returns an iterator on dicts,
        one for each item in the table,
        in no particular order AT THE MOMENT
    '''
    cur=db.cursor()
    selectStatement='SELECT * FROM %s' % (tableName)
    if DB_DEBUG:
        print('[dbRetrieveAllRecords] %s' % selectStatement)
    cur.execute(selectStatement)
    for recTuple in cur.fetchall():
        yield dict(zip(listColumns(tableName),recTuple))

def dbRetrieveRecordByKey(db, tableName, key):
    '''
        key is for instance {'id': '123'}
        and specifies the primary key of the table.
        Converts to dict!
    '''
    cur=db.cursor()
    kNames,kValues=zip(*list(key.items()))
    whereClause=' AND '.join('%s=?' % kn for kn in kNames)
    selectStatement='SELECT * FROM %s WHERE %s' % (tableName,whereClause)
    if DB_DEBUG:
        print('[dbRetrieveRecordByKey] %s' % selectStatement)
        print('[dbRetrieveRecordByKey] %s' % ','.join('%s' % iv for iv in kValues))
    cur.execute(selectStatement, kValues)
    docTuple=cur.fetchone()
    if docTuple is not None:
        docDict=dict(zip(listColumns(tableName),docTuple))
        return docDict
    else:
        return None

def dbDeleteRecordsByKey(db, tableName, key):
    cur=db.cursor()
    kNames,kValues=zip(*list(key.items()))
    whereClause=' AND '.join('%s=?' % kn for kn in kNames)
    deleteStatement='DELETE FROM %s WHERE %s' % (tableName, whereClause)
    if DB_DEBUG:
        print('[dbDeleteRecordsByKey] %s' % deleteStatement)
        print('[dbDeleteRecordsByKey] %s' % ','.join('%s' % iv for iv in kValues))
    cur.execute(deleteStatement, kValues)

# TABLE-TIED FUNCTION SHORTCUTS
def dbGetUser(db, username):
    userDict = dbRetrieveRecordByKey(db,'users',{'username': username})
    return User(**userDict)

def dbAddUser(db, nUser):
    dbAddRecordToTable(db,'users',nUser.asDict())

def dbAddSetting(db, nSetting):
    dbAddRecordToTable(db,'settings',nSetting.asDict())

def dbSaveSetting(db, sKey, sVal):
    dbUpdateRecordOnTable(db,'settings',{'key': sKey, 'value': sVal})

def dbGetSetting(db, sKey, default=None):
    '''
        returns just the VALUE
    '''
    sDict = dbRetrieveRecordByKey(db,'settings',{'key': sKey})
    if sDict is not None:
        return sDict['value']
    else:
        return default

def dbAddCounter(db, nCounter):
    '''
        must ensure no two counters have the same key!
        returns nonzero on error
    '''
    if nCounter.key in [cnt.key for cnt in dbGetCounters(db)]:
        return (1,'Duplicate key')
    else:
        dbAddRecordToTable(db,'counters',nCounter.asDict())
        return (0,'')

def dbUpdateUser(db,nUser):
    dbUpdateRecordOnTable(
        db,
        'users',
        nUser.asDict(),
    )

def dbGetCounters(db, keepAsDict=False):
    if keepAsDict:
        return list(dbRetrieveAllRecords(db,'counters'))
    else:
        return [
            Counter(**counterDict)
            for counterDict in dbRetrieveAllRecords(db,'counters')
        ]

def dbGetCounter(db, counterid, keepAsDict=False):
    counterDict = dbRetrieveRecordByKey(db, 'counters', {'id': counterid})
    if keepAsDict:
        return counterDict
    else:
        return Counter(**counterDict) if counterDict else None

def dbGetCounterByKey(db, cKey, keepAsDict=False):
    counterDict = dbRetrieveRecordByKey(db, 'counters', {'key': cKey})
    if keepAsDict:
        return counterDict
    else:
        return Counter(**counterDict) if counterDict else None

def dbGetCounterStatus(db, counterid, keepAsDict=False):
    counterDict = dbRetrieveRecordByKey(db, 'counterstatuses', {'id': counterid})
    if keepAsDict:
        return counterDict
    else:
        return CounterStatus(**counterDict) if counterDict else None

def dbUpdateCounterStatus(db, counterid, nCounterStatus):
    dbUpdateRecordOnTable(db, 'counterstatuses', nCounterStatus, allowPartial=True)

def dbAddCounterStatus(db, nCounterStatus):
    dbAddRecordToTable(db, 'counterstatuses', nCounterStatus)

def dbUpdateCounter(db,nCounter):
    if nCounter.key in [cnt.key for cnt in dbGetCounters(db) if cnt.id!=nCounter.id]:
        return (1,'Duplicate key')
    else:
        dbUpdateRecordOnTable(
            db,
            'counters',
            nCounter.asDict(),
        )
        return (0,'')

def dbDeleteCounter(db,counterid):
    dbDeleteRecordsByKey(db, 'counters', {'id': counterid})
