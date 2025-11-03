#!/usr/bin/python

import datetime
from dateutil.relativedelta import relativedelta
import base64

from django.core.management.base import BaseCommand, CommandError
from django.template import loader
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q, Max
from django.contrib.auth.models import User
from django.core import signing
from django.utils import timezone

from membersapp.app.models import Members, VoteElection
from membersapp.account.util.propagate import send_change_to_apps


NO_VOTE = 0
VOTE = 1


class Command(BaseCommand):
    help = 'Deal with sending notifications to or cleaning up inactive SPI contributing members'
    vote_case = None

    def get_case(self):
        last_vote = VoteElection.objects.aggregate(Max('period_start'))['period_start__max']
        if last_vote is None or (datetime.datetime.now(datetime.timezone.utc) - relativedelta(years=1) > last_vote):
            print("No vote happened in a year. Last vote was on " + str(last_vote))
            self.vote_case = NO_VOTE
        else:
            print("A vote happened within a year, on " + str(last_vote))
            self.vote_case = VOTE

    def add_arguments(self, parser):
        parser.add_argument('action', choices=['clean', 'ping'],
                            help="Clean or only ping inactive members.")
        parser.add_argument('--dry-run', dest='dryrun',
                            help="Just show what would happen, don't take any action",
                            action='store_const', const=True, default=False)

    def get_concerned_members(self):
        if self.vote_case == VOTE:
            max_date = VoteElection.objects.filter(period_start__lt=timezone.now()).aggregate(Max('period_start'))['period_start__max']
        else:
            max_date = datetime.datetime.now(datetime.timezone.utc) - relativedelta(years=1)
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

    def generate_update_id(self, member):
        token = signing.dumps({'user_id': member.pk})
        b64_token = base64.urlsafe_b64encode(token.encode()).decode()
        return b64_token

    def send_ping(self, dryrun):
        pingable_members = self.get_concerned_members()
        if self.vote_case == VOTE:
            template = loader.get_template('activity-ping-email.txt')
        else:
            template = loader.get_template('activity-ping-email-novote.txt')
        if dryrun and len(pingable_members) > 0:
            print("***** Dry run *****")
        for member in pingable_members:
            print("Sending ping to %s" % member.name)
            context = {
                'name': member.name,
                'update_id': self.generate_update_id(member)
            }
            msg = template.render(context)
            if not dryrun:
                send_mail('SPI activity ping for %s' % member.name, msg, 'SPI Membership Committee <membership@spi-inc.org>', [member.email], fail_silently=False)

    def handle(self, *args, **options):
        self.get_case()
        if options['action'] == 'clean':
            self. clean_contrib(options['dryrun'])
        elif options['action'] == 'ping':
            self. send_ping(options['dryrun'])
