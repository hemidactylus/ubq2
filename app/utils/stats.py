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

def listToStat(lst, baseDict):
    '''
        makes a list of numbers into a 'stat' object
        always with 'avg' and 'std' and a number of additional
        provided fields
    '''
    if len(lst)==0:
        retDict={'avg': 0, 'std': 0}
    elif len(lst)==1:
        retDict={'avg': lst[0], 'std': 0}
    else:
        # real stats
        _n=1.0*len(lst)
        secMom=sum(k*k for k in lst)/_n
        firstMom=sum(lst)/_n
        retDict={
            'avg': firstMom,
            'std': (secMom-firstMom**2)**0.5,
        }
    retDict.update(baseDict)
    return retDict

def statOnListDict(ldict):
    '''
        takes a dict of k -> [n1,n2...]
        and makes it into a list of 'weekday-stat-objects',
        i.e. items of the form {'day': 0-6, 'avg': xxx, 'std': yyy}
        handling one- or zero-element lists gracefully
    '''
    return [
        listToStat(v,{'day':k})
        for k,v in ldict.items()
    ]
