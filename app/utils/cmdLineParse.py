'''
    cmdLineParse.py : a simple tool to automatically parse the general command line arguments passed to a script
'''

def cmdLineParse(alist):
    '''
        transforms a list of cmdline arguments in a pair:
            - list of "free" args
            - dict of "options", each with a name and a list of provided items
            
        Example:
            ./command one two three -a -b 10 -c pp qq rr
        returns:
            ['one','two','three'] , {'a': [], 'b': ['10'], 'c': ['pp', 'qq', 'rr']}
    '''
    aDict={}
    freeElems=[]
    while alist:
        qarg=alist.pop(0)
        if qarg[:1]=='-':
            nItem=[]
            while True and alist:
                if alist[0][:1]!='-':
                    nItem.append(alist.pop(0))
                else:
                    break
            aDict[qarg[1:]]=nItem
        else:
            freeElems.append(qarg)
    return freeElems,aDict
