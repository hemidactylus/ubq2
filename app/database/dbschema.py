'''
    dbschema.py : describes the structure of the tables in the db
'''

dbTablesDesc={
    'counters': {
        'primary_key': ('id', 'TEXT'),
        'columns': [
            ('name','TEXT'),
            ('lastupdate','INTEGER'),
            ('value', 'INTEGER'),
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
