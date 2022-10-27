#!/usr/bin/python

from django.core.management.base import BaseCommand, CommandError
from django.template import loader
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q, Max

from membersapp.app.models import Members, VoteElection


class Command(BaseCommand):
    help = 'Deal with cleaning up inactive SPI contributing members'

    def add_arguments(self, parser):
        parser.add_argument('action', choices=['clean', 'ping'],
                            help="Clean or only ping inactive members.")
        parser.add_argument('--dry-run', dest='dryrun',
                            help="Just show what would happen, don't take any action",
                            action='store_const', const=True, default=False)

    def get_concerned_members(self):
        max_date = VoteElection.objects.aggregate(Max('period_start'))['period_start__max']
        concerned_members = Members.objects.filter(Q(iscontrib=True) & Q(lastactive__lt=max_date))
        return concerned_members

    def clean_contrib(self, dryrun):
        downgradable_members = self.get_concerned_members()
        for member in downgradable_members:
            print("Downgrading %s to non-contributing" % member.name)
            if dryrun is False:
                member.iscontrib = False
                member.save()

    def send_ping(self, dryrun):
        pingable_members = self.get_concerned_members()
        template = loader.get_template('activity-ping-email.txt')
        for member in pingable_members:
            print("Sending ping to %s" % member.name)
            context = {
                'name': member.name
            }
            msg = template.render(context)
            if not dryrun:
                send_mail('SPI activity ping for %s' % member.name, msg, 'SPI Membership Committee <membership@spi-inc.org>', user.email, fail_silently=False)

    def handle(self, *args, **options):
        if options['action'] == 'clean':
            self. clean_contrib(options['dryrun'])
        elif options['action'] == 'ping':
            self. send_ping(options['dryrun'])
