'''
    mailTest.py : sendmail credentials test
'''

import env
from app.sendMail.sendMail import sendMail
from app.sendMail.mailSettings import senderUsername

if __name__=='__main__':
    print('Sendmail test...')
    sendMail("Test Sendmail","Hello, there",[senderUsername])
    print('Test done.')
