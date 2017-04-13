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
from collections import Counter

from app import app, lm

from config import (
    dbFullName,
)
from app.database.dblogging import (
    getCounterStatusSpans,
    dbGetUserUsageDays,
)
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
from app.utils.logstats import (
    eventDuration,
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

@app.route('/DATA_counter_duration_data/<counterid>/<daysback>')
@app.route('/DATA_counter_duration_data/<counterid>')
@login_required
def DATA_counter_duration_data(counterid,daysback=None):
    '''
        returns a JSON with a histogram of frequency for
        the number durations for a given counter.
        Special values "-1" does not enter the statistics.
        If starttime is not provided, the whole history is read,
        otherwise it is taken to be a number of days back w.r.t. now.
    '''
    db=dbOpenDatabase(dbFullName)
    counterName=dbGetCounter(db,counterid).fullname
    # retrieve all events for the required counter and the required time frame
    # must build the time-window after reconverting back from jday
    startTimestamp=pastTimestamp(nDays=int(daysback)) if daysback else None

    durationHistogram=Counter(
        [
            eventDuration(ev)
            for ev in getCounterStatusSpans(
                db,
                counterid, 
                startTime=startTimestamp,
            )
            if ev.value!=-1
        ]
    )
    fullStructure={
        'histogram': [
            {
                'duration': k,
                'count': v
            } 
            for k,v in durationHistogram.items()
        ],
        'n': sum(durationHistogram.values()),
    }
    return jsonify(**fullStructure)

@app.route('/DATA_user_usage_data_per_day/<counterid>')
@app.route('/DATA_user_usage_data_per_day/<counterid>/<jday>')
@login_required
def DATA_user_usage_data_per_day(counterid,jday=None):
    '''
        if no java-day provided, returns a list of the available days
        else a list of usage users for that day
    '''
    db=dbOpenDatabase(dbFullName)
    counterName=dbGetCounter(db,counterid).fullname
    if jday:
        reqDay=javaTimestampToTimestamp(float(jday))
    else:
        reqDay=None
    #
    userStatDays=list(dbGetUserUsageDays(db,counterid,reqDay))
    if reqDay:
        # detailed response per one day
        allTimes=[1000*t for ev in userStatDays for t in [ev.firstrequest,ev.lastrequest]]
        fullStructure={
            'day': jday,
            'counterid': counterid,
            'countername': counterName,
            'starttime': min(allTimes),
            'endtime': max(allTimes),
            'usages': [
                {
                    'firstrequest': 1000*udd.firstrequest,
                    'lastrequest': 1000*udd.lastrequest,
                    'nrequests': udd.nrequests,
                    'userid': udd.userid,
                }
                for udd in userStatDays
            ],
        }
    else:
        # a list of available days
        daysList=sorted(set([
            1000*udd.date for udd in userStatDays
        ]))
        fullStructure={
            'days': daysList,
            'n': len(daysList),
        }
    return jsonify(**fullStructure)