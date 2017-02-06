'''
    counters.py : handling of counters, their
    update, the logic of handling their status
'''

from datetime import datetime, timedelta
from time import time

from app.database.dbtools import (
    dbOpenDatabase,
    dbGetCounterByKey,
    dbUpdateCounterStatus,
    dbGetCounterStatus,
    dbAddCounterStatus,
)
from config import (
    dbFullName,
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
        if oldStatus is None or oldStatus.value != newValue:
            # really new number
            newStatus['value']=newValue
            newStatus['lastchange']=newStatus['lastupdate']
        # TEMP HERE SHOULD LEAVE THESE TWO FIELDS TO THE ONLINECHECKER
        newStatus['online']=1
        newStatus['tonotify']=0
        # write changes to record
        if oldStatus is not None:
            dbUpdateCounterStatus(db,newStatus['id'],newStatus)
        else:
            dbAddCounterStatus(db,newStatus)
        print('Here Should Invoke Onlinechecker/Statter')
        db.commit()
        return '0'
