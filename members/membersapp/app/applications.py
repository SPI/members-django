from django.db import connection

from .models import Members, Applications
from .utils import *


def get_applications(manager=None):
    """Get all applications, optionally only for a given manager."""
    applications = []
    cur = connection.cursor()
    if manager:
        cur.execute('SELECT a.*, m.* from applications a, members m ' +
                    'WHERE m.memid = a.member AND a.manager = %s ' +
                    'ORDER BY a.appdate', (manager.memid_id, ))
    else:
        cur.execute('SELECT a.*, m.* from applications a, members m ' +
                    'WHERE m.memid = a.member ORDER BY a.appdate')
    for row in dictfetchall(cur):
        if not manager or manager.memid_id != row['manager']:
            manager = get_member_by_id(row['manager'])
        applications.append(application_from_db(row))
    return applications


def get_applications_by_user(user):
        """Retrieve all applications for the supplied user."""
        applications = Applications.objects.filter(member=user.memid_id)
        return applications
