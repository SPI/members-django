from django.db import connection


def type_to_sql(listtype):
    """Build the WHERE clause for looking up members by type"""
    t = 'true'
    f = 'false'

    if listtype == 'ncm':
        where = ('AND m.iscontrib = false ' +
                 ' AND (contribapp = false OR contribapp IS NULL)')
    elif listtype == 'ca':
        where = ('AND a.approve IS NULL AND ' +
                 'contribapp = true')
    elif listtype == 'cm':
        where = ('AND m.iscontrib = true '
                 ' AND contribapp = true')
    elif listtype == 'mgr':
        where = ('AND m.ismanager = true '
                 ' AND contribapp = true')
    else:
        where = ''

    return where


def get_stats():
    """Retrieve membership statistics"""
    stats = {}

    for listtype in ['ncm', 'ca', 'cm', 'mgr']:
        where = type_to_sql(listtype)
        with connection.cursor() as cursor:
            cursor.execute('SELECT COUNT(memid) AS count FROM applications a, ' +
                           'members m WHERE m.memid = a.member ' + where)
            row = cursor.fetchone()
        if row:
            stats[listtype] = row[0]

    return stats
