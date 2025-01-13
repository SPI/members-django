#!/usr/bin/python

from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from django.core.management.base import BaseCommand, CommandError
from django.template import loader
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q, Max
from django.contrib.auth.models import User

from membersapp.app.models import Members, VoteElection
from membersapp.account.util.propagate import send_change_to_apps


class Command(BaseCommand):
    help = 'Deal with sending notifications to or cleaning up inactive SPI contributing members'

    def add_arguments(self, parser):
        parser.add_argument('action', choices=['clean', 'ping'],
                            help="Clean or only ping inactive members.")
        parser.add_argument('--dry-run', dest='dryrun',
                            help="Just show what would happen, don't take any action",
                            action='store_const', const=True, default=False)

    def get_concerned_members(self):
        max_date = max(VoteElection.objects.aggregate(Max('period_start'))['period_start__max'],
                       datetime.now(timezone.utc) - relativedelta(years=1))
        concerned_members = Members.objects.filter(Q(iscontrib=True) & Q(lastactive__lt=max_date))
        return concerned_members

    def clean_contrib(self, dryrun):
        downgradable_members = self.get_concerned_members()
        if dryrun and len(downgradable_members) > 0:
            print("***** Dry run *****")
        for member in downgradable_members:
            print("Downgrading %s to non-contributing" % member.name)
            if dryrun is False:
                member.iscontrib = False
                member.save()
                send_change_to_apps(User.objects.get(pk=member.pk), status=True)

    def send_ping(self, dryrun):
        pingable_members = self.get_concerned_members()
        template = loader.get_template('activity-ping-email.txt')
        if dryrun and len(pingable_members) > 0:
            print("***** Dry run *****")
        for member in pingable_members:
            print("Sending ping to %s" % member.name)
            context = {
                'name': member.name
            }
            msg = template.render(context)
            if not dryrun:
                send_mail('SPI activity ping for %s' % member.name, msg, 'SPI Membership Committee <membership@spi-inc.org>', [member.email], fail_silently=False)

    def handle(self, *args, **options):
        if options['action'] == 'clean':
            self. clean_contrib(options['dryrun'])
        elif options['action'] == 'ping':
            self. send_ping(options['dryrun'])
