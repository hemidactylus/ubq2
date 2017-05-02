'''
    trigger_checkbeat.py : performs a round of check on all counters
'''

from time import sleep
import sys

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
    while True:
        print('Checking...',end='')
        db=dbOpenDatabase(dbFullName)
        checkbeatfrequency=int(dbGetSetting(db, 'CHECKBEAT_FREQUENCY', '10'))
        checkBeat(db)
        db.commit()
        print(' done.')
        sys.stdout.flush()
        sleep(checkbeatfrequency)
