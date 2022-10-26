#!/usr/bin/python

import datetime
from smtplib import SMTPException

from django.core.management.base import BaseCommand, CommandError
from django.template import loader
from django.conf import settings
from django.core.mail import send_mail

from membersapp.app.stats import get_stats


class Command(BaseCommand):
    help = 'Send email containing stats on members and applications'

    def add_arguments(self, parser):
        parser.add_argument('--email', dest='email',
                            help="Email address to send message",
                            action='store', default='board@spi-inc.org, membership@spi-inc.org')
        parser.add_argument('--dry-run', dest='dryrun',
                            help="Just show what would happen, don't take any action",
                            action='store_const', const=True, default=False)

    def handle(self, *args, **options):
        template = loader.get_template('stats.txt')
        context = {
            'stats': get_stats(),
            'date': '{:%F %T}'.format(datetime.datetime.today())
        }
        msg = template.render(context)
        if not options['dryrun']:
            try:
                send_mail('SPI membership statistics', msg, 'SPI Membership Committee <membership@spi-inc.org>', options['email'].split(","), fail_silently=False)
            except (SMTPException, ConnectionRefusedError):
                raise CommandError('Unable to send contributing member confirmation email.')
        else:
            self.stdout.write(msg)
