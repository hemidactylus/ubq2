'''
    checkbeat.py : handles external periodic check on the times - alternative to the in-webapp endpoint
'''

TO FIX THIS

@app.route('/checkbeat')
def ep_checkbeat():
    '''
        this is called from a heartbeat job and triggers offline-counter-checks
    '''
    db=dbOpenDatabase(dbFullName)
    allCounters=dbGetCounters(db)
    for cnt in allCounters:
        checkCounterActivity(db, cnt.id)
    db.commit()
    return '0'
