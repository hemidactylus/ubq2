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
    dbDeleteTable,
    dbRetrieveAllRecords,
    dbDeleteRecordsByKey,
    dbAddUser,
    dbAddCounter,
    dbAddSetting,
    dbAddSystemAlert,
)
from app.database.dbschema import dbTablesDesc
from config import dbFullName
from app.database.models import User, Counter, Setting
from app.database.default_db_values import (
    default_settings,
    default_system_alerts,
)
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
    qargs=sys.argv[1:]
    tablesToRecreate=None
    target_users,target_counters=test_users,test_counters
    while qargs:
        arg=qargs.pop(0)
        if arg=='-s':
            # use real values if available
            if secretValuesLoaded:
                print('  ** Using SECRET values **')
                target_users,target_counters=real_users,real_counters
            else:
                print('  ** Cannot use secret values: falling back to TEST values **')
                target_users,target_counters=test_users,test_counters
        elif arg=='-t':
            # a list of non-flag items will follow with the name of the tables
            tablesToRecreate=[]
            while qargs and qargs[0][0]!='-':
                narg=qargs.pop(0)
                tablesToRecreate.append(narg)
            print('  ** Tables to recreate: %s **' % ','.join(tablesToRecreate))
        else:
            print('  ** Unrecognised argument "%s" **' % arg)
    #
    if not tablesToRecreate:
        if os.path.isfile(dbFullName):
            logDo(lambda: os.remove(dbFullName), '  * Deleting old file')
    #
    if tablesToRecreate is None:
        tablesToRecreate=list(dbTablesDesc.keys())
    db=logDo(lambda: dbOpenDatabase(dbFullName), '  * Opening new DB')
    # table creation
    print('  * Creating tables...')
    for tName, tContents in filter(lambda tnd: tnd[0] in tablesToRecreate,dbTablesDesc.items()):
        try:
            retVal=logDo(lambda:dbDeleteTable(db, tName),'    * Deleting table "%s"' % tName)
        except:
            pass
        retVal=logDo(lambda:dbCreateTable(db, tName, tContents),'    * Creating table "%s"' % tName)

    print('  * Populating tables...')
    adders=[dbAddUser,dbAddCounter,dbAddSetting,dbAddSystemAlert]
    vals=[target_users,target_counters,default_settings,default_system_alerts]
    onames=['users','counters','settings','system_alerts']
    obs=[User,Counter,Setting]
    for adder,vals,ob,oname in zip(adders,vals,obs,onames):
        if oname in tablesToRecreate:
            print('    * Emptying table "%s"' % oname)
            kname=dbTablesDesc[oname].get('primary_key',('id',0))[0][0]
            keys=[doc[kname] for doc in dbRetrieveAllRecords(db,oname)]
            for k in keys:
                dbDeleteRecordsByKey(db,oname,{kname:k})
        if oname in tablesToRecreate:
            print('    * Table "%s"' % oname)
            for oStruct in vals:
                o=ob(**oStruct)
                logDo(lambda: adder(db, o), '      * %s "%s"' % (oname,o))

    logDo(lambda: db.commit(), '  * Committing')
    logDo(lambda: db.close(), '  * Closing')
    logDo(lambda: setRWAttributeForAll(dbFullName), '  * Setting DB file attributes')

    print('Finished.')
