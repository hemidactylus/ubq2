'''
    trigger_checkbeat.py : performs a round of check on all counters
'''

from time import sleep

import env
from app.counters.counters import checkBeat
from config import (
    dbFullName,
)
from app.database.dbtools import (
    dbOpenDatabase,
    dbGetSetting,
)

if __name__=='__main__':
    db=dbOpenDatabase(dbFullName)
    while True:
        print('Checking...',end='')
        checkbeatfrequency=int(dbGetSetting(db, 'CHECKBEAT_FREQUENCY', '10'))
        checkBeat(db)
        db.commit()
        print(' done.')
        sleep(checkbeatfrequency)
