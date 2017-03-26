'''
    data_endpoints.py : this collects the endpoints used by the d3 pages to display
    statistics
'''

from flask import   (
                        render_template,
                        flash,
                        redirect,
                        session,
                        url_for,
                        request,
                        g,
                        abort,
                        escape,
                        make_response,
                        jsonify,
                    )
from flask_login import  (
    login_user,
    logout_user,
    current_user,
    login_required,
)
from datetime import datetime
from time import time

from app import app, lm

from config import (
    dbFullName,
)
from app.database.dblogging import getCounterStatusSpans
from app.database.dbtools import (
    dbOpenDatabase,
    dbGetSetting,
    dbGetCounters,
    dbGetCounter,
)
from app.utils.dateformats import (
    formatTimestamp,
    formatTimeinterval,
    stringToTimestamp,
    pastTimestamp,
    localDateFromTimestamp,
    toJavaTimestamp,
    makeJavaDay,
    javaTimestampToTimestamp,
)

@app.route('/DATA_counterstats_timeplot_days/<counterid>')
@login_required
def DATA_counterstats_timeplot_days(counterid):
    '''
        returns a JSON with a sorted list
        of all distinct days with some values from
        the counter-timeplot logs
    '''
    db=dbOpenDatabase(dbFullName)
    workingTimeZone=dbGetSetting(db,'WORKING_TIMEZONE')
    counterName=dbGetCounter(db,counterid).fullname
    # retrieve all events for the required counter
    jdaySet=sorted(
        {
            makeJavaDay(
                localDateFromTimestamp(d,workingTimeZone)
            )
            for ev in getCounterStatusSpans(
                db,
                counterid,
            )
            for d in [ev.starttime, ev.endtime]
        }
    )
    numDays=len(jdaySet)

    retStruct={
        'days': jdaySet,
        'n': numDays,
    }

    return jsonify(retStruct)

@app.route('/DATA_counterstats_timeplot_data/<counterid>/<jday>')
@login_required
def DATA_counterstats_timeplot_data(counterid,jday):
    db=dbOpenDatabase(dbFullName)
    workingTimeZone=dbGetSetting(db,'WORKING_TIMEZONE')
    counterName=dbGetCounter(db,counterid).fullname
    # retrieve all events for the required counter and the required time frame
    # must build the time-window after reconverting back from jday
    startTimestamp=javaTimestampToTimestamp(float(jday))
    deltaTimestamp=86400.0
    endTimestamp=startTimestamp+deltaTimestamp
    eventList=[
        {
            'value': ev.value,
            'start': 1000*ev.starttime,
            'end': 1000*ev.endtime,
        }
        for ev in sorted(getCounterStatusSpans(
            db,
            counterid, 
            startTime=startTimestamp,
            endTime=endTimestamp,
        ))
    ]
    fullStructure={
        'xrange': {
            'min': startTimestamp*1000,
            'max': endTimestamp*1000,
        },
        'values': eventList,
        'countername': counterName,
    }
    return jsonify(**fullStructure)
