'''
    sendMail.py : a utility to handle email from a given gmail address,
    provided a username/appPassword pair is generated.
    
    These and other settings are in mailSettings.py
    
'''

import smtplib
from datetime import datetime
import socket

from mailSettings import (
    gmailServerConnectString,
    senderUsername,
    senderPassword,
    senderFromAddress,
    currentDateFormat,
    emailTextTemplate,
)

def _normaliseList(lst):
    if isinstance(lst,List):
        return lst
    elif isinstance(lst, str) or isinstance(lst, unicode):
        return [lst]

def sendMail(
        mailSubject,
        mailBody,
        recipientList,
        ccList=[],
        bccList=[],
    ):
    '''
        send a text-only email to a list of addresses
        in recipient, cc and bcc destination lists.
        
        Sender is the owner set in the config file.
        
        Signature is set in the config file.

        Addresses are a list of strings or strings for individual entries.
        
    '''
    # open the server and connect
    mailServer = smtplib.SMTP(gmailServerConnectString)
    mailServer.starttls()
    mailServer.login(senderUsername,senderPassword)
    # prepare the email message
    msgObject=smtplib.email.message.Message()
    msgObject.add_header('From',senderFromAddress)
    msgObject.add_header('To', ', '.join(recipientList))
    if ccList:
        msgObject.add_header('Cc', ', '.join(ccList))
    if bccList:
        msgObject.add_header('Bcc', ', '.join(bccList))
    msgObject.add_header('Subject',mailSubject)
    # possibly add signatures to the message body
    completeText=emailTextTemplate.format(
        mailBody=mailBody,
        currentDate=datetime.now().strftime(currentDateFormat),
        hostName=socket.gethostname(),
    )
    msgObject.set_payload(completeText)
    # send the email
    mailServer.send_message(msgObject)
    # done, close the connection
    mailServer.quit()

if __name__=='__main__':
    toaddrs  = ['someone@email.server.address']
    ccaddrs = []
    bccaddrs = []
    msgText = 'Aaa\nBbb\nCcc'
    msgSubject='Sub Ject'

    sendMail(
        msgSubject,
        msgText,
        toaddrs,
        ccaddrs,
        bccaddrs,
    )
    
    print('Done.')
