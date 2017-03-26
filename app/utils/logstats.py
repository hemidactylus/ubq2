'''
    logstats.py : utilities for performing reductions and transformations
    to yield statistics on all kinds of usage
'''

# settings for the interval-duration statistics.
# Minutes, 0 to 60 and ">60"
EV_DURATION_CONSTANT=30
EV_DURATION_DIVISOR=60
EV_DURATION_MINVAL=0
EV_DURATION_MAXVAL=61

def eventDuration(ev):
    '''
        returns an integer expressing the duration time for the event.
        At the moment it is in minutes and rounded to the closest
    '''
    evDuration=int((EV_DURATION_CONSTANT+ev.endtime-ev.starttime)/EV_DURATION_DIVISOR)
    if evDuration>EV_DURATION_MAXVAL:
        evDuration=EV_DURATION_MAXVAL
    if evDuration<EV_DURATION_MINVAL:
        evDuration=EV_DURATION_MINVAL
    return evDuration
