from django.db import connection

from .models import Members


def get_applications(self, manager=None):
        """Get all applications, optionally only for a given manager."""
        applications = []
        cur = connection.cursor()
        if manager:
            if self.data['dbtype'] == 'sqlite3':
                cur.execute('SELECT a.*, m.* from applications a, members m ' +
                            'WHERE m.memid = a.member AND a.manager = ? ' +
                            'ORDER BY a.appdate', (manager.memid, ))
            elif self.data['dbtype'] == 'postgres':
                cur.execute('SELECT a.*, m.* from applications a, members m ' +
                            'WHERE m.memid = a.member AND a.manager = %s ' +
                            'ORDER BY a.appdate', (manager.memid, ))
        else:
            cur.execute('SELECT a.*, m.* from applications a, members m ' +
                        'WHERE m.memid = a.member ORDER BY a.appdate')
        for row in cur.fetchall():
            if not manager or manager.memid != row['manager']:
                manager, _ = Members.object.get(pk=row['manager'])
            applications.append(self.application_from_db(row))
        return applications
