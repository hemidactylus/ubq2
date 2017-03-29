import os
from datetime import time

# directories and so on
basedir = os.path.abspath(os.path.dirname(__file__))

# stuff for Flask
WTF_CSRF_ENABLED = True
from sensible_config import SECRET_KEY

# official service name
UBQ_SERVICE_FULLNAME='UBQ [www.salamandrina.net/ubq]'

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
APP_COMPLETE_ADDRESS='http://www.salamandrina.net/ubq'

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

# Usage tracking level: True uses cookies, False relies on User-Agent
USE_ANONYMOUS_COOKIES=True

# DERIVED VARIABLES - do not edit below this line (theoretically)
dbFullName=os.path.join(DB_DIRECTORY,DB_NAME)
