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

