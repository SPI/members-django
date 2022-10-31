#!/usr/bin/python

import urllib.request
import ssl
import sys

from django.core.management.base import BaseCommand, CommandError
from django.template import loader
from django.conf import settings
from django.core.mail import send_mail

from pglister.lists.models import SubscriberAddress, List, ListSubscription


class Command(BaseCommand):
    help = 'Prompt the members application for contributing members list and subscribe them to the spi-private mailing list'

    def add_arguments(self, parser):
        parser.add_argument('hostname',
                            help="Hostname of target URL, to be used in header of request.")
        parser.add_argument('--dry-run', dest='dryrun',
                            help="Just show what would happen, don't take any action",
                            action='store_const', const=True, default=False)
        parser.add_argument('--url', dest='url',
                            help="URL of the members application",
                            action='store', default='https://localhost')

    def handle(self, *args, **options):
        url = '%s/privatesubs' % options['url']
        r = urllib.request.Request(url, headers={'Host': options['hostname']})
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        response = urllib.request.urlopen(r, context=ctx)
        data = response.read()
        addresses = data.decode('utf-8').split('\n')
        try:
            subprivate = List.objects.get(name='spi-private')
        except List.DoesNotExist:
            print("Error: spi-private does not exist. Please create it in pglister's admin interface")
            sys.exit(1)
        for address in addresses:
            print("Subscribing %s to spi-private" % address)
            if not options['dryrun']:
                subscriber = SubscriberAddress.objects.get(email=address)
                subscription = ListSubscription(list=subprivate, subscriber=subscriber)
                subscriber.save()
