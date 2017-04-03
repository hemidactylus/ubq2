'''
    dbschema.py : describes the structure of the tables in the db
'''

dbTablesDesc={
    'counters': {                       # STATIC, DESIGNED FEATURES OF THE COUNTER
        'primary_key': ('id', 'TEXT'),  # CC1, EM1 ...
        'columns': [
            ('fullname','TEXT'),        # complete, human readable name
            ('notes','TEXT'),
            ('key', 'INTEGER'),         # a number used on requests to validate the req
            ('mode', 'TEXT'),           # 'a' = active, 'm' = maintenance, 'o' = off; 'p'=private (no show up)
            ('fcolor', 'TEXT'),         # forecolor (number)
            ('bcolor', 'TEXT'),         # backcolor
            ('ncolor', 'TEXT'),         # notes-color (bottom, small font)
        ],
    },
    'counterstatuses': {                # DYNAMIC STATUS DEPENDING ON TIME AND UPDATES
        'primary_key': ('id', 'TEXT'),
        'columns': [
            ('lastupdate','INTEGER'),   # datetime of the last received signal
            ('value', 'INTEGER'),       # the last number received
            ('lastchange','INTEGER'),   # datetime of the last received number-changing signal (incl. wakeup from offline)
            # states w.r.t. notifications
            ('online', 'INTEGER'),      # whether it is considered online or offline w.r.t. wakeups and notifies
            ('tonotify', 'INTEGER'),    # whether the last offline-going event is still to notify
            ('lastnotify', 'INTEGER'),  # datetime of the last alert actually sent out
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
    },
    'settings': {
        'primary_key': ('key', 'TEXT'), # a unique string identifying the setting
        'columns': [
            ('value', 'TEXT'),          # this setting's value - always a string
        ],
    },
    # this stores the historical time-of-permanence (start,stop)
    # in a given status (=a number) for each counter
    'stat_counterstatusspans': {
        'columns': [
            ('counterid',   'TEXT'),    # counter ID
            ('value',       'INTEGER'), # counter value of this timespan
            ('starttime',   'INTEGER'), # datetime(as int) of beginning
            ('endtime',     'INTEGER'), # datetime(as int) of end
        ]
    },
    # this stores the per-user, per-counter, per-day pattern of usage:
    #   time of first and last request, number of requests
    'stat_userusagedays': {
        'columns': [
            ('userid',      'TEXT'),    # userID - a string
            ('counterid',   'TEXT'),    # counter ID
            ('date',        'INTEGER'), # a timestamp expressing an exact date
            ('firstrequest','INTEGER'), # datetime of first request
            ('lastrequest', 'INTEGER'), # datetime of (currently) last request
            ('nrequests',   'INTEGER'), # number of requests received
        ]
    }
}
