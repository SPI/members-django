from django.db import models
from django.contrib.auth.models import User
from django.db.models.functions import Now


class Members(models.Model):
    memid = models.OneToOneField(User, null=False, blank=False, primary_key=True, on_delete=models.RESTRICT, db_column='memid', db_constraint=False)
    email = models.CharField(max_length=50, null=False, unique=True)  # for linking with pgweb
    name = models.CharField(max_length=50, null=False)
    phone = models.CharField(max_length=20, null=True)
    pgpkey = models.CharField(max_length=50, null=True)
    firstdate = models.DateField(null=True)
    expirydate = models.DateField(null=True)
    iscontrib = models.BooleanField(null=False, blank=False, default=False)
    ismanager = models.BooleanField(null=False, blank=False, default=False)
    sub_private = models.BooleanField(default=False, null=False, verbose_name='Subscribe to spi-private?')
    lastactive = models.DateField(null=True)
    createvote = models.BooleanField(null=False, blank=False, default=False)

    object = models.Manager()

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'members'


class Applications(models.Model):
    appid = models.AutoField(null=False, primary_key=True)
    appdate = models.DateField(null=True)
    member = models.ForeignKey(Members, null=False, blank=False, db_column='member', on_delete=models.DO_NOTHING, related_name='app2member', db_constraint=False)
    emailkey = models.CharField(max_length=50, null=True)
    emailkey_date = models.DateField(null=True)
    validemail = models.BooleanField(null=True)
    validemail_date = models.DateField(null=True)
    contrib = models.TextField(null=True, verbose_name='Contributions')
    comment = models.TextField(null=True, verbose_name='Mgr Comments')
    lastchange = models.DateField(null=True)
    manager = models.ForeignKey(Members, null=True, blank=True, db_column='manager', on_delete=models.RESTRICT, related_name='app2manager', limit_choices_to={'ismanager': True})
    manager_date = models.DateField(null=True, verbose_name='Date Assigned')
    approve = models.BooleanField(null=True)
    approve_date = models.DateField(null=True)
    contribapp = models.BooleanField(null=True, default=False)

    def __str__(self):
        return "{0} ({1})".format(self.member, self.appdate)

    class Meta:
        db_table = 'applications'

    @property
    def get_status(self):
        """Return the member status for this application"""
        if self.contrib is not None:
            return 'CM'
        elif self.contribapp:
            return 'CA'
        elif self.approve:
            return 'NCM'
        else:
            return 'NCA'


class VoteElection(models.Model):
    ref = models.AutoField(null=False, primary_key=True)
    title = models.CharField(max_length=256, null=False)
    description = models.TextField(null=True)
    period_start = models.DateTimeField(auto_now_add=True, null=True)
    period_stop = models.DateTimeField(null=True)
    owner = models.ForeignKey(Members, null=False, blank=False, db_column='owner', on_delete=models.RESTRICT)
    winners = models.IntegerField(null=False, default=1)
    system = models.IntegerField(null=False)

    object = models.Manager()

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'vote_election'


class VoteOption(models.Model):
    ref = models.AutoField(null=False, primary_key=True)
    election_ref = models.ForeignKey(VoteElection, null=False, blank=False, db_column='election_ref', on_delete=models.RESTRICT)
    description = models.TextField(null=True)
    sort = models.IntegerField(null=False)
    option_character = models.CharField(max_length=1, null=False)

    def __str__(self):
        return self.description

    class Meta:
        unique_together = (('election_ref', 'sort'), ('election_ref', 'option_character'))
        db_table = 'vote_option'


class VoteVote(models.Model):
    ref = models.AutoField(null=False, primary_key=True)
    voter_ref = models.ForeignKey(Members, null=True, blank=False, db_column='voter_ref', on_delete=models.RESTRICT)
    election_ref = models.ForeignKey(VoteElection, null=False, blank=False, db_column='election_ref', on_delete=models.RESTRICT)
    private_secret = models.CharField(max_length=32, null=True)
    late_updated = models.DateTimeField(auto_now=True, null=True)  # missing: with time zone
    sent_notify = models.BooleanField(null=False, default=False)

    class Meta:
        unique_together = (('voter_ref', 'election_ref'), )
        db_table = 'vote_vote'

    @property
    def is_active(self):
        """"Check if a vote is currently active"""
        now = Now()
        return self.start <= now <= self.end

    @property
    def is_over(self):
        """"Check if a voting period is over"""
        now = Now()
        return now > self.end

    @property
    def is_pending(self):
        """"Check if a vote is still waiting to be active"""
        now = datetime.datetime.utcnow()
        return now < self.start


class VoteVoteOption(models.Model):
    vote_ref = models.ForeignKey(VoteVote, null=False, blank=False, db_column='vote_ref', on_delete=models.RESTRICT)
    option_ref = models.ForeignKey(VoteOption, null=False, blank=False, db_column='option_ref', on_delete=models.RESTRICT)
    preference = models.IntegerField(null=True)

    class Meta:
        unique_together = (('vote_ref', 'option_ref'), )
        db_table = 'vote_voteoption'


# These tables do not seem to be used, even though they exist in production

# class VoteLog(models.Model):
#     ref = models.AutoField(null=False, primary_key=True)
#     time = models.DateTimeField(auto_now_add=True, null=False)
#     source_ip = models.CharField(max_length=255, null=True)
#     vote_caset = models.CharField(max_length=255, null=True)
#     vote_ref = models.ForeignKey(VoteVote, null=False, blank=False, db_column='vote_ref', on_delete=models.RESTRICT)
#     who = models.ForeignKey(VoteVoter, null=False, blank=False, db_column='who', on_delete=models.RESTRICT)

#     class Meta:
#         db_table = 'vote_log'

# class VoteSession(models.Model):
#     ref = models.AutoField(null=False, primary_key=True)
#     vote_session_id = models.CharField(max_length=256, null=False, unique=True, db_column='id')  # todo: merge with ref?
#     data = models.BinaryField(null=True)
#     last_seen = models.DateTimeField(auto_now=True)

#     class Meta:
#         db_table = 'vote_session'

# class VoteVoter(models.Model):
#     ref = models.ForeignKey(Members, null=False, blank=False, db_column='ref', on_delete=models.RESTRICT)
#     session_ref = models.IntegerField(null=True)

#     class Meta:
#         db_table = 'vote_voter'
