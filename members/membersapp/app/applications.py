import datetime
import email
import email.header
from smtplib import SMTPException

from django.db import connection
from django.contrib import messages
from django.template import loader
from django.conf import settings
from django.core.mail import send_mail

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


def process_contrib_application(request, form, application, approve_pre_value):
    """Deals with changes to a contributing application by a manager"""
    user = Members.object.get(pk=application.member)

    if form["approve"].data and not approve_pre_value:
        user.iscontrib = True
        user.lastactive = datetime.date.today()
        user.save()
        messages.success(request, 'Applicant become a Contributing member, ' +
                         'emailing them.')
        # Send the welcome confirmation email
        template = loader.get_template('contrib-email.txt')
        context = {
            'user': user
        }
        msg = template.render(context, request)
        subject = 'SPI Contributing Member application for %s' % user.name
        from_field = 'SPI Membership Committee <membership@spi-inc.org>'
        try:
            send_mail(subject, msg, from_field, [user.email], fail_silently=False)
        except (SMTPException, ConnectionRefusedError):
            messages.error(request, 'Unable to send contributing member confirmation email.')
