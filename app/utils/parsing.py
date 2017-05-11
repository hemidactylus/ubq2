'''
    parsing.py : miscellaneous utilities to transform data
'''

def integerOrDefault(text, default=None):
    '''
        if it is not an integer expression, return None,
        else return the integer
    '''
    try:
        qNum=int(text)
    except:
        qNum=default
    return qNum
