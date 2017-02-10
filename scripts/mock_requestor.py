'''
    mock_requestor.py : simulates a progression of numbers
'''

from time import sleep, time
import sys
import requests
from random import randint

reqSettings={
    'counterid':  'LM1',
    'mindelay' :     10,
    'maxdelay' :     50,
    'key'      : 123456,
    'minincr'  :      1,
    'maxincr'  :     10,
    'url'      : 'http://localhost:5000/update1.php',
}

responseDesc={
    0: 'OK   ',
    1: '!args',
    2: '!key ',
    3: '!req ',
}

def main():
    # parse command line
    _args=sys.argv[1:]
    argTrouble=[]
    while _args:
        qarg=_args.pop(0)
        if qarg=='-set':
            if len(_args)>=2:
                k=_args.pop(0)
                v=_args.pop(0)
                if k in reqSettings:
                    try:
                        reqSettings[k]=type(reqSettings[k])(v)
                    except:
                        argTrouble+=['Cannot set "%s" to "%s"' % (k,v)]
                        break
                else:
                    argTrouble+=['Unknown setting: "%s"' % k]
                    break
            else:
                argTrouble+=['Wrong specifications after -set']
                break
        elif qarg=='-h':
            argTrouble+=['Help needed']
            break
        else:
            argTrouble+=['Malformed command-line options']
            break
    #
    if argTrouble:
        print('Errors in command line:')
        print('\n'.join('    %s' % msg for msg in argTrouble))
        print('Usage: <cmd> [-h | [-s key val [-s key val [...]]]]')
        print('Keys:')
        print('\n'.join('    %s => %s' % (k,v) for k,v in reqSettings.items()))
        return
    #
    cntVal=0
    print('Starting requestor')
    while True:
        cntVal=(cntVal+randint(reqSettings['minincr'],reqSettings['maxincr'],))%100
        print('[%i] Sending val=%2i ...' % (int(time()),cntVal), end='')
        reqText='%s?N=%i&K=%i' % (reqSettings['url'],cntVal,reqSettings['key'])
        answer=int(requests.get(reqText).text)
        print(' => %s. ' % responseDesc[int(answer)], end='')
        sleepTime=randint(reqSettings['mindelay'],reqSettings['maxdelay'])
        print('Sleeping %i seconds.' % sleepTime)
        sleep(sleepTime)

if __name__=='__main__':
    main()
