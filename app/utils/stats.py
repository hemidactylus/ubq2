'''
    stats.py : miscellaneous utilities to apply statistics, regroupings, etc
'''

from app.utils.dateformats import (
    localDateFromTimestamp,
)

def groupByWeekday(numberTimelineDict,dbTZ):
    '''
        reduces a dict date->number
        to a dict weekday->[n1,n2,...]

        weekdays are numbers, 0 is Monday
    '''
    wDict={wd: [] for wd in range(7)}
    for dt,nb in numberTimelineDict.items():
        wDict[localDateFromTimestamp(dt,dbTZ).weekday()].append(nb)
    return wDict

def listToStat(lst):
    '''
        makes a list of numbers into a 'stat' object
        with 'avg' / 'std' if possible
    '''
    if len(lst)==0:
        return {}
    elif len(lst)==1:
        return {'avg': lst[0]}
    else:
        # real stats
        _n=1.0*len(lst)
        secMom=sum(k*k for k in lst)/_n
        firstMom=sum(lst)/_n
        return {
            'avg': firstMom,
            'std': (secMom-firstMom**2)**0.5,
        }

def statOnListDict(ldict):
    '''
        takes a dict of k -> [n1,n2...]
        and makes it into a k -> {'avg': X, 'std': X},
        handling one- or zero-element lists gracefully
    '''
    return {
        k: listToStat(v)
        for k,v in ldict.items()
    }
