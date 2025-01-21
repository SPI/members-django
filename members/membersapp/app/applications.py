import datetime
import email
import email.header
from smtplib import SMTPException

from django.contrib.auth.models import User
from django.db import connection
from django.db.models import Q
from django.contrib import messages
from django.template import loader
from django.conf import settings
from django.core.mail import send_mail

from .models import Members, Applications
from .utils import *
from membersapp.account.util.propagate import send_change_to_apps


def process_contrib_application(request, form, application):
    """Deals with changes to a contributing application by a manager"""
    user = Members.object.get(pk=application.member)

    if form["approve"].data and not user.iscontrib:
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
        send_change_to_apps(User.objects.get(pk=user.pk), status=True)


def get_applications_by_type(listtype):
    if listtype == 'nca':
        applications = Applications.objects.filter(Q(member__ismember=False))
    elif listtype == 'ncm':
        applications = Applications.objects.filter(Q(member__ismember=True) & Q(member__iscontrib=False) & (Q(contribapp=False) | Q(contribapp__isnull=True)))
    elif listtype == 'ca':
        applications = Applications.objects.filter(Q(member__ismember=True) & Q(approve__isnull=True) & Q(contribapp=True))
    elif listtype == 'cm':
        applications = Applications.objects.filter(Q(member__iscontrib=True) & Q(contribapp=True))
    elif listtype == 'mgr':
        applications = Applications.objects.filter(Q(member__ismanager=True))
    elif listtype == 'all':
        applications = Applications.objects.all()
    else:
        applications = None
    return applications
