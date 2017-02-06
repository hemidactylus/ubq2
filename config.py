import os

# directories and so on
basedir = os.path.abspath(os.path.dirname(__file__))

# stuff for Flask
WTF_CSRF_ENABLED = True
from sensible_config import SECRET_KEY

# database settings
DB_DIRECTORY=os.path.join(basedir,'app/database')
DB_NAME='ubq2.db'
DB_DEBUG=False

# DERIVED VARIABLES - do not edit below this line (theoretically)
dbFullName=os.path.join(DB_DIRECTORY,DB_NAME)

# counter appearance settings
NOT_FOUND_COUNTER_MESSAGE='(no info)'
NOT_FOUND_COUNTER_VALUE='--'
COUNTER_OFF_MESSAGE='Counter OFF'
COUNTER_OFF_VALUE='--'
COUNTER_MAINTENANCE_MESSAGE='Maintenance'
COUNTER_MAINTENANCE_VALUE='--'
COUNTER_OFFLINE_MESSAGE_TEMPLATE='Offline for %s'
COUNTER_OFFLINE_VALUE='--'

DATE_FORMAT='%b %d, %H:%M'

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
