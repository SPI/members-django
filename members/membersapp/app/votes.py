from django.db import connection

from .models import Members


def vote_from_db(row):
    """"Given a row from the vote_election table, return a Vote object"""
    owner = Members.object.get(pk=row['owner'])
    return Vote(row['ref'], row['title'], row['description'],
                row['period_start'], row['period_stop'], owner,
                row['winners'], row['system'])

def get_votes(user, active=None, owner=None):
    """Return all / only active votes from the database."""
    votes = []
    sql = "SELECT * FROM vote_election"
    now = "'now'"

    if active is not None:
        if active:
            sql += ' WHERE period_start <= ' + now
            sql += ' AND period_stop >= ' + now
        else:
            sql += ' WHERE period_start > ' + now
            sql += ' OR period_stop < ' + now

    if owner is not None:
        if active is None:
            sql += ' WHERE'
        else:
            sql += ' AND'
            # Yes, this isn't escaped, but we know it's just a number and
            # not user supplied.
        sql += ' owner = ' + str(owner.id)

    sql += ' ORDER BY ref DESC'

    cur = connection.cursor()
    cur.execute(sql)

    for row in cur.fetchall():
        votes.append(vote_from_db(row))
    return votes
