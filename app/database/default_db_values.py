'''
    default_db_values.py : initial values for some non-sensitive tables
'''

default_settings=[
    {
        'key'           : 'COUNTER_OFFLINE_TIMEOUT',
        'value'         : '60',
    },
    {
        'key'           : 'COUNTER_ALERT_TIMEOUT',
        'value'         : '600',
    },
    {
        'key'           : 'ALERT_WINDOW_START',
        'value'         : '9:20',
    },
    {
        'key'           : 'ALERT_WINDOW_END',
        'value'         : '11:35',
    },
    {
        'key'           : 'WORKING_TIMEZONE',
        'value'         : 'Europe/Rome',
    },
    {
        'key'           : 'CHECKBEAT_FREQUENCY',
        'value'         : '10',
    },
    {
        'key'           : 'COUNTER_BACK_ONLINE_TIMESPAN',
        'value'         : '18000',
    },
]
