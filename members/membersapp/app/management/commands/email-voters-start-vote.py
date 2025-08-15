#!/usr/bin/python

from datetime import timedelta

from django.utils import timezone
from django.core.management.base import BaseCommand, CommandError
from django.template import loader
from django.conf import settings
from django.core.mail import send_mail

from membersapp.app.models import VoteElection, VoteBallot, VoteVote, Applications, Members
from membersapp.app.applications import get_applications_by_type


class Command(BaseCommand):
    help = 'Email contributing members about open votes + populate data for quorum'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', dest='dryrun',
                            help="Just show what would happen, don't take any action",
                            action='store_const', const=True, default=False)

    def send_email(self, user, vote, new, dryrun, incorrect=False):
        if new:
            template = loader.get_template('vote-begin.txt')
            subject = 'SPI vote open: %s' % vote.title
            print("Emailing voter %s (%s) regarding opening of vote %s" % (user.name, user.email, vote.ref))
        elif incorrect:
            template = loader.get_template('vote-incorrect.txt')
            subject = "Error: vote cannot be run due to incorrect configuration : %s" % vote.title
            print("Emailing owner %s (%s) regarding incorrect configuration of vote %s" % (user.name, user.email, vote.ref))
        else:
            template = loader.get_template('vote-mid.txt')
            subject = 'SPI vote reminder: %s' % vote.title
            print("Emailing voter %s (%s) regarding reminder for vote %s" % (user.name, user.email, vote.ref))
        context = {
            'user': user,
            'vote': vote
        }
        msg = template.render(context)
        if not dryrun:
            try:
                send_mail(subject, msg, 'SPI Membership Committee <membership@spi-inc.org>', [user.email], fail_silently=False)
            except (SMTPException, ConnectionRefusedError):
                raise CommandError('Unable to send voting information email to user %s (%s) regarding vote %s.' % (user.name, user.email, vote.ref))

    def inform_voters(self, vote, new=False, dryrun=False):
        voters = set()
        ballots = VoteBallot.objects.filter(election_ref=vote)
        for ballot in ballots:
            for x in VoteVote.objects.filter(ballot_ref=ballot):
                voters.add(x.voter_ref.memid)
        for app in get_applications_by_type('cm'):
            if app.member.memid not in voters:
                self.send_email(app.member, vote, new, dryrun)

    def handle(self, *args, **options):
        votes = [x for x in VoteElection.objects.all() if x.is_active]
        for vote in votes:
            if not vote.is_runnable:
                vote.period_start += timedelta(days=3)
                vote.save()
                self.send_email(vote.owner, vote, False, options['dryrun'], True)
            else:
                now = timezone.now()
                mid = vote.period_start + timedelta(seconds=(vote.period_stop -
                                                             vote.period_start).total_seconds() / 2)
                if now - timedelta(hours=24) < vote.period_start <= now:
                    if vote.nb_contrib is not None:
                        print("Error: vote was already started. Not emailing voters to avoid double email.")
                    else:
                        self.inform_voters(vote, new=True, dryrun=options['dryrun'])
                        if not options['dryrun']:
                            vote.nb_contrib = Members.objects.filter(iscontrib=True).count()
                            vote.save()
                            print("Number of contributing members at start of vote: %s" % vote.nb_contrib)
                elif now - timedelta(hours=24) < mid <= now:
                    self.inform_voters(vote, new=False, dryrun=options['dryrun'])
