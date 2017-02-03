'''
    test_retrieve.py : various retrieval tests
'''

import os

import env
from app.database.dbtools import dbOpenDatabase, dbGetUser
from config import dbFullName
from app.database.models import User

if __name__=='__main__':
    db=dbOpenDatabase(dbFullName)
    u = dbGetUser(db, 'Stefano')
    print(u)
    print('Finished.')
