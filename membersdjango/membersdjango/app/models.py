from django.db import models

class Members(models.model):
    memid = models.AutoField(null=False, primary_key=True)
    name = models.CharField(max_length=50, null=False)
    email = models.CharField(max_length=50, null=False)
    phone = models.CharField(max_length=20)
    password = models.CharField(max_length=15, null=False)
    pgpkey = models.CharField(max_length=50)
    firstdate = models.DateTimeField()
    expirydate = models.DateTimeField()
    ismember = models.BooleanField(null=False, blank=False, default=False)
    iscontrib = models.BooleanField(null=False, blank=False, default=False)
    ismanager = models.BooleanField(null=False, blank=False, default=False)
    sub_private = models.BooleanField( default=False)
    lastactive = models.DateTimeField()
    createvote = models.BooleanField(null=False, blank=False, default=False)

    class Meta:
        db_table = 'members'


class Applications(models.model):
    appid = models.AutoField(null=False, primary_key=True)
    appdate = models.DateTimeField()
    member = models.ForeignKey(Members, null=False, blank=False, db_column='member', on_delete=models.RESTRICT)
    emailkey = models.CharField(max_length=50)
    emailkey_date = models.DateTimeField()
    validemail = models.BooleanField()
    validemail_date = models.DateTimeField()
    contrib = models.TextField()
    comment = models.TextField()
    lastchange = models.DateTimeField()
    manager = models.ForeignKey(Members, null=False, blank=False, db_column='mamager', on_delete=models.RESTRICT)
    manager_date = models.DateTimeField()
    approve = models.BooleanField()
    approve_date = models.DateTimeField()
    contribapp = models.BooleanField(default=False)

    class Meta:
        db_table = 'applications'


class VoteElection(models.model):
    ref = models.AutoField(null=False, primary_key=True)
    title = models.CharField(max_length=256, null=False)
    description = models.TextField()
    period_start = models.DateTimeField(auto_add_now=True)
    period_stop = models.DateTimeField()
    owner = models.ForeignKey(Members, null=False, blank=False, db_column='owner', on_delete=models.RESTRICT)
    winners = models.IntegerField(null=False, default=1)
    system = models.IntegerField(null=False)

    class Meta:
        db_table = 'vote_election'


class VoteOption(models.model):
    ref = models.AutoField(null=False, primary_key=True)
    election_ref = models.ForeignKey(VoteElection, null=False, blank=False, db_column='election_ref', on_delete=models.RESTRICT)
    description = models.TextField()
    sort = models.IntegerField(null=False)
    option_character = models.CharField(max_length=1, null=False)

    class Meta:
        unique_together = (('election_ref', 'sort'), ('election_ref', 'option_character'))
        db_table = 'vote_option'


class VoteVote(models.model):
    ref = models.AutoField(null=False, primary_key=True)
    voter_ref = models.ForeignKey(Members, null=False, blank=False, db_column='voter_ref', on_delete=models.RESTRICT)
    election_ref = models.ForeignKey(VoteElection, null=False, blank=False, db_column='election_ref', on_delete=models.RESTRICT)
    private_secret = models.CharField(max_length=32)
    last_updated = models.DateTimeField(auto_now=True) # missing: with time zone
    send_notify = models.BooleanField(null=False, default=False)

    class Meta:
        unique_together = (('voter_ref', 'election_ref'), )
        db_table = 'vote_vote'


class VoteVoteOption(models.model):
    vote_ref = models.ForeignKey(VoteVote, null=False, blank=False, db_column='vote_ref', on_delete=models.RESTRICT)
    option_ref = models.ForeignKey(VoteOption, null=False, blank=False, db_column='option_ref', on_delete=models.RESTRICT)
    preference = models.IntegerField()

    class Meta:
        unique_together = (('vote_ref', 'option_ref'), )
        db_table = 'vote_voteoption'


# These tables do not seem to be used, even though they exist in production

#class VoteLog(models.model):
#    ref = models.AutoField(null=False, primary_key=True)
#    time = models.DateTimeField(auto_add_now=True, null=False)
#    source_ip = models.CharField(max_length=255)
#    vote_caset = models.CharField(max_length=255)
#    vote_ref = models.ForeignKey(VoteVote, null=False, blank=False, db_column='vote_ref', on_delete=models.RESTRICT)
#    who = models.ForeignKey(VoteVoter, null=False, blank=False, db_column='who', on_delete=models.RESTRICT)

#    class Meta:
#        db_table = 'vote_log'

#class VoteSession(models.model):
#    ref = models.AutoField(null=False, primary_key=True)
#    vote_session_id = models.CharField(max_length=256, null=False, unique=True, db_column='id')  # todo: merge with ref?
#    data = models.BinaryField()
#    last_seen = models.DateTimeField(auto_now=True)

#    class Meta:
#        db_table = 'vote_session'

#class VoteVoter(models.model):
#    ref = models.ForeignKey(Members, null=False, blank=False, db_column='ref', on_delete=models.RESTRICT)
#    session_ref = models.IntegerField()

#    class Meta:
#        db_table = 'vote_voter'
    
