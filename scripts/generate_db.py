'''
    generate_db.py : tools for handling generation of the database.
'''

import os
import sys
import stat

import env
from app.database.dbtools import (
    dbOpenDatabase,
    dbCreateTable,
    dbAddUser,
    dbAddCounter,
    dbAddSetting,
)
from app.database.dbschema import dbTablesDesc
from config import dbFullName
from app.database.models import User, Counter, Setting
from app.database.default_db_values import default_settings
from app.utils.interactive import ask_for_confirmation, logDo
from test_db_values import test_users, test_counters
try:
    from secret_db_values import real_users, real_counters
    secretValuesLoaded=True
except:
    secretValuesLoaded=False

def setRWAttributeForAll(filename):
    '''
        Set rw-rw-rw attribute to database file
    '''
    attrConstant=stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH | stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
    os.chmod(filename, attrConstant )

if __name__=='__main__':
    #
    if '-s' in sys.argv[1:]:
        # use real values if available
        if secretValuesLoaded:
            print('  ** Using SECRET values **')
            target_users,target_counters=real_users,real_counters
        else:
            print('  ** Cannot use secret values: falling back to TEST values **')
            target_users,target_counters=test_users,test_counters
    else:
        print(' ** Using TEST values **')
        target_users,target_counters=test_users,test_counters
    #
    if os.path.isfile(dbFullName):
        logDo(lambda: os.remove(dbFullName), '  * Deleting old file')
    #
    db=logDo(lambda: dbOpenDatabase(dbFullName), '  * Opening new DB')
    # table creation
    print('  * Creating tables...')
    for tName, tContents in dbTablesDesc.items():
        retVal=logDo(lambda:dbCreateTable(db, tName, tContents),'    * Creating table "%s"' % tName)

    print('  * Populating tables...')
    adders=[dbAddUser,dbAddCounter,dbAddSetting]
    vals=[target_users,target_counters,default_settings]
    onames=['user','counter','setting']
    obs=[User,Counter,Setting]
    for adder,vals,ob,oname in zip(adders,vals,obs,onames):
        print('    * Table "%s"' % oname)
        for oStruct in vals:
            o=ob(**oStruct)
            logDo(lambda: adder(db, o), '      * %s "%s"' % (oname,o))

    logDo(lambda: db.commit(), '  * Committing')
    logDo(lambda: db.close(), '  * Closing')
    logDo(lambda: setRWAttributeForAll(dbFullName), '  * Setting DB file attributes')

    print('Finished.')
