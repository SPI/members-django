import datetime
import hashlib
import uuid

from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.template import loader
from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.views.generic.edit import UpdateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.core.mail import send_mail

from membersapp.app.stats import get_stats
from membersapp.app.applications import *
from .models import Members, Applications, VoteElection, VoteBallot, VoteOption, VoteVote, VoteVoteOption
from .forms import *
from .votes import *
from membersapp.account.util.propagate import send_change_to_apps
from membersapp.account.models import SecondaryEmail


def handler404(request, exception):
    """Return a suitable 404 page for unhandled URLs"""
    user = get_current_user(request)
    template = loader.get_template('404.html')
    context = {
        'user': user
    }
    return HttpResponseNotFound(template.render(context, request))


def index(request):
    """Handler for main page. Displays users details."""
    if not request.user.is_authenticated:
        template = loader.get_template('index.html')
        context = {}
        return HttpResponse(template.render(context, request))
    else:
        template = loader.get_template('status.html')
        user = get_current_user(request)
        auth_user = User.objects.get(id=user.memid_id)
        form = MemberForm(instance=user)
        contribapp = (len(Applications.objects.filter(Q(member=user) & Q(contribapp=True))) > 0)
        downgraded_user = user.downgraded_user
        context = {
            'active_votes': VoteElection.objects.filter(Q(period_start__lte=timezone.now()) & Q(period_stop__gte=timezone.now())),
            'user_votes': VoteElection.objects.filter(owner=user),
            'applications': Applications.objects.filter(member=user),
            'applicants': Applications.objects.filter(manager=user),
            'contribapp': contribapp,
            'downgraded_user': downgraded_user,
            'user': user,
            'auth_user': auth_user,
            'form': form,
            'other_email_addresses': SecondaryEmail.objects.filter(user=user.pk).values_list('email', flat=True)
        }
        return HttpResponse(template.render(context, request))


@login_required
def application(request, appid):
    """Handler for viewing a specific application."""
    template = loader.get_template('application.html')
    application = get_object_or_404(Applications, appid=appid)
    user = get_current_user(request)
    if not user.ismanager and not application.member == user:
        return render(request, 'manager-only.html')
    member = Members.object.get(memid=application.member_id)
    memberform = MemberForm(instance=member)
    if user.ismanager:
        # Manager view of the contrib application
        applicationform = ApplicationForm(instance=application)
    else:
        # user view of the contrib application
        applicationform = ContribApplicationForm(instance=application)
    context = {
        'application': application,
        'member': member,
        'user': user,
        'memberform': memberform,
        'applicationform': applicationform
    }
    return HttpResponse(template.render(context, request))


@login_required
def updateactive(request):
    """Update a users most recently active date and redirect to main page"""
    user = get_current_user(request)
    user.lastactive = datetime.date.today()
    if user.downgraded_user:
        user.iscontrib = True
        messages.success(request, 'Retrieved contributing member status!')
    user.save()
    messages.success(request, '"Last active" date set to current date')
    send_change_to_apps(User.objects.get(pk=user .pk), status=True)
    return HttpResponseRedirect("/")


def showstats(request):
    """Handler for showing membership statistics"""
    stats = get_stats()
    user = get_current_user(request)
    return render(request, 'stats.html', {'stats': stats, 'user': user})


@login_required
def showapplications(request, listtype):
    """Handler for listing applications; managers only."""
    template = loader.get_template('applications.html')
    user = get_current_user(request)
    if not user.ismanager:
        return render(request, 'manager-only.html')
    template = loader.get_template('applications.html')
    applications = get_applications_by_type(listtype)
    if applications is None:
        messages.error(request, "Unknown application type!")
        return HttpResponseRedirect("/")
    sorted_applications = applications.order_by('appid')
    context = {
        'applicants': sorted_applications,
        'listtype': listtype,
        'user': user
    }
    return HttpResponse(template.render(context, request))


@login_required
def showvotes(request):
    """Handler for listing votes"""
    user = get_current_user(request)
    if not user.iscontrib:
        return render(request, 'contrib-only.html')
    template = loader.get_template('votes.html')
    votes = VoteElection.objects.order_by('-period_start')
    context = {
        'user': user,
        'votes': votes,
    }
    return HttpResponse(template.render(context, request))


@login_required
def showvote(request, ref):
    """Handler for viewing a specific vote."""
    user = get_current_user(request)
    if not user.iscontrib:
        return render(request, 'contrib-only.html')
    vote = get_object_or_404(VoteBallot, ref=ref)
    options = VoteOption.objects.filter(ballot_ref=ref)
    if len(options) < 2:
        messages.error(request, 'Error: vote does not have enough options to run.')
        return HttpResponseRedirect("/")
    template = loader.get_template('vote.html')
    form = VoteVoteForm(initial={'allow_blank': vote.allow_blank})
    try:
        membervote = VoteVote.object.get(voter_ref=user, ballot_ref=vote)
    except VoteVote.DoesNotExist:
        membervote = None
    context = {
        'user': user,
        'vote': vote,
        'options': options,
        'form': form,
        'membervote': membervote
    }
    return HttpResponse(template.render(context, request))


@login_required
def votevote(request, ref):
    """Handler for registering a vote."""
    user = get_current_user(request)
    vote = get_object_or_404(VoteElection, ref=ref)
    if not user.iscontrib:
        return render(request, 'contrib-only.html')
    if not vote.is_active:
        messages.error(request, 'Vote is not currently running.')
        return HttpResponseRedirect(reverse('vote', args=[ref]))
    if request.method == 'POST':
        form = VoteVoteForm(request.POST)
        membervote, created = VoteVote.object.get_or_create(voter_ref=user, election_ref=vote)
        if created:
            md5 = hashlib.md5()
            md5.update(vote.title.encode('utf-8'))
            md5.update(user.email.encode('utf-8'))
            md5.update(uuid.uuid1().hex.encode('utf-8'))
            membervote.private_secret = md5.hexdigest()
        if form.is_valid():
            if vote.is_active and membervote:
                if request.POST['vote'] != membervote.votestr:
                    res = membervote.set_vote(request.POST['vote'])
                    if res is not None:
                        messages.error(request, res)
                    else:
                        # Remove any previous vote details first
                        VoteVoteOption.objects.filter(vote_ref=membervote).delete()
                        for i, voteoption in enumerate(membervote.votes, 1):
                            votevoteoption = VoteVoteOption(vote_ref=membervote, option_ref=voteoption)
                            votevoteoption.save()
                        membervote.save()
                        user.lastactive = datetime.date.today()
                        user.save()
    return HttpResponseRedirect(reverse('vote', args=[ref]))


@login_required
def showmember(request, memid):
    """Handler for viewing a member"""
    user = get_current_user(request)
    if not user.ismanager:
        return render(request, 'manager-only.html')
    template = loader.get_template('member.html')
    member = get_object_or_404(Members, pk=memid)
    auth_user = User.objects.get(id=memid)
    context = {
        'user': user,
        'member': member,
        'auth_user': auth_user,
        'applications': Applications.objects.filter(member=member),
        'applicants': Applications.objects.filter(manager=member).order_by('appid'),
        'other_email_addresses': SecondaryEmail.objects.filter(user=member.pk).values_list('email', flat=True)
    }
    return HttpResponse(template.render(context, request))


@login_required
def memberedit(request):
    """Handler for editing member details"""
    if request.method == 'POST':
        user = get_current_user(request)
        form = MemberForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
    return HttpResponseRedirect(reverse('index'))


@login_required
def applicationedit(request, appid):
    """Handler for non-contributing membership application."""
    user = get_current_user(request)
    if request.method == 'POST':
        application = Applications.objects.get(pk=appid)
        memberform = MemberForm(request.POST, instance=application.member)
        if user.ismanager:
            applicationform = ApplicationForm(request.POST, instance=application)
            # caution: is_valid() modifies objects
            if memberform.is_valid() and applicationform.is_valid():
                memberform.save()
                applicationform.save()
                # This step must be done after others, otherwise changes on user
                # will be reverted
                process_contrib_application(request, applicationform, application)
        else:
            applicationform = ContribApplicationForm(request.POST, instance=application)
            if memberform.is_valid() and applicationform.is_valid() and application.member == user:
                memberform.save()
                applicationform.save()
                if settings.SEND_NOTIFICATION_EMAILS:
                    try:
                        template = loader.get_template('contribapp_updated.txt')
                        context = {
                            'username': user.name,
                            'appid': application.appid
                        }
                        msg = template.render(context)
                        send_mail('Contributing application updated', msg, 'SPI Membership Committee <membership@spi-inc.org>', [settings.NOTIFICATION_EMAILS_DESTINATION], fail_silently=False)
                    except (SMTPException, ConnectionRefusedError):
                        raise CommandError('Unable to send email to membership committee.')
    return HttpResponseRedirect(reverse('application', args=[appid]))


@login_required
def contribapplication(request):
    """Handler for contributing membership application."""
    user = get_current_user(request)
    if user.iscontrib:
        messages.error(request, 'You are already an SPI contributing member')
        return HttpResponseRedirect("/")
    applications = Applications.objects.filter(member=user)
    for apps in applications:
        if apps.contribapp and apps.approve is None:
            messages.warning(request, 'You already have an outstanding SPI contributing ' +
                             'membership application.')
            return HttpResponseRedirect("/")
    if request.method == 'POST':
        user = get_current_user(request)
        memberform = MemberForm(request.POST, instance=user)
        contribappform = ContribApplicationForm(request.POST)
        if memberform.is_valid() and contribappform.is_valid():
            memberform.save()
            contribapp = Applications(member=user,
                                      appdate=datetime.date.today(),
                                      lastchange=datetime.date.today(),
                                      contribapp=True,
                                      contrib=contribappform["contrib"].data)
            contribapp.save()
            user.last_active = datetime.date.today()
            user.save()
            if settings.SEND_NOTIFICATION_EMAILS:
                try:
                    template = loader.get_template('contribapp_new.txt')
                    context = {
                        'username': user.name,
                        'appid': contribapp.appid
                    }
                    msg = template.render(context)
                    send_mail('New contributing application', msg, 'SPI Membership Committee <membership@spi-inc.org>', [settings.NOTIFICATION_EMAILS_DESTINATION], fail_silently=False)
                except (SMTPException, ConnectionRefusedError):
                    raise CommandError('Unable to send email to membership committee.')
        else:
            print(memberform.errors.as_data(), contribappform.errors.as_data())
        return HttpResponseRedirect(reverse('index'))
    template = loader.get_template('contrib-application.html')
    user = get_current_user(request)
    memberform = MemberForm(instance=user)
    contribappform = ContribApplicationForm()
    context = {
        'user': user,
        'memberform': memberform,
        'contribappform': contribappform
    }
    return HttpResponse(template.render(context, request))


@login_required
def votecreate(request):
    """Handler that creates a new vote."""
    user = get_current_user(request)
    if not user.createvote:
        messages.error(request, 'You are not allowed to create new votes')
        return HttpResponseRedirect("/")

    if request.method == 'POST':
        user = get_current_user(request)
        form = CreateVoteForm(request.POST, prefix='election')
        form_ballot = CreateVoteFormBallot(request.POST, prefix='ballot')
        if form.is_valid() and form_ballot.is_valid():
            form.instance.owner = user
            # match behaviour of previous application by setting end date to
            # end of the day
            form.instance.period_stop += datetime.timedelta(hours=23, minutes=59, seconds=59)
            new_vote = form.save()
            ballot = form_ballot.save(commit=False)
            ballot.election_ref = new_vote
            form_ballot.save()
            return HttpResponseRedirect(reverse('voteedit', args=(new_vote.pk,)))
        else:
            messages.error(request, "Error while filling the form:")
            if not form.is_valid():
                messages.error(request, form.errors)
            if not form_ballot.is_valid():
                messages.error(request, form_ballot.errors)
            # Fall back to showing regular create page

    template = loader.get_template('vote-create.html')
    createvoteform = CreateVoteForm(prefix='election')
    createvoteformballot = CreateVoteFormBallot(prefix='ballot')
    context = {
        'user': user,
        'createvoteform': createvoteform,
        'createvoteformballot': createvoteformballot
    }
    return HttpResponse(template.render(context, request))


def tests_vote(request, user, vote):
    """Checks common to different voting-related functions"""
    if not user.createvote:
        messages.error(request, 'You are not allowed to create new votes')
        return False
    if vote.owner != user:
        messages.error(request, 'You can only edit your own votes.')
        return False
    if vote.is_active or vote.is_over:
        messages.error(request, 'Vote must not have run to be edited.')
        return False
    return True


@login_required
def voteeditedit(request, ref):
    """Handler for editing a vote."""
    user = get_current_user(request)
    vote = get_object_or_404(VoteElection, ref=ref)

    if not tests_vote(request, user, vote):
        return HttpResponseRedirect("/")

    if request.method == 'POST':
        if request.POST['vote-btn'] == "Edit":
            form = EditVoteForm(request.POST, instance=vote)
            if form.is_valid():
                form.instance.owner = user
                form.save()
            else:
                messages.error(request, "Error while filling the form:")
                messages.error(request, form.errors)
            return HttpResponseRedirect(reverse('voteedit', args=(ref,)))
        elif request.POST['vote-btn'] == "Delete":
            VoteOption.objects.filter(election_ref=vote).delete()
            vote.delete()
            messages.success(request, 'Vote deleted')
        if request.POST['vote-btn'] == "Create ballot":
            form = CreateVoteFormBallot(request.POST)
            if form.is_valid():
                ballot = form.save(commit=False)
                ballot.election_ref = vote
                form.save()
                messages.success(request, 'Ballot created')
            else:
                messages.error(request, "Error while filling the form:")
                messages.error(request, form.errors)
            return HttpResponseRedirect(reverse('voteedit', args=(ref,)))

    return HttpResponseRedirect("/")


@login_required
def voteeditballot(request, ref):
    """Handler for editing a ballot."""
    user = get_current_user(request)
    ballot = get_object_or_404(VoteBallot, ref=ref)
    vote = VoteElection.objects.get(ref=ballot.election_ref.pk)

    if not tests_vote(request, user, vote):
        return HttpResponseRedirect("/")

    if request.method == 'POST':
        if request.POST['ballot-btn'] == "Edit":
            form = EditVoteFormBallot(request.POST, instance=ballot)
            if form.is_valid():
                form.save()
            else:
                messages.error(request, "Error while filling the form:")
                messages.error(request, form.errors)
            return HttpResponseRedirect(reverse('voteedit', args=(vote.pk,)))
        elif request.POST['ballot-btn'] == "Delete":
            VoteOption.objects.filter(ballot_ref=ballot).delete()
            ballot.delete()
            messages.success(request, 'Ballot deleted')
            return HttpResponseRedirect(reverse('voteedit', args=(vote.pk,)))

    return HttpResponseRedirect("/")


@login_required
def voteedit(request, ref):
    """Handler for the form to edit a vote."""
    user = get_current_user(request)
    vote = get_object_or_404(VoteElection, ref=ref)

    if not tests_vote(request, user, vote):
        return HttpResponseRedirect("/")

    template = loader.get_template('vote-edit.html')
    editvoteform = EditVoteForm(instance=vote)
    ballots = VoteBallot.objects.filter(election_ref=ref)
    createvoteformballot = CreateVoteFormBallot()
    editvoteformballots = []
    for ballot in ballots:
        existingvoteoptions = []
        existingvoteorders = set()
        voteoptions = VoteOption.objects.filter(ballot_ref=ballot.ref)
        for voteoption in voteoptions:
            voteoptionform = VoteOptionForm(instance=voteoption)
            existingvoteoptions.append(voteoptionform)
            existingvoteorders.add(voteoption.sort)
        if len(existingvoteorders) == 0:
            sort = 1
        else:
            sort = max(existingvoteorders) + 1
        newvoteoptionform = VoteOptionForm(initial={'sort': sort, 'ballot_ref': ballot.ref})
        editvoteformballot = {
            'ballot_ref': ballot.ref,
            'form': EditVoteFormBallot(instance=ballot),
            'existingvoteoptions': existingvoteoptions,
            'voteoptionform': newvoteoptionform,
        }
        editvoteformballots.append(editvoteformballot)
    context = {
        'user': user,
        'editvoteform': editvoteform,
        'editvoteformballots': editvoteformballots,
        'createvoteformballot': createvoteformballot,
        'vote_ref': ref,
    }
    return HttpResponse(template.render(context, request))


@login_required
def voteeditoption(request, ref):
    """Handler for editing options of a vote."""
    user = get_current_user(request)
    ballot = get_object_or_404(VoteBallot, ref=ref)
    vote = VoteElection.objects.get(ref=ballot.election_ref.pk)

    if not tests_vote(request, user, vote):
        return HttpResponseRedirect("/")

    if request.method == 'POST':
        voteoption = VoteOption.objects.filter(Q(sort=request.POST['sort']) & Q(ballot_ref=ballot))
        if request.POST['obtn'] == "Add":
            if voteoption:
                messages.error(request, "Error: selection character already used")
            else:
                form = VoteOptionForm(request.POST)
                if form.is_valid():
                    form.instance.ballot_ref = ballot
                    form.save()
                else:
                    messages.error(request, "Error while filling the form:")
                    messages.error(request, form.errors)
        elif request.POST['obtn'] == "Edit":
            form = VoteOptionForm(instance=voteoption[0], data=request.POST)
            if form.is_valid():
                form.save()
            else:
                messages.error(request, "Error while filling the form:")
                messages.error(request, form.errors)
        elif request.POST['obtn'] == "Delete":
            form = VoteOptionForm(request.POST)
            voteoption.delete()
    return HttpResponseRedirect(reverse('voteedit', args=(vote.pk,)))


@login_required
def voteresult(request, ref):
    """Handler for viewing a specific vote result."""
    user = get_current_user(request)
    vote = get_object_or_404(VoteElection, ref=ref)

    if vote.owner != user:
        messages.error(request, 'You can only view results for your own votes.')
        return HttpResponseRedirect("/")

    if not vote.is_over:
        messages.error(request, 'Vote must be finished to view results.')
        return HttpResponseRedirect("/")

    membervotes = sorted(VoteVote.objects.filter(election_ref=ref),
                         key=lambda x: x.voter_ref.name if x.voter_ref else '')
    blank_votes_count = sum(1 for mv in membervotes if not mv.votestr.strip())
    options = VoteOption.objects.filter(election_ref=ref)

    if len(options) < 2:
        messages.error(request, 'Votes must have at least 2 candidates to run.')
        return HttpResponseRedirect("/")

    if vote.system == 0:
        votesystem = CondorcetVS(vote, membervotes)
    elif vote.system == 1:
        votesystem = CondorcetVS(vote, membervotes, ignoremissing=False)
    elif vote.system == 2:
        votesystem = OpenSTVVS(vote, membervotes)

    votesystem.run()

    template = loader.get_template('vote-result.html')
    context = {
        'user': user,
        'vote': vote,
        'options': options,
        'membervotes': membervotes,
        'votesystem': votesystem,
        'blank_votes_count': blank_votes_count
    }
    return HttpResponse(template.render(context, request))


def privatesubs(request):
    """Return the list of -private subscriber addressess"""
    user = get_current_user(request)
    if request.META.get('REMOTE_ADDR') not in settings.LIST_HOSTS:
        messages.error(request, 'This page is not reachable from your IP address.')
        return HttpResponseRedirect("/")

    emails = sorted([x.email for x in Members.objects.filter(Q(sub_private=True) & Q(iscontrib=True))])
    emaillist = '\n'.join(emails)
    return HttpResponse(emaillist.lower(), content_type='text/plain')


class MemberEditView(LoginRequiredMixin, UpdateView):
    model = Members
    fields = ['sub_private']
