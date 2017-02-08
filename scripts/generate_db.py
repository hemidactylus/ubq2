'''
    generate_db.py : tools for handling generation of the database.
'''

import os

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

if __name__=='__main__':
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
    vals=[test_users,test_counters,default_settings]
    onames=['user','counter','setting']
    obs=[User,Counter,Setting]
    for adder,vals,ob,oname in zip(adders,vals,obs,onames):
        print('    * Table "%s"' % oname)
        for oStruct in vals:
            o=ob(**oStruct)
            logDo(lambda: adder(db, o), '      * %s "%s"' % (oname,o))

    logDo(lambda: db.commit(), '  * Committing')
    logDo(lambda: db.close(), '  * Closing')

    print('Finished.')
