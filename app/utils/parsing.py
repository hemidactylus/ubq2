'''
    parsing.py : miscellaneous utilities to transform data
'''

def integerOrNone(text):
    '''
        if it is not an integer expression, return None,
        else return the integer
    '''
    try:
        qNum=int(text)
    except:
        qNum=None
    return qNum
