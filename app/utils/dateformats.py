'''
    dateformats.py : utilities to deal with formatting timestamps and timeintervals
'''

from datetime import datetime

from config import DATE_FORMAT

def formatTimestamp(tsint):
    return datetime.fromtimestamp(tsint).strftime(DATE_FORMAT)

def formatTimeinterval(tsint):
    '''
        this adapts the display to whatever is the appropriate
        time window. Either:
            days only (>10)
            days, hours (>=24 hours)
            hours, minutes (>=60 minutes)
            minutes, seconds (>=60 seconds)
            seconds (otherwise)
    '''
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
            text = '%i:%02i\'' % (_hours,_mins)
    else:
        if _days<10:
            text = '%id %ih' % (_days,_hours)
        else:
            text = '%i days' % _days
    return text
