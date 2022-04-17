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
