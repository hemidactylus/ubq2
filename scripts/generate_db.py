'''
    generate_db.py : tools for handling generation of the database.
'''

import os

import env
from app.database.dbtools import dbOpenDatabase, dbCreateTable, dbAddUser
from app.database.dbschema import dbTablesDesc
from config import dbFullName
from app.database.models import User
from app.utils.interactive import ask_for_confirmation, logDo
from test_db_values import test_users

if __name__=='__main__':
    #
    if os.path.isfile(dbFullName):
        logDo(lambda: os.remove(dbFullName), ' * Deleting old file')
    #
    db=logDo(lambda: dbOpenDatabase(dbFullName), ' * Opening new DB')
    # table creation
    print(' * Creating tables...')
    for tName, tContents in dbTablesDesc.items():
        retVal=logDo(lambda:dbCreateTable(db, tName, tContents),'  * Creating table "%s"' % tName)

    print(' * Populating tables...')
    for uStruct in test_users:
        u=User(**uStruct)
        logDo(lambda: dbAddUser(db, u), '  * Creating user "%s"' % u.username)

    logDo(lambda: db.commit(), ' * Committing')
    logDo(lambda: db.close(), ' * Closing')

    print('Finished.')
