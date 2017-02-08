'''
    dateformats.py : utilities to deal with formatting timestamps and timeintervals
'''

from datetime import datetime
import pytz

from config import (
    DATE_FORMAT,
)

def localDateFromTimestamp(ts,tzonedesc):
    '''
        using the timezone settings, extracts
        a localised datetime from a (utc) timestamp
    '''
    locDate=pytz.utc.localize(datetime.utcfromtimestamp(ts),is_dst=None)
    return locDate.astimezone(pytz.timezone(tzonedesc))

def stringToTimestamp(timestr):
    '''
        "18:44" to time(18,44,0)
    '''
    return datetime.strptime(timestr,'%H:%M').time()

def formatTimestamp(tsint, tzonedesc):
    return localDateFromTimestamp(tsint,tzonedesc).strftime(DATE_FORMAT)

def formatTimeinterval(_tsint):
    '''
        this adapts the display to whatever is the appropriate
        time window. Either:
            days only (>10)
            days, hours (>=24 hours)
            hours, minutes (>=60 minutes)
            minutes, seconds (>=60 seconds)
            seconds (otherwise)
    '''
    tsint=int(_tsint/5)*5
    _secs=int(tsint % 60)
    _mins=int((tsint / 60) % 60)
    _hours=int((tsint / 3600) % 24)
    _days=int((tsint / 86400))
    if _days==0:
        if _hours==0:
            if _mins==0:
                text = '%i sec' % _secs
            else:
                text = '%i\'%02i\'\'' % (_mins,_secs)
        else:
            text = '%ih %02i\'' % (_hours,_mins)
    else:
        if _days<10:
            text = '%id %ih' % (_days,_hours)
        else:
            text = '%i days' % _days
    return text
