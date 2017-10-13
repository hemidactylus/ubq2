import os
from datetime import time

# directories and so on
basedir = os.path.abspath(os.path.dirname(__file__))

# stuff for Flask
WTF_CSRF_ENABLED = True
from sensible_config import SECRET_KEY

# database settings
DB_DIRECTORY=os.path.join(basedir,'app/database')
DB_NAME='ubq2.db'
DB_DEBUG=False

# iframe embed code template
IFRAME_EMBED_CODE='''<iframe
    src="{prefix}{url}"
    height="110" width="110"
    style="width: 100px; height: 100px; overflow-y: hidden;"
    scrolling="no" 
    seamless="seamless">
</iframe>'''
APP_COMPLETE_ADDRESS='https://www.salamandrina.net'

# official service name
UBQ_SERVICE_FULLNAME='UBQ [%s]' % APP_COMPLETE_ADDRESS

# counter appearance settings
NOT_FOUND_COUNTER_MESSAGE='(no info)'
NOT_FOUND_COUNTER_VALUE='--'
COUNTER_OFF_MESSAGE='Counter OFF'
COUNTER_OFF_VALUE='--'
COUNTER_MAINTENANCE_MESSAGE='Maintenance'
COUNTER_MAINTENANCE_VALUE='--'
COUNTER_OFFLINE_MESSAGE_TEMPLATE='Off for %s'
COUNTER_OFFLINE_VALUE='--'
DEFAULT_COUNTER_COLORS={
    'fcolor': 'Gold',
    'bcolor': 'Black',
    'ncolor': '#00F0A0',
}
DEFAULT_COUNTER_MODE='o'
MODE_ICON_MAP={
    'o': 'fa-times-circle',
    'a': 'fa-check-circle',
    'm': 'fa-wrench',
    'p': 'fa-key',
}
DATE_FORMAT='%b %d, %H:%M'
LONG_DATE_FORMAT='%b %d, %Y - %H:%M:%S'
ALERT_DATE_FORMAT='%Y/%m/%d %H:%M:%S'

# Debug option for redirecting email to stdout (and no email)
REDIRECT_EMAIL_TO_STDOUT=False

# Template for sending out email alerts
EMAIL_OFFLINE_ALERT_SUBJECT='UBQ Counter {counterid} offline alert'
EMAIL_OFFLINE_ALERT_BODY='''UBQ Alert:
counter "{countername}" ({counterid}) offline for more than {alerttimeout} seconds.

Counter ID: {counterid}.
Counter name: {countername}.
Counter description: {counternotes}.

You receive this email since your account on {servicename} has email notifications turned on and the time-window condition is currently met.'''
EMAIL_ONLINE_ALERT_SUBJECT='UBQ Counter {counterid} is back online'
EMAIL_ONLINE_ALERT_BODY='''UBQ Counter Back Online:
counter "{countername}" ({counterid}) is online again.

Counter ID: {counterid}.
Counter name: {countername}.
Counter description: {counternotes}.

You receive this email since your account on {servicename} has email notifications turned on and the time-window condition is currently met.'''

# Template for sending 'illegal access' email
EMAIL_ILLEGAL_ACCESS_SUBJECT='UBQ - Unauthorized access attempt detected!'
EMAIL_ILLEGAL_ACCESS_BODY='''UBQ Security warning:
an unauthorized access attempt has been received.

Request details:

** Headers:
{reqHeaders}

** Cookies:
{reqCookies}

** Request Url:
{reqUrl}

** Remote Address:
{reqRemoteAddr}

You receive this email since your account on {servicename} has email notifications turned on.'''

PERFORM_USER_IDENTIFICATION=True
# Usage tracking level: True uses cookies, False relies on User-Agent
USE_ANONYMOUS_COOKIES=True
COOKIE_DURATION_SECONDS=86400*365 # i.e. one year

# trigger checkbeat verbosity
TRIGGER_CHECKBEAT_VERBOSE=False

# DERIVED VARIABLES - do not edit below this line (theoretically)
dbFullName=os.path.join(DB_DIRECTORY,DB_NAME)
