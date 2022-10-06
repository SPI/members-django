import datetime

from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.template import loader
from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.views.generic.edit import UpdateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from django.utils import timezone

from membersapp.app.stats import get_stats
from membersapp.app.applications import *
from .models import Members, Applications, VoteElection, VoteOption
from .forms import *


def handler404(request, exception):
    user = get_current_user(request)
    template = loader.get_template('404.html')
    context = {
        'user': user
    }
    return HttpResponseNotFound(template.render(context, request))


def index(request):
    if not request.user.is_authenticated:
        template = loader.get_template('index.html')
        context = {}
        return HttpResponse(template.render(context, request))
    else:
        template = loader.get_template('status.html')
        user = get_current_user(request)
        form = MemberForm(instance=user)
        context = {
            'active_votes': VoteElection.objects.filter(Q(period_start__lte=timezone.now()) & Q(period_stop__gte=timezone.now())),
            'user_votes': VoteElection.objects.filter(owner=user),
            'applications': get_applications_by_user(user),
            'applicants': get_applications(user),
            'user': user,
            'form': form
        }
        return HttpResponse(template.render(context, request))


@login_required
def application(request, appid):
    template = loader.get_template('application.html')
    application = get_object_or_404(Applications, appid=appid)
    user = get_current_user(request)
    if application.member != user:
        return render(request, 'manager-only.html')
    member = Members.object.get(memid=application.member_id)
    memberform = MemberForm(instance=member)
    applicationform = ApplicationForm(instance=application)
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
    if request.method == 'POST':
        user = get_current_user(request)
        user.lastactive = datetime.date.today()
        user.save()
    return HttpResponseRedirect("/")


def showstats(request):
    """Handler for showing membership statistics"""
    stats = get_stats()
    user = get_current_user(request)
    return render(request, 'stats.html', {'stats': stats, 'user': user})


@login_required
def showapplications(request, listtype):
    user = get_current_user(request)
    if not user.ismanager:
        return render(request, 'manager-only.html')
    template = loader.get_template('applications.html')
    if listtype == 'ncm':
        applications = Applications.objects.filter(Q(member__iscontrib=False) & (Q(contribapp=False) | Q(contribapp__isnull=True)))
    elif listtype == 'ca':
        applications = Applications.objects.filter(Q(approve__isnull=True) & Q(contribapp=True))
    elif listtype == 'cm':
        applications = Applications.objects.filter(Q(member__iscontrib=True) & Q(contribapp=True))
    elif listtype == 'mgr':
        applications = Applications.objects.filter(Q(member__ismanager=True) & Q(contribapp=True))
    else:
        applications = Applications.objects.all()
    sorted_applications = applications.order_by('appid')
    context = {
        'applicants': sorted_applications,
        'listtype': listtype,
        'user': user
    }
    return HttpResponse(template.render(context, request))


@login_required
def showvotes(request):
    user = get_current_user(request)
    if not user.ismanager:
        return render(request, 'manager-only.html')
    template = loader.get_template('votes.html')
    votes = VoteElection.objects.order_by('-period_start')
    context = {
        'user': user,
        'votes': votes,
    }
    return HttpResponse(template.render(context, request))


@login_required
def showvote(request, ref):
    user = get_current_user(request)
    if not user.ismanager:
        return render(request, 'manager-only.html')
    template = loader.get_template('vote.html')
    vote = VoteElection.object.get(pk=ref)
    options = VoteOption.objects.filter(election_ref=ref)
    context = {
        'user': user,
        'vote': vote,
        'options': options
    }
    return HttpResponse(template.render(context, request))


@login_required
def showmember(request, memid):
    user = get_current_user(request)
    if not user.ismanager:
        return render(request, 'manager-only.html')
    template = loader.get_template('member.html')
    member = Members.object.get(pk=memid)
    context = {
        'user': user,
        'member': member,
        'applications': get_applications_by_user(member)
    }
    return HttpResponse(template.render(context, request))


@login_required
def memberedit(request):
    if request.method == 'POST':
        user = get_current_user(request)
        form = MemberForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
    return HttpResponseRedirect(reverse('index'))


@login_required
def applicationedit(request, appid):
    # todo: check edit privileges
    if request.method == 'POST':
        application = Applications.objects.get(pk=appid)
        application_pre_value = application.approve
        memberform = MemberForm(request.POST, instance=application.member)
        applicationform = ApplicationForm(request.POST, instance=application)
        # caution: is_valid() modifies objects
        if memberform.is_valid() and applicationform.is_valid():
            process_contrib_application(request, applicationform, application, application_pre_value)
            memberform.save()
            applicationform.save()
    return HttpResponseRedirect(reverse('application', args=[appid]))


@login_required
def contribapplication(request):
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
    user = get_current_user(request)
    if not user.createvote:
        messages.error(request, 'You are not allowed to create new votes')
        return HttpResponseRedirect("/")

    if request.method == 'POST':
        user = get_current_user(request)
        form = CreateVoteForm(request.POST)
        if form.is_valid():
            form.instance.owner = user
            new_vote = form.save()
            return HttpResponseRedirect(reverse('voteedit', args=(new_vote.pk,)))
        else:
            messages.error(request, "Error while filling the form:")
            messages.error(request, form.errors)
            # Fall back to showing regular create page

    template = loader.get_template('vote-create.html')
    createvoteform = CreateVoteForm()
    context = {
        'user': user,
        'createvoteform': createvoteform
    }
    return HttpResponse(template.render(context, request))


@login_required
def voteedit(request, ref):
    user = get_current_user(request)
    vote = get_object_or_404(VoteElection, ref=ref)
    if not user.createvote:
        messages.error(request, 'You are not allowed to create new votes')
        return HttpResponseRedirect("/")

    if vote.owner != user:
        messages.error(request, 'You can only edit your own votes.')
        return HttpResponseRedirect("/")

    if vote.is_active or vote.is_over:
        messages.error(request, 'Vote must not have run to be edited.')
        return HttpResponseRedirect("/")
    if request.method == 'POST':
        voteoption = VoteOption.objects.filter(Q(option_character=request.POST['option_character']) & Q(election_ref=vote))
        if request.POST['obtn'] == "Add":
            if voteoption:
                messages.error(request, "Error: selection character already used")
            else:
                form = VoteOptionForm(request.POST)
                if form.is_valid():
                    form.instance.election_ref = vote
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
#        elif request.POST['obtn'] == "Add":
#            pass

    template = loader.get_template('vote-edit.html')
    editvoteform = EditVoteForm(instance=vote)
    existingvoteoptions = []
    voteoptions = VoteOption.objects.filter(election_ref=ref)
    existingvoteorders = set()
    for voteoption in voteoptions:
        voteoptionform = VoteOptionForm(instance=voteoption)
        existingvoteoptions.append(voteoptionform)
        existingvoteorders.add(voteoption.sort)
    if len(existingvoteorders) == 0:
        sort = 1
    else:
        sort = max(existingvoteorders) + 1
    newvoteoptionform = VoteOptionForm(initial={'sort': sort, 'election_ref': ref})
    # data={'election_ref': ref},
    context = {
        'user': user,
        'editvoteform': editvoteform,
        'existingvoteoptions': existingvoteoptions,
        'voteoptionform': newvoteoptionform
    }
    return HttpResponse(template.render(context, request))


class MemberEditView(LoginRequiredMixin, UpdateView):
    model = Members
    fields = ['sub_private']
