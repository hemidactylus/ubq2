'''
    staticValues.py : naming maps and similar for a pretty interface
'''

counterModes=[
    ('a','Active'),
    ('m','Maintenance'),
    ('o','Off'),
    ('p','Private'),
]
counterModeMap={p[0]:p[1] for p in counterModes}

alertTypes=[
    ('cannot_send_email_alert','Error sending email'),
    ('offline_alert','Offline alert'),
    ('online_alert','Online alert'),
    ('illegal_access_alert','Illegal access alert'),
]
alertTypeMap={p[0]:p[1] for p in alertTypes}
