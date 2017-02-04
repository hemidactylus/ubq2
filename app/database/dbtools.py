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
    colList=[dbTablesDesc[tableName]['primary_key'][0]]
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

def dbUpdateRecordOnTable(db,tableName,newDict):
    dbKey=dbTablesDesc[tableName]['primary_key'][0]
    otherFields=list(map(itemgetter(0),dbTablesDesc[tableName]['columns']))
    updatePart=', '.join('%s=?' % of for of in otherFields)
    updatePartValues=[newDict[of] for of in otherFields]
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
    fieldLines=['%s %s PRIMARY KEY' % (tableDesc['primary_key'])]
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

# TABLE-TIED FUNCTION SHORTCUTS
def dbGetUser(db, username):
    userDict = dbRetrieveRecordByKey(db,'users',{'username': username})
    return User(**userDict)

def dbAddUser(db, nUser):
    dbAddRecordToTable(db,'users',nUser.asDict())

def dbAddCounter(db, nCounter):
    dbAddRecordToTable(db,'counters',nCounter.asDict())

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

def dbGetCounterStatus(db, counterid, keepAsDict=False):
    counterDict = dbRetrieveRecordByKey(db, 'counterstatuses', {'id': counterid})
    if keepAsDict:
        return counterDict
    else:
        return CounterStatus(**counterDict) if CounterDict else None
