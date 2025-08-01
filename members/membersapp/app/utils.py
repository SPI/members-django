from .models import Members, Applications


def get_member_by_id(memid):
    try:
        member = Members.objects.get(pk=memid)
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


def get_current_user(request):
    try:
        return Members.objects.get(pk=request.user.pk)
    except Members.DoesNotExist:
        return None
