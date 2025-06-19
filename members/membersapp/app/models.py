import hashlib

from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.db.models.functions import Now
from django.core.validators import MinValueValidator
from django.db.models import Q


class Members(models.Model):
    memid = models.OneToOneField(User, null=False, blank=False, primary_key=True, on_delete=models.RESTRICT, db_column='memid')
    email = models.CharField(max_length=50, null=False, unique=True)  # for linking with pgweb
    name = models.CharField(max_length=50, null=False)
    ismember = models.BooleanField(null=False, blank=False, default=False)
    iscontrib = models.BooleanField(null=False, blank=False, default=False)
    ismanager = models.BooleanField(null=False, blank=False, default=False)
    sub_private = models.BooleanField(default=False, null=False, verbose_name='Subscribe to spi-private?')
    lastactive = models.DateField(null=True)
    createvote = models.BooleanField(null=False, blank=False, default=False)

    object = models.Manager()
    objects = models.Manager()

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'members'

    @property
    def downgraded_user(self):
        if self.iscontrib:
            return False
        return (len(Applications.objects.filter(Q(member=self) & Q(contribapp=True) & Q(approve=True))) > 0)

    @property
    def get_status(self):
        """Return the member status"""
        if not self.ismember:
            return 'nm'
        elif not self.iscontrib:
            return 'ncm'
        else:
            return 'cm'


class Applications(models.Model):
    appid = models.AutoField(null=False, primary_key=True)
    appdate = models.DateField(null=True)
    member = models.ForeignKey(Members, null=False, blank=False, db_column='member', on_delete=models.RESTRICT, related_name='app2member')
    contrib = models.TextField(null=True, verbose_name='Contributions')
    comment = models.TextField(null=True, verbose_name='Manager Comments')
    lastchange = models.DateField(null=True)
    manager = models.ForeignKey(Members, null=True, blank=True, db_column='manager', on_delete=models.RESTRICT, related_name='app2manager', limit_choices_to={'ismanager': True})
    manager_date = models.DateField(null=True, verbose_name='Date Assigned')
    approve = models.BooleanField(null=True)
    approve_date = models.DateField(null=True)
    contribapp = models.BooleanField(null=True, default=False)
    emailcheck_date = models.DateField(null=True)
    validemail = models.BooleanField(null=True)
    validemail_date = models.DateField(null=True)

    object = models.Manager()
    objects = models.Manager()

    def __str__(self):
        return "{0} ({1})".format(self.member, self.appdate)

    class Meta:
        db_table = 'applications'

    @property
    def get_status(self):
        """Return the member status for this application"""
        if self.member.iscontrib:
            return 'CM'
        elif self.contribapp:
            return 'CA'
        else:
            return 'NCM'


class VoteElection(models.Model):
    ref = models.AutoField(null=False, primary_key=True)
    title = models.CharField(max_length=256, null=False, verbose_name='Vote title')
    period_start = models.DateTimeField(null=True, verbose_name='Start date', validators=[MinValueValidator(timezone.now)])
    period_stop = models.DateTimeField(null=True, verbose_name='End date', validators=[MinValueValidator(timezone.now)])
    owner = models.ForeignKey(Members, null=False, blank=False, db_column='owner', on_delete=models.RESTRICT)

#    object = models.Manager()
#    objects = models.Manager()

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'vote_election'

    @property
    def is_active(self):
        """"Check if a vote is currently active"""
        now = timezone.now()
        return self.period_start <= now <= self.period_stop

    @property
    def is_over(self):
        """"Check if a voting period is over"""
        now = timezone.now()
        return now > self.period_stop

    @property
    def is_pending(self):
        """"Check if a vote is still waiting to be active"""
        now = timezone.now()
        return now < self.period_start


class VoteBallot(models.Model):
    ref = models.AutoField(primary_key=True)
    election_ref = models.ForeignKey(VoteElection, db_column='election_ref', on_delete=models.RESTRICT)
    title = models.CharField(max_length=256, null=False, verbose_name='Ballot title')
    description = models.TextField(null=True)
    winners = models.IntegerField(null=False, default=1, validators=[MinValueValidator(1)])
    system = models.IntegerField(null=False, verbose_name='Voting system')
    allow_blank = models.BooleanField(default=True, verbose_name='Allow blank votes')

    class Meta:
        db_table = 'vote_ballot'

    def __str__(self):
        return self.title


class VoteOption(models.Model):
    ref = models.AutoField(null=False, primary_key=True)
    ballot_ref = models.ForeignKey(VoteBallot, null=False, blank=False, db_column='ballot_ref', on_delete=models.RESTRICT)
    description = models.TextField(null=True)
    sort = models.IntegerField(null=False)
    option_character = models.CharField(max_length=1, null=False)

    object = models.Manager()
    objects = models.Manager()

    def __str__(self):
        return self.description

    class Meta:
        unique_together = (('ballot_ref', 'sort'), ('ballot_ref', 'option_character'))
        db_table = 'vote_option'


class VoteVote(models.Model):
    ref = models.AutoField(null=False, primary_key=True)
    voter_ref = models.ForeignKey(Members, null=True, blank=False, db_column='voter_ref', on_delete=models.RESTRICT)
    ballot_ref = models.ForeignKey(VoteBallot, null=False, blank=False, db_column='ballot_ref', on_delete=models.RESTRICT)
    private_secret = models.CharField(max_length=32, null=True)
    late_updated = models.DateTimeField(auto_now=True, null=True)  # missing: with time zone
    sent_notify = models.BooleanField(null=False, default=False)
    votes = []

    object = models.Manager()
    objects = models.Manager()

    class Meta:
        unique_together = (('voter_ref', 'ballot_ref'), )
        db_table = 'vote_vote'

    def __init__(self, *args, **kwargs):
        super(VoteVote, self).__init__(*args, **kwargs)
        self.votes = [x.option_ref for x in VoteVoteOption.objects.filter(vote_ref=self.ref).order_by('preference')]

    @property
    def votestr(self):
        """Returns a string representing the user's voting preference."""
        res = ""
        for vote in self.votes:
            res += vote.option_character
        return res

    @property
    def resultcookie(self):
        """Returns the user's secret cookie for voting verification."""
        md5 = hashlib.md5()
        if self.voter_ref is None:
            email = None
        else:
            email = self.voter_ref.email
        md5.update(str(self.private_secret).encode('utf-8') + b" " + str(email).encode('utf-8') + b"\n")
        return md5.hexdigest()

    def set_vote(self, votestr):
        """Update the user's voting preference based on the voting string."""

        newvotes = []
        for char in votestr:
            try:
                option = VoteOption.object.get(Q(option_character=char) & Q(ballot_ref=self.ballot_ref))
            except VoteOption.DoesNotExist:
                return "Invalid vote option " + char
            if option in newvotes:
                return "Can't vote for " + char + " more than once."
            newvotes.append(option)
        self.votes = newvotes
        return None


class VoteVoteOption(models.Model):
    vote_ref = models.ForeignKey(VoteVote, null=False, blank=False, db_column='vote_ref', on_delete=models.RESTRICT)
    option_ref = models.ForeignKey(VoteOption, null=False, blank=False, db_column='option_ref', on_delete=models.RESTRICT)
    preference = models.IntegerField(null=True)

    class Meta:
        unique_together = (('vote_ref', 'option_ref'), )
        db_table = 'vote_voteoption'
