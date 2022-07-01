from django.db import connection

from .models import Members


VOTE_SYSTEMS = [(0, "Condorcet (ignore unspecified)"),
                (1, "Condorcet (unspecified ranked lowest)"),
                (2, "Scottish STV"),
                ]
