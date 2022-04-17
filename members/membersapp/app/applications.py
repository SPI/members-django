from django.db import connection

from .models import Members, Applications
from .utils import *


def get_applications(manager=None):
    """Get all applications, optionally only for a given manager."""
    if manager:
        applications = Applications.objects.filter(manager=manager.memid_id)
    else:
        applications = Applications.objects.all()
    return applications


def get_applications_by_user(user):
    """Retrieve all applications for the supplied user."""
    applications = Applications.objects.filter(member=user.memid_id)
    return applications
