from django.db import connection

from .models import Members, Applications
from .utils import *


def get_applications(self, manager=None):
    """Get all applications, optionally only for a given manager."""
    applications = []
    cur = connection.cursor()
    if manager:
        cur.execute('SELECT a.*, m.* from applications a, members m ' +
                    'WHERE m.memid = a.member AND a.manager = %s ' +
                    'ORDER BY a.appdate', (manager.memid, ))
    else:
        cur.execute('SELECT a.*, m.* from applications a, members m ' +
                    'WHERE m.memid = a.member ORDER BY a.appdate')
    for row in dictfetchall(cur):
        if not manager or manager.memid != row['manager']:
            manager = get_member_by_id(row['manager'])
        applications.append(application_from_db(row))
    return applications
