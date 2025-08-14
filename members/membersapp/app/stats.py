from django.db import connection

from .models import Members


def type_to_sql(listtype):
    """Build the WHERE clause for looking up members by type"""
    t = 'true'
    f = 'false'

    if listtype == 'nca':
        where = 'AND (m.ismember = false OR m.ismember IS NULL)'
    elif listtype == 'ncm':
        where = ('AND m.ismember = true AND m.iscontrib = false ' +
                 ' AND (contribapp = false OR contribapp IS NULL)')
    elif listtype == 'ca':
        where = ('AND m.ismember = true AND a.approve IS NULL AND ' +
                 'contribapp = true')
#    elif listtype == 'cm':
#        where = ('AND m.ismember = true AND m.iscontrib = true '
#                 ' AND contribapp = true')
    elif listtype == 'mgr':
        where = ('AND m.ismember = true AND m.ismanager = true '
                 ' AND contribapp = true')
    else:
        where = ''

    return where


def get_stats():
    """Retrieve membership statistics"""
    stats = {}

    for listtype in ['nca', 'ncm', 'ca', 'mgr']:
        where = type_to_sql(listtype)
        with connection.cursor() as cursor:
            cursor.execute('SELECT COUNT(memid) AS count FROM applications a, ' +
                           'members m WHERE m.memid = a.member ' + where)
            row = cursor.fetchone()
        if row:
            stats[listtype] = row[0]

    # An elected NCM director becomes contrib automatically, which
    # means that all contrib members won't necessarily have an
    # application. Hence, count contrib members directly instead of
    # using applications
    stats['cm'] = Members.objects.filter(iscontrib=True).count()

    return stats
