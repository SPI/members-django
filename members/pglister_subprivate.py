#!/usr/bin/python

import urllib.request

from django.core.management.base import BaseCommand, CommandError
from django.template import loader
from django.conf import settings
from django.core.mail import send_mail

# from pglister.lists import


class Command(BaseCommand):
    help = 'Prompt the members application for contributing members list and subscribe them to the spi-private mailing list'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', dest='dryrun',
                            help="Just show what would happen, don't take any action",
                            action='store_const', const=True, default=False)

    def handle(self, *args, **options):
        url = 'https://beta.membersdjango.spi-inc.org/subprivate'
        response = urllib.request.urlopen(url)
        data = response.read()
        addresses = data.decode('utf-8').split('\n')
