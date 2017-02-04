'''
    dbschema.py : describes the structure of the tables in the db
'''

dbTablesDesc={
    'counters': {                      # STATIC, DESIGNED FEATURES OF THE COUNTER
        'primary_key': ('id', 'TEXT'), # CC1, EM1 ...
        'columns': [
            ('fullname','TEXT'),       # complete, human readable name
            ('notes','TEXT'),
            ('key', 'INTEGER'),        # a number used on requests to validate the req
            ('mode', 'TEXT'),          # 'a' = active, 'm' = maintenance, 'o' = off; 'p'=private (no show up)
            ('fcolor', 'TEXT'),        # forecolor (number)
            ('bcolor', 'TEXT'),        # backcolor
            ('ncolor', 'TEXT'),        # notes-color (bottom, small font)
        ],
    },
    'counterstatuses': {                 # DYNAMIC STATUS DEPENDING ON TIME AND UPDATES
        'primary_key': ('id', 'TEXT'),
        'columns': [
            ('lastupdate','INTEGER'),  # datetime of the last received signal
            ('lastchange','INTEGER'),  # datetime of the last received number-changing signal
            ('value', 'INTEGER'),      # the number held in the counter
            ('status', 'TEXT'),        # current status comparing last-update and current time
            # MISSING: email sent / not sent / back to normal
        ],
    },
    'users': {
        'primary_key': ('username', 'TEXT'),
        'columns': [
            ('fullname', 'TEXT'),
            ('passwordhash','TEXT'),
            ('email', 'TEXT'),
            ('subscribed', 'INTEGER'),
        ],
    }
}
