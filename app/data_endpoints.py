'''
    data_endpoints.py : this collects the endpoints used by the d3 pages to display
    statistics
'''

from collections import Counter
from operator import itemgetter

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
    logRetrieveNumberOfAccessesPerDay,
    logRetrieveNumberOfNumbersPerDay,
    logNumbersUsageFetch,
    logRetrieveAccessesPerUser,
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
    localDayTimestamp,
    toJavaTimestamp,
    makeJavaDay,
    javaTimestampToTimestamp,
)
from app.utils.logstats import (
    eventDuration,
)
from app.utils.parsing import (
    integerOrDefault,
)

from app.utils.stats import (
    groupByWeekday,
    listToStat,
    statOnListDict,
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

@app.route('/DATA_daily_volumes/<counterid>')
@app.route('/DATA_daily_volumes/<counterid>/<durationthreshold>')
@app.route('/DATA_daily_volumes/<counterid>/<durationthreshold>/<accessthreshold>')
@app.route('/DATA_daily_volumes/<counterid>/<durationthreshold>/<accessthreshold>/<daysBack>')
@login_required
def DATA_daily_volumes(counterid,durationthreshold='0',accessthreshold='0',daysBack=None):
    '''
        Returns a time-plot for the daily count of numbers
        and one for the daily amount-of-visitors,
        with a threshold (duration[seconds], reqtimespan[seconds]) applied to both
    '''
    acc_num=logNumbersUsageFetch(counterid,durationthreshold,accessthreshold,daysBack)
    accesses=acc_num['accesses']
    numbers=acc_num['numbers']
    #
    fullStruct={
        'accesses': sorted(
            [
                {
                    'date': 1000.0*dateStamp,
                    'value': count,
                }
                for dateStamp,count in accesses.items()
            ],
            key=lambda st: st['date'],
        ),
        'numbers': sorted(
            [
                {
                    'date': 1000.0*dateStamp,
                    'value': count,
                }
                for dateStamp,count in numbers.items()
            ],
            key=lambda st: st['date'],
        )
    }
    return jsonify(**fullStruct)

@app.route('/DATA_weekday_volumes/<counterid>')
@app.route('/DATA_weekday_volumes/<counterid>/<durationthreshold>')
@app.route('/DATA_weekday_volumes/<counterid>/<durationthreshold>/<accessthreshold>')
@app.route('/DATA_weekday_volumes/<counterid>/<durationthreshold>/<accessthreshold>/<daysBack>')
@login_required
def DATA_weekday_volumes(counterid,durationthreshold='0',accessthreshold='0',daysBack=None):
    '''
        Returns a double-bar-chart: for the weekday-count of numbers
        and one for the weekday-count-of-visitors.
        Call pattern has the same syntax as DATA_daily_volumes
    '''
    acc_num=logNumbersUsageFetch(counterid,durationthreshold,accessthreshold,daysBack)
    accesses=acc_num['accesses']
    numbers=acc_num['numbers']
    # regroup the numbers in lists, one per weekday
    db=dbOpenDatabase(dbFullName)
    dbTZ=dbGetSetting(db,'WORKING_TIMEZONE')
    wNumberList=groupByWeekday(numbers,dbTZ)
    wAccessList=groupByWeekday(accesses,dbTZ)
    #
    fullStruct={
        'accesses': statOnListDict(wAccessList),
        'numbers': statOnListDict(wNumberList),
    }
    return jsonify(**fullStruct)

@app.route('/DATA_recurring_users/<counterid>')
@app.route('/DATA_recurring_users/<counterid>/<accessthreshold>')
@app.route('/DATA_recurring_users/<counterid>/<accessthreshold>/<daysBack>')
@app.route('/DATA_recurring_users/<counterid>/<accessthreshold>/<daysBack>/<minDaysCut>')
@login_required
def DATA_recurring_users(counterid,accessthreshold='0',daysBack=None,minDaysCut='0'):
    '''
        Returns a double-bar-chart: for the weekday-count of numbers
        and one for the weekday-count-of-visitors.
        Call pattern has syntax similar to DATA_daily_volumes
    '''
    db=dbOpenDatabase(dbFullName)
    dbTZ=dbGetSetting(db,'WORKING_TIMEZONE')
    accessesPerUser=logRetrieveAccessesPerUser(db,dbTZ,counterid,accessthreshold,daysBack,minDaysCut)
    return jsonify(
        [
            {
                'user': accPerU['user'],
                'accesses': [
                    {
                        'date': acc['date']*1000.0,
                        'nrequests': acc['nrequests'],
                    }
                    for acc in accPerU['accesses']
                ]
            }
            for accPerU in accessesPerUser
        ]
    )

@app.route('/DATA_frequent_users/<counterid>')
@app.route('/DATA_frequent_users/<counterid>/<accessthreshold>')
@app.route('/DATA_frequent_users/<counterid>/<accessthreshold>/<daysBack>')
@app.route('/DATA_frequent_users/<counterid>/<accessthreshold>/<daysBack>/<minDaysCut>')
@login_required
def DATA_frequent_users(counterid,accessthreshold='0',daysBack=None,minDaysCut='0'):
    '''
        Returns a simple histogram of frequency for each number-of-days-of-connection-per-user,
        with the same calling syntax as DATA_recurring_users
    '''
    db=dbOpenDatabase(dbFullName)
    dbTZ=dbGetSetting(db,'WORKING_TIMEZONE')
    accessesPerUser=logRetrieveAccessesPerUser(db,dbTZ,counterid,accessthreshold,daysBack,minDaysCut)
    return jsonify(
        [
            {
                'ndays': nTimes,
                'count': uCount,
            }
            for nTimes,uCount in sorted(
                Counter(len(accPerU['accesses']) for accPerU in accessesPerUser).items(),
                key=itemgetter(0),
            )
        ]
    )
