import os

# directories and so on
basedir = os.path.abspath(os.path.dirname(__file__))

# stuff for Flask
WTF_CSRF_ENABLED = True
from sensible_config import SECRET_KEY

# database settings
DB_DIRECTORY=os.path.join(basedir,'app/database')
DB_NAME='ubq2.db'
DB_DEBUG=True

# DERIVED VARIABLES - do not edit below this line (theoretically)
dbFullName=os.path.join(DB_DIRECTORY,DB_NAME)

# counter appearance settings
NOT_FOUND_COUNTER_MESSAGE='(no info)'
NOT_FOUND_COUNTER_VALUE='--'
