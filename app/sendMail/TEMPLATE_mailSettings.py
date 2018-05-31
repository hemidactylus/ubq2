'''
    mailSettings.py: configuration for the sendMail utilities
'''

# Do not let other people get hold of these settings.

mailServerConnectString='smtp.fastmail.com:587'
senderUsername='USERNAME@gmail.com'
senderPassword='APPLICATION_PASSWORD'
senderFromAddress = 'NAME <USERNAME@gmail.com>'
currentDateFormat='%Y/%m/%d %H:%M:%S'
emailTextTemplate='{mailBody}\n\n[Message auto-generated on {hostName} at {currentDate}]'
