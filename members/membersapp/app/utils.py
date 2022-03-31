from .models import Members, Applications


def get_member_by_id(memid):
    try:
        member = Members.object.get(pk=memid)
    except Members.DoesNotExist:
        member = None
    return member


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def member_from_db(row):
    """Given a row dict from the members table, return a Member object"""
    return Members(row['memid'], row['email'], row['name'], row['password'],
                   row['firstdate'], row['iscontrib'], row['ismanager'],
                   row['ismember'], row['sub_private'], row['createvote'],
                   row['lastactive'])


def application_from_db(row, manager=None):
    """Return an application object for a given database result."""
    user = member_from_db(row)
    if not manager or manager.memid != row['manager']:
        manager = get_member_by_id(row['manager'])
    return Applications(user, manager, row['appid'],
                       row['appdate'], row['approve'], row['approve_date'],
                       row['contribapp'],
                       row['emailkey'], row['emailkey_date'],
                       row['validemail'], row['validemail_date'],
                       row['contrib'], row['comment'], row['manager_date'],
                       row['lastchange'])
