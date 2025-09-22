#!/usr/bin/python

import urllib.request
import ssl
import sys
import json

from django.core.management.base import BaseCommand, CommandError
from django.template import loader
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import User

from pglister.lists.models import SubscriberAddress, List, ListSubscription, Subscriber
from lib.baselib.misc import generate_random_token


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
        parser.add_argument('--verbose', dest='verbose',
                            help="Print more information about subscriptions",
                            action='store_const', const=True, default=False)

    def handle(self, *args, **options):
        try:
            spiprivate = List.objects.get(name='spi-private')
        except List.DoesNotExist:
            print("Error: spi-private does not exist. Please create it in pglister's admin interface", file=sys.stderr)
            sys.exit(1)
        url = '%s/privatesubs' % options['url']
        r = urllib.request.Request(url, headers={'Host': options['hostname']})
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        response = urllib.request.urlopen(r, context=ctx)
        data = response.read()
        text_data = data.decode()
        users = json.loads(text_data)
        previous_subcriptions = ListSubscription.objects.filter(list=spiprivate)
        addresses = [x["members__email"] for x in users]
        for subscription in previous_subcriptions:
            if str(subscription.subscriber) not in addresses:
                print("%s no longer subscribed, removing subscription" % subscription.subscriber)
                if not options['dryrun']:
                    subscription.delete()
            elif options['verbose']:
                print("%s remains subscribed" % subscription.subscriber)
        for user in users:
            if not User.objects.filter(username=user["username"]).exists():
                print("User %s does not exist, creating them" % user["username"])
                new_user = User(username=user["username"], first_name=user["first_name"], last_name=user["last_name"], email=user["members__email"])
                if not options['dryrun']:
                    new_user.save()
            try:
                subscriber = SubscriberAddress.objects.get(email=user["members__email"])
                if subscriber.subscriber_id is None:
                    sub = Subscriber.objects.filter(user__email=subscriber.email).first()
                    if sub is not None:
                        print("Linking subscriber address %s to user %s" % (subscriber.email, sub.pk))
                        if not options['dryrun']:
                            subscriber.subscriber = sub
                            subscriber.save()
            except SubscriberAddress.DoesNotExist:
                print("Subscriber %s does not exist, creating them" % user["members__email"])
                subscriber = SubscriberAddress(email=user["members__email"], confirmed=True, blocked=False, token=generate_random_token())
                if not options['dryrun']:
                    subscriber.save()
            if ListSubscription.objects.filter(list=spiprivate, subscriber=subscriber).exists():
                ls = ListSubscription.objects.get(list=spiprivate, subscriber=subscriber)
                if not (ls.nomail != user["members__sub_private"]):
                    print("Changing subscriber %s subscription to %s" % (user["members__email"], user["members__sub_private"]))
                    if not options['dryrun']:
                        ls.nomail = not user["members__sub_private"]
                        ls.save()
                if options['verbose']:
                    print("%s already subscribed to spi-private" % user["members__email"])
                continue
            print("Subscribing %s to spi-private" % user["members__email"])
            if not options['dryrun']:
                subscription = ListSubscription(list=spiprivate, subscriber=subscriber, nomail=not user["members__sub_private"])
                subscription.save()
